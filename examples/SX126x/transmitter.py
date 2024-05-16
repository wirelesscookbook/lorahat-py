import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from LoRaRF import SX126x
import toml
import time

# Load configuration from TOML file
t = toml.load('config.toml')

busId = t.get('busId')
csId = t.get('csId')
resetPin = t.get('resetPin')
busyPin = t.get('busyPin')
irqPin = t.get('irqPin')
txenPin = t.get('txenPin')
rxenPin = t.get('rxenPin')
LoRa = SX126x()
print("Begin LoRa radio")
# Begin LoRa radio with configured Raspberry Pi GPIO pins
if not LoRa.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin) :
    raise Exception("Something wrong, can't begin LoRa radio")

LoRa.setDio2RfSwitch()
# Set frequency
frequency_hz = int(t.get('frequency'))
frequency_mhz = round(frequency_hz / 1_000_000)
print(f"Set frequency to {frequency_mhz} Mhz")
LoRa.setFrequency(frequency_hz)

# This function will set PA config with optimal setting for requested TX power
txPower = int(t.get('txPower'))
print(f"Set TX power to +{txPower} dBm")
LoRa.setTxPower(txPower, LoRa.TX_POWER_SX1262)                       # TX power +17 dBm using PA boost pin

sf = int(t.get('spreadFactor'))
bw = int(t.get('bandwidth'))
cr = int(t.get('codingRate'))
print(f"Set modulation parameters:\n\tSpreading factor = {sf}\n\tBandwidth = {round(bw / 1000)} kHz\n\tCoding rate = 4/{cr}")
LoRa.setLoRaModulation(sf, bw, cr)

headerType = LoRa.HEADER_EXPLICIT                               # Explicit header mode
preambleLength = int(t.get('preambleLength'))
payloadLength = int(t.get('payloadLength'))
crcType = bool(t.get('crcType'))
print(f"Set packet parameters:\n\tExplicit header type\n\tPreamble length = {preambleLength}\n\tPayload Length = {payloadLength}\n\tCRC {crcType}")
LoRa.setLoRaPacket(headerType, preambleLength, payloadLength, crcType)

# Set syncronize word for public network (0x3444)
print("Set syncronize word to 0x3444")
LoRa.setSyncWord(0x3444)

print("\n-- LoRa Transmitter --\n")

# Message to transmit
message = str(t.get('message', 'HeLoRa World!\0'))
counter = 0

# Transmit message continuously
while True :

    if message == "temperature":
        try:
            # Read the CPU temperature from the system file
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp_file:
                temp = temp_file.read().strip()
                cpu_temp = float(temp) / 1000.0
                temp_msg = f"CPU temperature: {cpu_temp:.2f}°C"
        except FileNotFoundError:
            temp_msg = "Unable to read CPU temperature"
    else:
        temp_msg = message

    messageList = [ord(char) for char in temp_msg]

    # Transmit message and counter
    # write() method must be placed between beginPacket() and endPacket()
    LoRa.beginPacket()
    LoRa.write(messageList, len(messageList))
    LoRa.write([counter], 1)
    LoRa.endPacket()

    # Print message and counter
    print(f"{temp_msg}  {counter}")

    # Wait until modulation process for transmitting packet finish
    LoRa.wait()

    # Print transmit time and data rate
    print("Transmit time: {0:0.2f} ms | Data rate: {1:0.2f} byte/s".format(LoRa.transmitTime(), LoRa.dataRate()))

    # Don't load RF module with continous transmit
    time.sleep(5)
    counter = (counter + 1) % 256

try :
    pass
except :
    LoRa.end()
