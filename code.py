import time
import rtc
import board
import busio
import adafruit_rfm9x
from adafruit_datetime import datetime
from digitalio import DigitalInOut, Direction, Pull
import binascii
import config

rxtx = DigitalInOut(board.GP0)
rxtx.direction = Direction.OUTPUT
rxtx.value = False

pa = DigitalInOut(board.GP2)
pa.direction = Direction.OUTPUT
pa.value = False

biast = DigitalInOut(board.GP1)
biast.direction = Direction.OUTPUT
biast.value = False

# our version
VERSION = "RF.Guru_LoRaAPRSGateway 0.1" 

def purple(data):
  stamp = datetime.now()
  return "\x1b[38;5;104m[" + str(stamp) + "] " + data + "\x1b[0m"

def yellow(data):
  return "\x1b[38;5;220m" + data + "\x1b[0m"

def red(data):
  return "\x1b[1;5;31m -- " + data + "\x1b[0m"

# max 13dBm !!! for saw filter

# our version
print(red(config.hostname + " -=- " + VERSION))
#
# Lora Stuff
RADIO_FREQ_MHZ = 439.957
CS = DigitalInOut(board.GP21)
RESET = DigitalInOut(board.GP20)
spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP8)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False,crc=True)
rfm9x.tx_power = 23

message = "PagerTestPagerTestPagerTestPagerTestPagerTestPagerTestPagerTestPagerTestPagerTest"

while True:
    biast.value = False
#    rxtx.value = True
#    pa.value = True
#    rfm9x.send(
#        bytes("{}".format("<"), "UTF-8") + binascii.unhexlify("AA") + binascii.unhexlify("99") +
#        bytes("{}".format(message), "UTF-8")
#    )
#    print("send")
#    pa.value = False
#    rxtx.value = False
    time.sleep(1)