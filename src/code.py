import asyncio
import binascii
import random
import time

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import adafruit_rfm9x
import adafruit_rgbled
import board
import busio
import config
import microcontroller
import rtc
import supervisor
import usyslog
from adafruit_esp32spi import PWMOut, adafruit_esp32spi, adafruit_esp32spi_wifimanager
from APRS import APRS
from digitalio import DigitalInOut, Direction, Pull
from microcontroller import watchdog as w
from watchdog import WatchDogMode

# stop autoreloading
supervisor.runtime.autoreload = False

# gateway or igate detect via pin state
versionPin = DigitalInOut(board.GP9)
versionPin.direction = Direction.INPUT
versionPin.pull = Pull.UP

# 1/2W Pa
pa = DigitalInOut(board.GP2)
pa.direction = Direction.OUTPUT
pa.value = False

# 5v biasT
biast = DigitalInOut(board.GP1)
biast.direction = Direction.OUTPUT
biast.value = False

igate = False
if versionPin.value is True:
    igate = True
    loraTimeout = 900
    biast = DigitalInOut(board.GP0)
    biast.direction = Direction.OUTPUT
    biast.value = False
else:
    loraTimeout = 30
    transmit = DigitalInOut(board.GP0)
    transmit.direction = Direction.OUTPUT
    transmit.value = False

if config.biast is True:
    biast.value = True

# our version
if igate is True:
    VERSION = "RF.Guru_APRSiGate 0.1"
else:
    VERSION = "RF.Guru_APRSGateway 0.1"


def _format_datetime(datetime):
    return "{:02}/{:02}/{} {:02}:{:02}:{:02}".format(
        datetime.tm_mon,
        datetime.tm_mday,
        datetime.tm_year,
        datetime.tm_hour,
        datetime.tm_min,
        datetime.tm_sec,
    )


