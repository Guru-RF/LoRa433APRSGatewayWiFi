import time
import rtc
import board
import busio
import adafruit_rfm9x
from digitalio import DigitalInOut, Direction, Pull
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import PWMOut
import adafruit_rgbled
import adafruit_requests as requests
from adafruit_datetime import datetime
import binascii
import config


# our version
VERSION = "RF.Guru_LoRaAPRSPagerGateway 0.1" 

#def purple(data):
#  stamp = datetime.now()
#  return "\x1b[38;5;104m[" + str(stamp) + "] " + data + "\x1b[0m"
#
#def yellow(data):
#  return "\x1b[38;5;220m" + data + "\x1b[0m"
#
#def red(data):
#  return "\x1b[1;5;31m -- " + data + "\x1b[0m"
#
## our version
#print(red(config.hostname + " -=- " + VERSION))
#
#try:
#    from secrets import secrets
#except ImportError:
#    print("WiFi secrets are kept in secrets.py, please add them there!")
#    raise
#
#esp32_cs = DigitalInOut(board.GP17)
#esp32_ready = DigitalInOut(board.GP14)
#esp32_reset = DigitalInOut(board.GP13)
#
## Clock MOSI(TX) MISO(RX)
#spi = busio.SPI(board.GP18, board.GP19, board.GP16)
#esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
#
##esp.set_hostname(config.hostname)
#
#if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
#      print("ESP32 found and in idle mode")
#print("Firmware vers.", esp.firmware_version)
#print("MAC addr:", [hex(i) for i in esp.MAC_address])
#
#RED_LED = PWMOut.PWMOut(esp, 25)
#GREEN_LED = PWMOut.PWMOut(esp, 26)
#BLUE_LED = PWMOut.PWMOut(esp, 27)
#status_light = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)
#wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)
#
### Connect to WiFi
#print("Connecting to WiFi..")
#wifi.connect()
#  
#print("Connected to:\n", str(esp.ssid, "utf-8"), "\nRSSI:", esp.rssi)
#
## Initialize a requests object with a socket and esp32spi interface
#socket.set_interface(esp)
#requests.set_socket(socket, esp)
#
#print("Sync time with NTP!")
#now = None
#while now is None:
#    try:
#        now = time.localtime(esp.get_time()[0])
#    except OSError:
#        pass
#rtc.RTC().datetime = now
#print("Time is in sync!")

# Lora Stuff
RADIO_FREQ_MHZ = 439.957
CS = DigitalInOut(board.GP21)
RESET = DigitalInOut(board.GP20)
spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP8)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False,crc=True)
rfm9x.tx_power = 5

message = "PagerTest"

while True:
    rfm9x.send(
        bytes("{}".format("<"), "UTF-8") + binascii.unhexlify("AA") + binascii.unhexlify("99") +
        bytes("{}".format(message), "UTF-8")
    )
    print("send")
    time.sleep(10)