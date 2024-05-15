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

# Set RX gain to boosted gain
print("Set RX gain to power saving gain")
LoRa.setRxGain(LoRa.RX_GAIN_BOOSTED)

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

print("\n-- LoRa Receiver Listen --\n")

# Receive message continuously
while True :

    # Listen for a LoRa packet in 10 ms and sleep in 10 ms
    rxPeriod = 10
    sleepPeriod = 10
    LoRa.listen(rxPeriod, sleepPeriod)

    # Check for incoming LoRa packet
    if LoRa.available() :

        # Put received packet to message and counter variable
        message = ""
        while LoRa.available() > 1 :
            message += chr(LoRa.read())
        counter = LoRa.read()

        # Print received message and counter in serial
        print(f"{message}  {counter}")

        # Print packet/signal status including RSSI, SNR, and signalRSSI
        print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB".format(LoRa.packetRssi(), LoRa.snr()))

        # Show received status in case CRC or header error occur
        status = LoRa.status()
        if status == LoRa.STATUS_CRC_ERR : print("CRC error")
        elif status == LoRa.STATUS_HEADER_ERR : print("Packet header error")

try :
    pass
except :
    LoRa.end()