def purple(data):
    s.info(data)
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\x1b[38;5;104m[" + str(stamp) + "] " + data + "\x1b[0m"


def green(data):
    s.info(data)
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\r\x1b[38;5;112m[" + str(stamp) + "] " + data + "\x1b[0m"


def blue(data):
    global s
    s.info(data)
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\x1b[38;5;14m[" + str(stamp) + "] " + data + "\x1b[0m"


def yellow(data):
    return "\x1b[38;5;220m" + data + "\x1b[0m"


def red(data):
    s.info(data)
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\x1b[1;5;31m[" + str(stamp) + "] " + data + "\x1b[0m"


def bgred(data):
    s.info(data)
    stamp = "{}".format(_format_datetime(time.localtime()))
    return "\x1b[41m[" + str(stamp) + "] " + data + "\x1b[0m"


# wait for console
time.sleep(2)

print("\x1b[1;5;31m -- " + f"{config.call} -=- {VERSION}" + "\x1b[0m\n")

try:
    from secrets import secrets
except ImportError:
    print(red("WiFi secrets are kept in secrets.py, please add them there!"))
    raise

esp32_cs = DigitalInOut(board.GP17)
esp32_ready = DigitalInOut(board.GP14)
esp32_reset = DigitalInOut(board.GP13)

# Clock MOSI(TX) MISO(RX)
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print(yellow("ESP32 found and in idle mode"))
print(yellow("Firmware version: " + (esp.firmware_version).decode("utf-8")))
print(yellow("MAC addr: " + str([hex(i) for i in esp.MAC_address])))

RED_LED = PWMOut.PWMOut(esp, 25)
GREEN_LED = PWMOut.PWMOut(esp, 26)
BLUE_LED = PWMOut.PWMOut(esp, 27)
status_light = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

## Connect to WiFi
print(yellow("Connecting to WiFi..."))
wifi.connect()
print(yellow("Connected!"))

print(yellow("Connected to: [" + str(esp.ssid, "utf-8") + "]\tRSSI:" + str(esp.rssi)))
print()

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

# aprs auth packet
rawauthpacket = f"user {config.call} pass {config.passcode} vers {VERSION} filter t/m/{config.call}/{config.msgDistance}\n"

now = None
while now is None:
    try:
        now = time.localtime(esp.get_time()[0])
    except OSError:
        pass
rtc.RTC().datetime = now

# usyslog
s = usyslog.UDPClient(
    socket, esp, hostname=config.call, host=config.syslogHost, port=config.syslogPort
)
s.info("test")

while True:
    time.sleep(30)
    s.info("test")


# aprs
aprs = APRS()

txmsgs = []

# configure watchdog
w.timeout = 5
w.mode = WatchDogMode.RESET
w.feed()


async def iGateAnnounce():
    # Periodically sends status packets and position packets to the APRS-IS server over TCP.
    # Handles reconnecting if the send fails.
    global w, s, rawauthpacket
    try:
        socket.set_interface(esp)
        requests.set_socket(socket, esp)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        socketaddr = socket.getaddrinfo(config.aprs_host, config.aprs_port)[0][4]
        s.connect(socketaddr)
        s.send(bytes(rawauthpacket, "utf-8"))
        w.feed()
    except Exception as error:
        print(bgred(f"[{config.call}] init: An exception occurred: {error}"))
        print(
            purple(
                f"[{config.call}] init: Connect to ARPS {config.aprs_host} {config.aprs_port} Failed ! Lost Packet ! Restarting System !"
            )
        )
        microcontroller.reset()
    while True:
        await asyncio.sleep(0)
        w.feed()
        temp = microcontroller.cpus[0].temperature
        freq = microcontroller.cpus[1].frequency / 1000000
        rawpacket = (
            f"{config.call}>APRFGI,TCPIP*:>Running on RP2040 t:{temp}C f:{freq}Mhz\n"
        )
        try:
            s.send(bytes(rawpacket, "utf-8"))
        except Exception as error:
            print(bgred(f"[{config.call}] iGateStatus: An exception occurred: {error}"))
            print(
                purple(
                    f"[{config.call}] iGateStatus: Reconnecting to ARPS {config.aprs_host} {config.aprs_port}"
                )
            )
            s.close()
            socket.set_interface(esp)
            requests.set_socket(socket, esp)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            try:
                socketaddr = socket.getaddrinfo(config.aprs_host, config.aprs_port)[0][
                    4
                ]
                s.connect(socketaddr)
                w.feed()
                s.send(bytes(rawauthpacket, "utf-8"))
                s.send(bytes(rawpacket, "utf-8"))
            except Exception as error:
                print(
                    bgred(
                        f"[{config.call}] iGateStatus: An exception occurred: {error}"
                    )
                )
                print(
                    purple(
                        f"[{config.call}] Connect to ARPS {config.aprs_host} {config.aprs_port} Failed ! Lost Packet ! Restarting system !"
                    )
                )
                microcontroller.reset()
        print(purple(f"[{config.call}] iGateStatus: {rawpacket}"), end="")
        aprs = APRS()
        pos = aprs.makePosition(
            config.latitude, config.longitude, -1, -1, config.symbol
        )
        altitude = "/A={:06d}".format(int(config.altitude * 3.2808399))
        comment = config.comment + altitude
        ts = aprs.makeTimestamp("z", now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        message = f"{config.call}>APRFGI,TCPIP*:@{ts}{pos}{comment}\n"
        try:
            w.feed()
            s.send(bytes(message, "utf-8"))
        except Exception as error:
            print(bgred(f"[{config.call}] iGateStatus: An exception occurred: {error}"))
            print(
                purple(
                    f"[{config.call}] iGateStatus: Reconnecting to ARPS {config.aprs_host} {config.aprs_port}"
                )
            )
            s.close()
            socket.set_interface(esp)
            requests.set_socket(socket, esp)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            try:
                socketaddr = socket.getaddrinfo(config.aprs_host, config.aprs_port)[0][
                    4
                ]
                s.connect(socketaddr)
                w.feed()
                s.send(bytes(rawauthpacket, "utf-8"))
                s.send(bytes(message, "utf-8"))
            except Exception as error:
                print(
                    bgred(
                        f"[{config.call}] iGateStatus: An exception occurred: {error}"
                    )
                )
                print(
                    purple(
                        f"[{config.call}] iGateStatus: Connect to ARPS {config.aprs_host} {config.aprs_port} Failed ! Lost Packet ! Restarting system !"
                    )
                )
                microcontroller.reset()

        print(purple(f"[{config.call}] iGatePossition: {message}"), end="")
        await asyncio.sleep(15 * 60)


async def tcpPost(packet):
    # Sends an APRS packet over TCP to the APRS-IS server.
    # Handles reconnecting if the send fails.
    global w, s, rawauthpacket
    w.feed()
    rawpacket = f"{packet}\n"
    try:
        await asyncio.sleep(0)
        s.settimeout(4)
        s.send(bytes(rawpacket, "utf-8"))
    except Exception as error:
        print(bgred(f"[{config.call}] aprsTCPSend: An exception occurred: {error}"))
        print(
            purple(
                f"[{config.call}] aprsTCPSend: Reconnecting to ARPS {config.aprs_host} {config.aprs_port}"
            )
        )
        s.close()
        socket.set_interface(esp)
        requests.set_socket(socket, esp)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        try:
            socketaddr = socket.getaddrinfo(config.aprs_host, config.aprs_port)[0][4]
            s.connect(socketaddr)
            w.feed()
            s.send(bytes(rawauthpacket, "utf-8"))
            s.send(bytes(rawpacket, "utf-8"))
        except Exception as error:
            print(bgred(f"[{config.call}] aprsTCPSend: An exception occurred: {error}"))
            print(
                purple(
                    f"[{config.call}] aprsTCPSend: Reconnecting to ARPS {config.aprs_host} {config.aprs_port} Failed ! Lost Packet ! Restarting system !"
                )
            )
            microcontroller.reset()
    print(blue(f"[{config.call}] aprsTCPSend: {packet}"))
    await asyncio.sleep(0)


async def aprsMsgFeed():
    # read the ARPS feed for text messages and queues them for transmit
    await asyncio.sleep(2)
    print(purple(f"[{config.call}] aprsMsgFeed: receiving APRS messages"))
    global w, s, rawauthpacket, txmsgs
    while True:
        try:
            while True:
                await asyncio.sleep(0)
                w.feed()
                s.settimeout(0.01)
                buff = s.recv(1024)
                raw = buff.decode("utf-8")
                for line in raw.splitlines():
                    if not line.startswith("#"):
                        if line[0].isupper():
                            station = (line.split(">", 1))[0]
                            data = (line.split("::", 1))[1]
                            packet = (
                                f"{config.call}>APRFGD,RFONLY,WIDE1-1::{station}:{data}"
                            )
                            txmsgs.append(packet)
                await asyncio.sleep(0)
        except socket.timeout:
            continue
            # we ignore the timeout
        except UnicodeError:
            continue
            # we ignore decode errors


async def loraRunner(loop):
    await asyncio.sleep(5)
    global w, txmsgs
    # Continuously receives LoRa packets and forwards valid APRS packets
    # via WiFi. Configures LoRa radio, prints status messages, handles
    # exceptions, creates asyncio tasks to process packets.
    # LoRa APRS frequency
    RADIO_FREQ_MHZ = 433.775
    CS = DigitalInOut(board.GP21)
    RESET = DigitalInOut(board.GP20)
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP8)
    rfm9x = adafruit_rfm9x.RFM9x(
        spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False, crc=True
    )
    if igate is False:
        rfm9x.tx_power = 23

    while True:
        await asyncio.sleep(0)
        w.feed()
        timeout = int(loraTimeout) + random.randint(1, 9)
        print(
            purple(
                f"[{config.call}] loraRunner: Waiting for lora APRS packet timeout:{timeout} ...\r"
            ),
            end="",
        )
        packet = rfm9x.receive(w, with_header=True, timeout=timeout)
        # packet = await rfm9x.areceive(with_header=True, timeout=timeout)
        if packet is not None:
            if packet[:3] == (b"<\xff\x01"):
                try:
                    rawdata = bytes(packet[3:]).decode("utf-8")
                    print(
                        green(
                            f"[{config.call}] loraRunner: RX: RSSI:{rfm9x.last_rssi} SNR:{rfm9x.last_snr} Data:{rawdata}"
                        )
                    )
                    wifi.pixel_status((100, 100, 0))
                    loop.create_task(tcpPost(rawdata))
                    await asyncio.sleep(0)
                    wifi.pixel_status((0, 100, 0))
                except Exception as error:
                    print(
                        bgred(
                            f"[{config.call}] loraRunner: An exception occurred: {error}"
                        )
                    )
                    print(
                        purple(
                            f"[{config.call}] loraRunner: Lost Packet, unable to decode, skipping"
                        )
                    )
                    continue
        if igate is False:
            if len(txmsgs) != 0:
                print()
                biast.value = False
                transmit.value = True
                pa.value = True
                while len(txmsgs) != 0:
                    w.feed()
                    packet = txmsgs.pop(0)
                    print(red(f"[{config.call}] loraRunner: TX: {packet}"))
                    await rfm9x.asend(
                        bytes("{}".format("<"), "UTF-8")
                        + binascii.unhexlify("FF")
                        + binascii.unhexlify("01")
                        + bytes("{}".format(packet), "UTF-8"),
                    )
                    w.feed()
            pa.value = False
            transmit.value = False
            if config.biast is True:
                biast.value = True


async def main():
    # Create asyncio tasks to run the LoRa receiver, APRS message feed,
    # and iGate announcement in parallel. Gather the tasks and wait for
    # them to complete wich will never happen ;)
    loop = asyncio.get_event_loop()
    loraR = asyncio.create_task(loraRunner(loop))
    loraA = asyncio.create_task(iGateAnnounce())
    if igate is False:
        loraM = asyncio.create_task(aprsMsgFeed())
        await asyncio.gather(loraA, loraM, loraR)
    else:
        await asyncio.gather(loraA, loraR)


asyncio.run(main())
