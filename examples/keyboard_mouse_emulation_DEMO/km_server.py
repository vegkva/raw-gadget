import asyncio
import websockets
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

MOUSE_FILE = "/tmp/mouse_delta"
KBD_FILE   = "/tmp/kbd_event"


# ----------------------------
# Shared state (websocket side)
# ----------------------------
state = {
    "dx": 0,
    "dy": 0,
    "btn": 0,
    "wheel": 0,
    "mod": 0,
    "key": 0
}

# ----------------------------
# HTML (same behavior as before)
# ----------------------------
HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>HID Web Control</title>
<style>
body {
    margin:0;
    height:100vh;
    background:#111;
    color:white;
    display:flex;
    justify-content:center;
    align-items:center;
    user-select:none;
    font-family:sans-serif;
}
</style>
</head>
<body>

HID Control Active

<script>
const ws = new WebSocket("ws://192.168.119.130:8765");

let lastX = null;
let lastY = null;

// ---------------- mouse move ----------------
document.addEventListener("mousemove", (e) => {
    if (lastX === null) {
        lastX = e.clientX;
        lastY = e.clientY;
        return;
    }

    let dx = e.clientX - lastX;
    let dy = e.clientY - lastY;

    lastX = e.clientX;
    lastY = e.clientY;

    ws.send(JSON.stringify({type:"move", dx, dy}));
});

// ---------------- buttons ----------------
document.addEventListener("mousedown", (e) => {
    if (e.button === 0) ws.send(JSON.stringify({type:"btn", btn:1, down:1}));
    if (e.button === 2) ws.send(JSON.stringify({type:"btn", btn:2, down:1}));
});

document.addEventListener("mouseup", (e) => {
    if (e.button === 0) ws.send(JSON.stringify({type:"btn", btn:1, down:0}));
    if (e.button === 2) ws.send(JSON.stringify({type:"btn", btn:2, down:0}));
});

document.addEventListener("contextmenu", e => e.preventDefault());

// ---------------- wheel ----------------
document.addEventListener("wheel", (e) => {
    let w = e.deltaY;
    w = Math.max(-127, Math.min(127, -w / 10));
    ws.send(JSON.stringify({type:"wheel", wheel:w}));
});

// ---------------- keyboard ----------------

const pressed = new Set();
function sendKeyboardState() {

    let mod = 0;
    let key = 0;

    // -----------------------------
    // modifiers
    // -----------------------------

    if (pressed.has("ControlLeft"))  mod |= 0x01;
    if (pressed.has("ShiftLeft"))    mod |= 0x02;
    if (pressed.has("AltLeft"))      mod |= 0x04;
    if (pressed.has("MetaLeft"))     mod |= 0x08;

    if (pressed.has("ControlRight")) mod |= 0x10;
    if (pressed.has("ShiftRight"))   mod |= 0x20;
    if (pressed.has("AltRight"))     mod |= 0x40;
    if (pressed.has("MetaRight"))    mod |= 0x80;

    // -----------------------------
    // regular HID keys
    // first non-modifier wins
    // -----------------------------

    const HID = {

    // =========================
    // LETTERS
    // =========================
    "KeyA": 0x04,
    "KeyB": 0x05,
    "KeyC": 0x06,
    "KeyD": 0x07,
    "KeyE": 0x08,
    "KeyF": 0x09,
    "KeyG": 0x0A,
    "KeyH": 0x0B,
    "KeyI": 0x0C,
    "KeyJ": 0x0D,
    "KeyK": 0x0E,
    "KeyL": 0x0F,
    "KeyM": 0x10,
    "KeyN": 0x11,
    "KeyO": 0x12,
    "KeyP": 0x13,
    "KeyQ": 0x14,
    "KeyR": 0x15,
    "KeyS": 0x16,
    "KeyT": 0x17,
    "KeyU": 0x18,
    "KeyV": 0x19,
    "KeyW": 0x1A,
    "KeyX": 0x1B,
    "KeyY": 0x1C,
    "KeyZ": 0x1D,

    // =========================
    // NUMBER ROW
    // =========================
    "Digit1": 0x1E,
    "Digit2": 0x1F,
    "Digit3": 0x20,
    "Digit4": 0x21,
    "Digit5": 0x22,
    "Digit6": 0x23,
    "Digit7": 0x24,
    "Digit8": 0x25,
    "Digit9": 0x26,
    "Digit0": 0x27,

    // =========================
    // BASIC KEYS
    // =========================
    "Enter": 0x28,
    "Escape": 0x29,
    "Backspace": 0x2A,
    "Tab": 0x2B,
    "Space": 0x2C,

    // =========================
    // SYMBOLS
    // =========================
    "Minus": 0x2D,          // -
    "Equal": 0x2E,          // =
    "BracketLeft": 0x2F,    // [
    "BracketRight": 0x30,   // ]
    "Backslash": 0x31,      // \
    "Semicolon": 0x33,      // ;
    "Quote": 0x34,          // '
    "Backquote": 0x35,      // `
    "Comma": 0x36,          // ,
    "Period": 0x37,         // .
    "Slash": 0x38,          // /

    // =========================
    // LOCKS
    // =========================
    "CapsLock": 0x39,
    "ScrollLock": 0x47,
    "Pause": 0x48,
    "NumLock": 0x53,

    // =========================
    // FUNCTION KEYS
    // =========================
    "F1": 0x3A,
    "F2": 0x3B,
    "F3": 0x3C,
    "F4": 0x3D,
    "F5": 0x3E,
    "F6": 0x3F,
    "F7": 0x40,
    "F8": 0x41,
    "F9": 0x42,
    "F10": 0x43,
    "F11": 0x44,
    "F12": 0x45,

    // =========================
    // NAVIGATION
    // =========================
    "Insert": 0x49,
    "Home": 0x4A,
    "PageUp": 0x4B,
    "Delete": 0x4C,
    "End": 0x4D,
    "PageDown": 0x4E,
    "ArrowRight": 0x4F,
    "ArrowLeft": 0x50,
    "ArrowDown": 0x51,
    "ArrowUp": 0x52,

    // =========================
    // NUMPAD
    // =========================
    "NumpadDivide": 0x54,
    "NumpadMultiply": 0x55,
    "NumpadSubtract": 0x56,
    "NumpadAdd": 0x57,
    "NumpadEnter": 0x58,

    "Numpad1": 0x59,
    "Numpad2": 0x5A,
    "Numpad3": 0x5B,
    "Numpad4": 0x5C,
    "Numpad5": 0x5D,
    "Numpad6": 0x5E,
    "Numpad7": 0x5F,
    "Numpad8": 0x60,
    "Numpad9": 0x61,
    "Numpad0": 0x62,
    "NumpadDecimal": 0x63,

    // =========================
    // EXTRA
    // =========================
    "ContextMenu": 0x65,
    "Power": 0x66,

    // =========================
    // MEDIA KEYS
    // =========================
    "AudioVolumeMute": 0x7F,
    "AudioVolumeUp": 0x80,
    "AudioVolumeDown": 0x81,

    // =========================
    // INTERNATIONAL
    // =========================
    "IntlBackslash": 0x64,
    "IntlRo": 0x87,
    "IntlYen": 0x89,

  
};


const MOD = {
    "ControlLeft":  0x01,
    "ShiftLeft":    0x02,
    "AltLeft":      0x04,
    "MetaLeft":     0x08,

    "ControlRight": 0x10,
    "ShiftRight":   0x20,
    "AltRight":     0x40,
    "MetaRight":    0x80
};

    for (const k of pressed) {

        if (HID[k]) {
            key = HID[k];
            break;
        }
    }

    ws.send(JSON.stringify({
        type: "key",
        mod: mod,
        key: key
    }));
}


