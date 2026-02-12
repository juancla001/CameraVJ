class Effect:
    name = "base"

    def reset(self):
        pass

    def set_controls(self, controls: dict):
        """
        controls ejemplo:
        {
          "motion": 0.0..1.0,
          "zones": {"left":..,"right":..,"top":..,"bottom":..}
        }
        """
        pass

    def apply(self, frame):
        return frame
