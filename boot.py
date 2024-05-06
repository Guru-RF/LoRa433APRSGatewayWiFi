# Configures board on boot:
# - Disables transmit pins
# - Checks if config button is pressed
#   - If pressed, enables USB drive and console
#   - If not pressed, disables USB drive and enables console
# - Remounts filesystem as read-only
# - Sets USB drive name if enabled
import board
import storage
import usb_cdc
from digitalio import DigitalInOut, Direction, Pull

# 5v biasT
biast = DigitalInOut(board.GP1)
biast.direction = Direction.OUTPUT
biast.value = False

# config button
btn = DigitalInOut(board.GP15)
btn.direction = Direction.INPUT
btn.pull = Pull.UP

# default disable usb drive
if btn.value is True:
    print("boot: button not pressed, disabling drive")
    storage.disable_usb_drive()
    storage.remount("/", readonly=False)

    usb_cdc.enable(console=True, data=False)
else:
    print("boot: button pressed, enable console, enabling drive")

    usb_cdc.enable(console=True, data=False)

    new_name = "APRSGATE"
    storage.remount("/", readonly=False)
    m = storage.getmount("/")
    m.label = new_name
    storage.remount("/", readonly=True)
