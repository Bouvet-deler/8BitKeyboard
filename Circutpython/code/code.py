import usb_hid
import time
import board
from digitalio import DigitalInOut, Direction, Pull
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
from adafruit_bitmap_font import bitmap_font
from displayio import Bitmap
import neopixel
from adafruit_led_animation.animation.rainbow import Rainbow

print("setup")
bitarray = []

kbd = Keyboard(usb_hid.devices)

button_0 = DigitalInOut(board.GP13)
button_0.direction = Direction.INPUT
button_0.pull = Pull.UP
button_1 = DigitalInOut(board.GP12)
button_1.direction = Direction.INPUT
button_1.pull = Pull.UP

switch_extended = DigitalInOut(board.GP29)
switch_extended.direction = Direction.INPUT
switch_extended.pull = Pull.UP

switch_std = DigitalInOut(board.GP26)
switch_std.direction = Direction.INPUT
switch_std.pull = Pull.UP

pixel_pin = board.GP16
pixel_num = 1
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, brightness=0.5, auto_write=False)
rainbow = Rainbow(pixels, speed=0.05, period=20)

displayio.release_displays()

i2c = busio.I2C(board.GP1, board.GP0)

display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)
display.rotation = 180

font = bitmap_font.load_font("fonts/LeagueSpartan-Bold-16.bdf", Bitmap)

# Make the display context
splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(128, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

print("setup finished")

def bitarrayToNumber(bitarray, padded):
    bitstring = ''.join(str(bit) for bit in bitarray)
    number = int(bitstring, 2)
    if padded:
        return '0' + str(number)
    return str(number)

# https://docs.circuitpython.org/projects/hid/en/latest/_modules/adafruit_hid/keycode.html
def intToUsbCodeArray(unicode):
    usbcodes = []
    for number in unicode:
        if number == '0':
            # Keycode.KEYPAD_ZERO)
            usbcodes.append(98)  
            continue
        usbcodes.append(Keycode.KEYPAD_ENTER + int(number))
    return usbcodes

def sendRealKeyStroke(asciiCode):
    if asciiCode == 48:
        kbd.send(Keycode.ZERO)
    elif (asciiCode >= 49 and asciiCode <= 57):
        kbd.send(asciiCode-49 + Keycode.ONE)
    elif (asciiCode >= 65 and asciiCode <= 90):
        kbd.send(asciiCode-65 + Keycode.A)
    elif (asciiCode >= 97 and asciiCode <= 122):
        kbd.send(asciiCode-97 + Keycode.A)


def sendAltNumpadKeystroke(number):
    usbcodes = intToUsbCodeArray(number)

    kbd.press(Keycode.ALT)

    for key in usbcodes:
        kbd.press(key)
        kbd.release(key)
    kbd.release_all()

def bitarrayToDisplayContent(bitarray):
    bitstring = ''.join(str(bit) for bit in bitarray)
    bitstring = bitstring + "_" * (8 - len(bitstring))
    return bitstring

def displayContent(content):
    # print out the bitarray with constant positioning of each number
    print(content)
    for i in range(8):
        if content[i] == '1':
            text_area[(i*2)+1].text = content[i]
            text_area[i*2].text = ''
        else:
            text_area[i*2].text = content[i]
            text_area[(i*2)+1].text = ''

import time

def wait_for_button_or_timeout(timeout):
    start_time = time.time()

    while True:
        if not button_0.value or not button_1.value:
            break

        if time.time() - start_time > timeout:
            break

def displayUnicodeIfPossible(number):
    displayContent("        ")
    # blank out display with a white rectangle
    inner_palette[0] = 0xFFFFFF
    time.sleep(0.2)
    inner_palette[0] = 0x000000
    unicode = int(number)

    if switch_std.value:
        if (unicode >= 48 and unicode <= 57) or (unicode >= 97 and unicode <= 122):
            unicodeArea.text = str(chr(unicode))
        elif (unicode >= 65 and unicode <= 90):
            unicodeArea.text = str(chr(unicode + 32))
        else:
            unicodeArea.text = "??"
    else:
        if (unicode >= 33 and unicode <= 126):
            unicodeArea.text = str(chr(unicode))
        else:
            unicodeArea.text = "??"
    wait_for_button_or_timeout(1)

def restart():
    bitarray.clear()
    time.sleep(0.1)
    # blank out display with a white rectangle
    inner_palette[0] = 0xFFFFFF
    time.sleep(0.1)
    inner_palette[0] = 0x000000
    unicodeArea.text = ""

# def updateNeopixel():
    # todo: create a rainbow effect

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(126, 30, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black

inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=1, y=1)
splash.append(inner_sprite)


text_area = []
for i in range(16):
    xcoordiante = (5 + i*15)
    text_area.append(label.Label(font, text='_', color=0xFFFFFF, x= xcoordiante, y=17))
    text_area.append(label.Label(font, text='', color=0xFFFFFF, x= xcoordiante+2, y=17))
    splash.append(text_area[i])

unicodeArea = label.Label(font, text='', color=0xFFFFFF, x=50, y=17)
splash.append(unicodeArea)

prev_button_0 = button_0.value
prev_button_1 = button_1.value
old_bitarray_len = len(bitarray)
both_pressed_executed = False

while True:
    if not button_0.value and not button_1.value:
        if not both_pressed_executed:
            print("both pressed, sending backspace")
            kbd.send(Keycode.BACKSPACE)
            restart()
            both_pressed_executed = True
    else:
        both_pressed_executed = False
        if button_0.value != prev_button_0:
            if not button_0.value:
                bitarray.append(0)
            prev_button_0 = button_0.value
        elif button_1.value != prev_button_1:
            if not button_1.value:
                bitarray.append(1)
            prev_button_1 = button_1.value

    time.sleep(0.05)

    if len(bitarray) != old_bitarray_len:
        print(bitarray)
        old_bitarray_len = len(bitarray)
        # update display with bitarray
        content = bitarrayToDisplayContent(bitarray)
        displayContent(content)

    if len(bitarray) > 7:
        number = bitarrayToNumber(bitarray, switch_extended.value)
        print(number)
        if switch_std.value:
            sendRealKeyStroke(int(number))
        else:
            sendAltNumpadKeystroke(number)
        displayUnicodeIfPossible(number)
        restart()

    rainbow.animate()