// -----------------------------
// keydown
// -----------------------------
document.addEventListener("keydown", (e) => {

    pressed.add(e.code);

    sendKeyboardState();

    e.preventDefault();
});


// -----------------------------
// keyup
// -----------------------------
document.addEventListener("keyup", (e) => {

    pressed.delete(e.code);

    sendKeyboardState();

    e.preventDefault();
});


// -----------------------------
// clear stuck keys on focus loss
// -----------------------------
window.addEventListener("blur", () => {

    pressed.clear();

    sendKeyboardState();
});
</script>

</body>
</html>
"""

# ----------------------------
# websocket handler
# ----------------------------
async def handler(ws):
    async for msg in ws:
        try:
            data = json.loads(msg)
            
            # ---------------- mouse ----------------
            if data["type"] == "move":
                state["dx"] += int(data["dx"])
                state["dy"] += int(data["dy"])

            elif data["type"] == "btn":
                # left=1 right=2 bitmask (matches C & 0x03)
                if data["down"]:
                    state["btn"] |= data["btn"]
                else:
                    state["btn"] &= ~data["btn"]

            elif data["type"] == "wheel":
                state["wheel"] += int(data["wheel"])

            # ---------------- keyboard ----------------
            elif data["type"] == "key":
                state["mod"] = int(data["mod"])
                state["key"] = int(data["key"])
                print(state["mod"])
                print(state["key"])

        except:
            pass


# ----------------------------
# writer loops (MATCH C POLLING EXACTLY)
# ----------------------------
async def writer_loop():
    while True:

        # ---------------- MOUSE FILE ----------------
        dx = state["dx"]
        dy = state["dy"]
        btn = state["btn"]
        wheel = state["wheel"]

        with open(MOUSE_FILE, "w") as f:
            f.write(f"{dx} {dy} {btn} {wheel}")

        # reset like C expects (file is consumed per loop)
        state["dx"] = 0
        state["dy"] = 0
        state["wheel"] = 0

        # ---------------- KEYBOARD FILE ----------------
        mod = state["mod"]
        key = state["key"]

        with open(KBD_FILE, "w") as f:
            f.write(f"{mod} {key}")

        await asyncio.sleep(0.005)  # ~200Hz like your C loop


# ----------------------------
# HTTP server (serves HTML)
# ----------------------------
def start_http():
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(HTML.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args):
            pass

    http = HTTPServer(("0.0.0.0", 8080), H)
    http.serve_forever()


# ----------------------------
# main
# ----------------------------
async def main():
    os.makedirs("/tmp", exist_ok=True)

    with open(MOUSE_FILE, "w") as f:
        f.write("0 0 0 0")

    with open(KBD_FILE, "w") as f:
        f.write("0 0")

    print("HTTP  : http://localhost:8080")
    print("WS    : ws://localhost:8765")

    threading.Thread(target=start_http, daemon=True).start()

    async with websockets.serve(handler, "0.0.0.0", 8765):
        asyncio.create_task(writer_loop())
        await asyncio.Future()


asyncio.run(main())