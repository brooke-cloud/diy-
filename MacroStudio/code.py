import board
import keypad
import json
import time
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

# SW1=GP2, SW2=GP3, SW3=GP8, SW4=GP5, SW5=GP6, SW6=GP7
PINS = (board.GP2, board.GP3, board.GP8, board.GP5, board.GP6, board.GP7)

DEFAULT_CONFIG = {
    "version": 1,
    "keys": [
        {"type": "hotkey", "value": "CTRL+C"},
        {"type": "hotkey", "value": "CTRL+V"},
        {"type": "hotkey", "value": "CTRL+Z"},
        {"type": "hotkey", "value": "ALT+TAB"},
        {"type": "hotkey", "value": "WIN+SHIFT+S"},
        {"type": "key", "value": "F5"}
    ]
}

ALIASES = {
    "CTRL": "LEFT_CONTROL", "CONTROL": "LEFT_CONTROL",
    "SHIFT": "LEFT_SHIFT", "ALT": "LEFT_ALT",
    "WIN": "LEFT_GUI", "GUI": "LEFT_GUI",
    "ESC": "ESCAPE", "RETURN": "ENTER",
    "UP": "UP_ARROW", "DOWN": "DOWN_ARROW",
    "LEFT": "LEFT_ARROW", "RIGHT": "RIGHT_ARROW",
    "PGUP": "PAGE_UP", "PGDN": "PAGE_DOWN"
}

def read_config():
    try:
        with open("/config.json", "r") as f:
            raw = f.read()
        data = json.loads(raw)
        if not isinstance(data, dict) or len(data.get("keys", [])) != 6:
            raise ValueError("config.json must contain 6 actions")
        return data, raw
    except Exception as error:
        raise ValueError("Invalid config.json: " + str(error))

def load_config():
    try:
        data, raw = read_config()
        print("Loaded config.json")
        return data, raw
    except Exception as error:
        print("Using default config:", error)
        return DEFAULT_CONFIG, ""

def resolve_key(name):
    token = name.strip().upper()
    token = ALIASES.get(token, token)
    return getattr(Keycode, token)

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
config, config_source = load_config()
keys = keypad.Keys(PINS, value_when_pressed=False, pull=True)
last_config_check = time.monotonic()

def run_action(action, index):
    try:
        kind = action.get("type", "key")
        value = str(action.get("value", ""))
        if kind == "text":
            layout.write(value)
            print("SW", index + 1, "TEXT sent")
        elif kind == "key":
            keyboard.send(resolve_key(value))
            print("SW", index + 1, "KEY", value)
        elif kind == "hotkey":
            names = [part.strip() for part in value.split("+") if part.strip()]
            codes = [resolve_key(name) for name in names]
            if not codes:
                raise ValueError("Empty hotkey")
            keyboard.press(*codes)
            time.sleep(0.04)
            keyboard.release_all()
            print("SW", index + 1, "HOTKEY", value)
        else:
            print("Unknown action type:", kind)
    except Exception as error:
        keyboard.release_all()
        print("Action error SW", index + 1, ":", error)

print("6-Key Macro Studio V1.1 ready")
print("GPIO: GP2, GP3, GP8, GP5, GP6, GP7")

while True:
    # config.json is watched at runtime, so saving from Macro Studio takes effect
    # without pressing RESET or unplugging the keyboard.
    now = time.monotonic()
    if now - last_config_check >= 0.5:
        last_config_check = now
        try:
            new_config, new_source = read_config()
            if new_source != config_source:
                keyboard.release_all()
                config = new_config
                config_source = new_source
                print("Reloaded config.json")
        except Exception as error:
            # Keep the last known-good configuration while a file is being
            # written or when an invalid configuration is supplied.
            print("Config reload skipped:", error)

    event = keys.events.get()
    if event and event.pressed:
        run_action(config["keys"][event.key_number], event.key_number)
    time.sleep(0.001)
