"""
Native Instruments K2 MIDI mapping.

K2 Layout (default MIDI channel):
- Pads: note_on messages (notes vary by mapping)
- Knobs: CC messages
- Fader: CC message

Default K2 mapping (may need adjustment based on actual K2 config):
- Pads 1-16: Notes 36-51 (bottom-left to top-right)
- Knobs 1-8: CC 16-23
- Fader: CC 7
"""


# --- Pad note mapping (adjust if your K2 is mapped differently) ---
PAD_NOTES = {
    36: 1, 37: 2, 38: 3, 39: 4,     # Bottom row
    40: 5, 41: 6, 42: 7, 43: 8,     # Second row
    44: 9, 45: 10, 46: 11, 47: 12,  # Third row
    48: 13, 49: 14, 50: 15, 51: 16, # Top row
}

# --- Knob CC mapping ---
KNOB_CCS = {
    16: 0, 17: 1, 18: 2, 19: 3,  # Knobs 1-4
    20: 4, 21: 5, 22: 6, 23: 7,  # Knobs 5-8
}

# --- Fader CC ---
FADER_CC = 7


class K2State:
    """Holds parsed K2 controller state."""

    def __init__(self):
        self.pads = {}       # pad_num (1-16) -> True/False (last press)
        self.knobs = [0.0] * 8   # knob values 0.0-1.0
        self.fader = 1.0     # fader value 0.0-1.0

    def process_message(self, msg):
        """Process a mido message and return (event_type, data) or None."""
        if msg.type == "note_on" and msg.velocity > 0:
            pad_num = PAD_NOTES.get(msg.note)
            if pad_num is not None:
                self.pads[pad_num] = True
                return ("pad", pad_num)

        elif msg.type == "control_change":
            knob_idx = KNOB_CCS.get(msg.control)
            if knob_idx is not None:
                self.knobs[knob_idx] = msg.value / 127.0
                return ("knob", knob_idx, self.knobs[knob_idx])

            if msg.control == FADER_CC:
                self.fader = msg.value / 127.0
                return ("fader", self.fader)

        return None
