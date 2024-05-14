import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from LoRaRF import SX126x
import time
import struct
import random

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

# Set TX power to +22 dBm
LoRa.setTxPower(22, LoRa.TX_POWER_SX1262)
print("Set TX power to +22 dBm")

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

print("\n-- LoRa Node --\n")

# IDs and message format to transmit
gatewayId = 0xCC
nodeId = 0x77
messageId = 0
format = 'BBHIi'
length = struct.calcsize(format)

# Transmit message continuously
while True :

    # Structured message
    structure = [
        gatewayId,
        nodeId,
        messageId,
        round(time.time()),
        random.randrange(-1073741824, 1073741824)
    ]
    message = struct.pack(format, *structure)
    messageId = (messageId + 1) % 65536

    # Transmit structured message
    # Set transmit timeout to 250 ms
    LoRa.beginPacket()
    LoRa.put(message)
    LoRa.endPacket(250)
    LoRa.wait()

    # Print structured message
    print("Gateway ID    : 0x{0:02X}".format(gatewayId))
    print("Node ID       : 0x{0:02X}".format(nodeId))
    print(f"Message ID    : {structure[2]}")
    print(f"Time          : {structure[3]}")
    print(f"Data          : {structure[4]}")

    # Print transmit time
    print("Transmit time : {0:0.2f} ms\n".format(LoRa.transmitTime()))

    # Print status timeout when transmit process terminated due to timeout
    if LoRa.status() == LoRa.STATUS_TX_TIMEOUT : print("Transmit timeout")

    # Put RF module to sleep in a few seconds
    LoRa.sleep()
    time.sleep(5)
    LoRa.wake()

try :
    pass
except :
    LoRa.end()