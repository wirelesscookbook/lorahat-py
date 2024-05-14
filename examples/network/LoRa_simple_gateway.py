import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from LoRaRF import SX126x
import time
import struct

# Begin LoRa radio and set NSS, reset, busy, IRQ, txen, and rxen pin with connected Raspberry Pi gpio pins
busId = 0; csId = 0 
resetPin = 18; busyPin = 20; irqPin = 16; txenPin = 6; rxenPin = -1 
LoRa = SX126x()
print("Begin LoRa radio")
if not LoRa.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin) :
    raise Exception("Something wrong, can't begin LoRa radio")

LoRa.setDio2RfSwitch()
# Set frequency to 868 Mhz
LoRa.setFrequency(868000000)
print("Set frequency to 868 Mhz")

# Set RX gain to boosted gain
LoRa.setRxGain(LoRa.RX_GAIN_BOOSTED)
print("Set RX gain to power saving gain")

# Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
sf = 7
bw = 125000
cr = 5
LoRa.setLoRaModulation(sf, bw, cr)
print("Set modulation parameters:\n\tSpreading factor = 7\n\tBandwidth = 125 kHz\n\tCoding rate = 4/5")

# Configure packet parameter including header type, preamble length, payload length, and CRC type
headerType = LoRa.HEADER_IMPLICIT
preambleLength = 12
payloadLength = 12
crcType = True
LoRa.setLoRaPacket(headerType, preambleLength, payloadLength, crcType)
print(f"Set packet parameters:\n\tImplicit header type\n\tPreamble length = 12\n\tPayload Length = 12\n\tCRC on")

# Set syncronize word for public network (0x3444)
LoRa.setSyncWord(0x3444)
print("Set syncronize word to 0x3444")

print("\n-- LoRa Gateway --\n")

# IDs and message format from received message
gatewayId = 0xCC
format = 'BBHIi'
length = struct.calcsize(format)

# Transmit message continuously
while True :

    # Set RF module to listen mode with 20 ms RX mode and 10 ms sleep
    # Some LoRa packet will not be received if sleep period too long or preamble length too short
    rxPeriod = 20
    sleepPeriod = 10
    LoRa.listen(rxPeriod, sleepPeriod)
    # Wait for incoming LoRa packet
    LoRa.wait()

    # Get received structured message
    message = LoRa.get(length)
    structure = struct.unpack(format, message)

    # Check gateway ID from received message
    if structure[0] == gatewayId :

        # Print structured message
        print("Gateway ID    : 0x{0:02X}".format(gatewayId))
        print("Node ID       : 0x{0:02X}".format(structure[1]))
        print(f"Message ID    : {structure[2]}")
        print(f"Time          : {structure[3]}")
        print(f"Data          : {structure[4]}")

        # Print packet status
        print("Packet status : RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB\n".format(LoRa.packetRssi(), LoRa.snr()))

    else :

        # Print error message
        print("Received message with wrong gateway ID (0x{0:02X})".format(structure[0]))

    # Show received status in case CRC or header error occur
    status = LoRa.status()
    if status == LoRa.STATUS_CRC_ERR : print("CRC error")
    if status == LoRa.STATUS_HEADER_ERR : print("Packet header error")

try :
    pass
except :
    LoRa.end()