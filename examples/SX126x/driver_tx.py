import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from LoRaRF import SX126x
import RPi.GPIO
import time

busId = 0; csId = 0 
resetPin = 18; busyPin = 20; irqPin = 16; txenPin = 6; rxenPin = -1 

LoRa = SX126x()
GPIO = RPi.GPIO

# Xtal setting
# xtalCap = [0x12, 0x12]

# RF frequency setting
rfFrequency = 868000000

# PA and TX power setting
paDutyCycle = 0x02
hpMax = 0x03
deviceSel = 0x00
power = 0x16

# Define modulation parameters setting
sf = 7
bw = LoRa.BW_125000
cr = LoRa.CR_4_5
ldro = LoRa.LDRO_OFF

# Define packet parameters setting
preambleLength = 0x0C
headerType = LoRa.HEADER_EXPLICIT
payloadLength = 0x40
crcType = LoRa.CRC_ON
invertIq = LoRa.IQ_STANDARD

# SyncWord setting
sw = [0x34, 0x44]

# Transmit flag
transmitted = False
intSet = False

def checkTransmitDone(channel) :
    global transmitted
    transmitted = True

def settingFunction() :

    print("-- SETTING FUNCTION --")

    # SPI and GPIO Pins setting
    print("Setting pins")
    LoRa.setSpi(busId, csId)
    LoRa.setPins(resetPin, busyPin, irqPin, txenPin, rxenPin)

    # Reset RF module by setting resetPin to LOW and begin SPI communication
    print("Resetting RF module")
    LoRa.reset()
    LoRa.setStandby(LoRa.STANDBY_RC)
    if not LoRa.busyCheck() :
        print("Going to standby mode")
    else :
        print("Something wrong, can't set to standby mode")

    # Optionally configure TCXO or XTAL used in RF module
    # print("Set RF module to use XTAL as clock reference")
    # LoRa.writeRegister(LoRa.REG_XTA_TRIM, xtalCap, 2)

    # Optionally configure DIO2 as RF switch control
    # print("Set RF switch is controlled by DIO2")
    # LoRa.setDio2AsRfSwitchCtrl(LoRa.DIO2_AS_RF_SWITCH)

    # Set packet type to LoRa
    print("Set packet type to LoRa")
    LoRa.setPacketType(LoRa.LORA_MODEM)

    # Set frequency to selected frequency (rfFrequency = rfFreq * 32000000 / 2 ^ 25)
    print(f"Set frequency to {rfFrequency/1000000} Mhz")
    rfFreq = int(rfFrequency * 33554432 / 32000000)
    LoRa.setRfFrequency(rfFreq)

    # Set tx power to selected TX power
    print(f"Set TX power to {power} dBm")
    LoRa.setPaConfig(paDutyCycle, hpMax, deviceSel, 0x01)
    LoRa.setTxParams(power, LoRa.PA_RAMP_200U)

    # Configure modulation parameter with predefined spreading factor, bandwidth, coding rate, and low data rate optimize setting
    print("Set modulation with predefined parameters")
    LoRa.setModulationParamsLoRa(sf, bw, cr, ldro)

    # Configure packet parameter with predefined preamble length, header mode type, payload length, crc type, and invert iq option
    print("Set packet with predefined parameters")
    LoRa.setPacketParamsLoRa(preambleLength, headerType, payloadLength, crcType, invertIq)

    # Set predefined syncronize word
    print("Set syncWord to 0x{0:02X}{1:02X}".format(sw[0], sw[1]))
    LoRa.writeRegister(LoRa.REG_LORA_SYNC_WORD_MSB, sw, 2)

def transmitFunction(message: list, timeout: int) -> int :

    print("\n-- TRANSMIT FUNCTION --")

    # Set buffer base address
    print("Mark a pointer in buffer for transmit message")
    LoRa.setBufferBaseAddress(0x00, 0x80)

    # Write the message to buffer
    length = len(message)
    messageString = ""
    for i in range(len(message)) : messageString += chr(message[i])
    print(f"Write message \"{messageString}\" in buffer")
    print(f"Message in bytes : {message}")
    LoRa.writeBuffer(0x00, message, length)

    # Set payload length same as message length
    print(f"Set payload length same as message length ({length})")
    LoRa.setPacketParamsLoRa(preambleLength, headerType, length, crcType, invertIq)

    # Activate interrupt when transmit done on DIO1
    print("Set TX done and timeout IRQ on DIO1")
    mask = LoRa.IRQ_TX_DONE | LoRa.IRQ_TIMEOUT
    LoRa.setDioIrqParams(mask, mask, LoRa.IRQ_NONE, LoRa.IRQ_NONE)

    # Attach irqPin to DIO1
    print(f"Attach interrupt on IRQ pin")
    global intSet
    if not intSet :
        GPIO.setup(irqPin, GPIO.IN)
        GPIO.add_event_detect(irqPin, GPIO.RISING, callback=checkTransmitDone, bouncetime=100)
        intSet = True
    # Set rxen and txen pin state for transmitting packet
    if txenPin != -1 and rxenPin != -1 :
        GPIO.output(txenPin, GPIO.HIGH)
        GPIO.output(rxenPin, GPIO.LOW)

    # Calculate timeout (timeout duration = timeout * 15.625 us)
    tOut = timeout * 64
    # Set RF module to TX mode to transmit message
    print("Transmitting LoRa packet")
    LoRa.setTx(tOut)
    tStart = time.time()
    tTrans = 0

    # Wait for TX done interrupt and calcualte transmit time
    print("Wait for TX done interrupt")
    global transmitted
    while not transmitted : pass
    tTrans = time.time() - tStart
    # Clear transmit interrupt flag
    transmitted = False
    print("Packet transmitted!")

    # Display transmit time
    print(f"Transmit time = {tTrans*1000} ms")

    # Clear the interrupt status
    irqStat = LoRa.getIrqStatus()
    print("Clear IRQ status")
    LoRa.clearIrqStatus(irqStat)
    if txenPin != -1 :
        GPIO.output(txenPin, GPIO.LOW)

    # Return interrupt status
    return irqStat

# Settings for LoRa communication
settingFunction()
LoRa.setDio2RfSwitch()

while True :

    # Message to transmit
    messageString = "HeLoRa World!\0"
    message = list(messageString)
    for i in range(len(message)) : message[i] = ord(message[i])

    # Transmit message
    timeout = 1000
    status = transmitFunction(message, timeout)
    # Display status if error happen
    if status & LoRa.IRQ_TIMEOUT :
        print("Transmit timeout")

    # Don't load RF module with continous transmit
    time.sleep(10)

try :
    pass
except :
    LoRa.end()
