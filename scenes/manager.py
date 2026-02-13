import json
import os

SCENES_FILE = "scenes.json"
MAX_SCENES = 8  # F1-F8


class SceneManager:
    """Save and load effect stack configurations (scenes).

    Scenes store:
    - Effect IDs in the stack
    - Active effect index
    - Preset index
    - Per-effect parameters
    """

    def __init__(self, filepath=SCENES_FILE):
        self.filepath = filepath
        self.scenes = {}
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.scenes = json.load(f)
                print(f"[scenes] loaded {len(self.scenes)} scenes from {self.filepath}")
            except Exception as e:
                print(f"[scenes] failed to load: {e}")
                self.scenes = {}

    def _save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.scenes, f, indent=2)
        except Exception as e:
            print(f"[scenes] failed to save: {e}")

    def save_scene(self, slot, runner):
        """Save current effect stack to a slot (1-8).

        Args:
            slot: Scene slot number (1-8)
            runner: PipelineRunner instance
        """
        if slot < 1 or slot > MAX_SCENES:
            return

        scene = {
            "effects": [],
            "active_idx": runner.active_idx,
            "preset_idx": runner.preset_idx,
        }

        for eid, effect in runner.effect_stack:
            effect_data = {
                "id": eid,
                "params": self._extract_params(effect),
            }
            scene["effects"].append(effect_data)

        self.scenes[str(slot)] = scene
        self._save()
        names = [str(e["id"]) for e in scene["effects"]]
        print(f"[scenes] saved slot {slot}: [{','.join(names)}]")

    def load_scene(self, slot, runner):
        """Load a scene from slot into runner.

        Args:
            slot: Scene slot number (1-8)
            runner: PipelineRunner instance
        """
        key = str(slot)
        if key not in self.scenes:
            print(f"[scenes] slot {slot} is empty")
            return

        scene = self.scenes[key]

        # Clear current stack
        runner._clear_effects()

        # Load effects
        for effect_data in scene.get("effects", []):
            eid = effect_data["id"]
            runner._toggle_effect(eid)

            # Apply saved params
            if runner.effect_stack:
                _, effect = runner.effect_stack[-1]
                self._apply_params(effect, effect_data.get("params", {}))

        runner.active_idx = min(
            scene.get("active_idx", 0),
            max(0, len(runner.effect_stack) - 1)
        )
        runner.preset_idx = scene.get("preset_idx", 0)

        names = [str(e["id"]) for e in scene["effects"]]
        print(f"[scenes] loaded slot {slot}: [{','.join(names)}]")

    def _extract_params(self, effect):
        """Extract tunable parameters from an effect."""
        params = {}
        # Common params across effects
        for attr in [
            "levels", "speed", "phase",
            "t1", "t2", "blur_ksize",
            "feedback", "warp", "noise",
            "mode",
            "scan_strength", "shift",
            "persist", "glow",
            "strength", "radial",
            "threshold", "intensity", "direction",
            "contrast", "blur", "_map_idx",
            "rate", "color_mode",
            "hue_speed", "glow_size",
            "tracking_intensity", "color_bleed", "noise_amount",
            "block_count", "max_shift",
            "cell_size", "colored", "font_scale",
            "max_particles",
            "blend", "smooth",
            "corruption", "block_size",
            "amplitude",
            "palette_idx",
            "buffer_size", "spread",
        ]:
            if hasattr(effect, attr):
                val = getattr(effect, attr)
                # Only save serializable types
                if isinstance(val, (int, float, bool, str)):
                    params[attr] = val
        return params

    def _apply_params(self, effect, params):
        """Apply saved parameters to an effect."""
        for attr, val in params.items():
            if hasattr(effect, attr):
                setattr(effect, attr, val)

        # Special: update colormap if _map_idx was saved
        if "_map_idx" in params and hasattr(effect, "_colormaps"):
            idx = int(params["_map_idx"]) % len(effect._colormaps)
            effect.colormap = effect._colormaps[idx]

    def list_scenes(self):
        """Return dict of slot -> effect IDs."""
        result = {}
        for slot, scene in self.scenes.items():
            result[slot] = [e["id"] for e in scene.get("effects", [])]
        return result
