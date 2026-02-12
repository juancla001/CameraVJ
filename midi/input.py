import threading

try:
    import mido
    HAS_MIDO = True
except ImportError:
    HAS_MIDO = False


class MidiInput:
    """MIDI input receiver using mido. Auto-detects K2 controller."""

    K2_NAMES = ["traktor", "kontrol", "k2", "ni k2"]

    def __init__(self):
        self._port = None
        self._running = False
        self._messages = []
        self._lock = threading.Lock()
        self._thread = None

    def start(self, port_name=None):
        if not HAS_MIDO:
            print("[midi] mido not installed. Install with: pip install mido python-rtmidi")
            return False

        if port_name is None:
            port_name = self._find_k2()

        if port_name is None:
            available = mido.get_input_names()
            if available:
                port_name = available[0]
                print(f"[midi] K2 not found, using first device: {port_name}")
            else:
                print("[midi] No MIDI devices found")
                return False

        try:
            self._port = mido.open_input(port_name)
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print(f"[midi] Connected to: {port_name}")
            return True
        except Exception as e:
            print(f"[midi] Failed to open {port_name}: {e}")
            return False

    def _find_k2(self):
        """Auto-detect Native Instruments K2."""
        if not HAS_MIDO:
            return None
        for name in mido.get_input_names():
            lower = name.lower()
            for pattern in self.K2_NAMES:
                if pattern in lower:
                    return name
        return None

    def _read_loop(self):
        while self._running and self._port:
            try:
                for msg in self._port.iter_pending():
                    with self._lock:
                        self._messages.append(msg)
            except Exception:
                break
            # Small sleep to avoid busy-waiting
            import time
            time.sleep(0.002)

    def poll(self):
        """Return and clear pending messages."""
        with self._lock:
            msgs = self._messages[:]
            self._messages.clear()
        return msgs

    def stop(self):
        self._running = False
        if self._port:
            self._port.close()
            self._port = None

    @property
    def is_running(self):
        return self._running
