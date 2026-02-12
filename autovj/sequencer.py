import random


# Effect pools by energy level
# IDs correspond to EFFECTS_FACTORY keys
POOL_LOW = [1, 4, 6, 9]        # posterize, kaleido, trails, thermal
POOL_MID = [2, 3, 5, 7, 11]    # contours, glitch, scanlines, chromatic, edge_neon
POOL_HIGH = [3, 5, 7, 8, 10, 12]  # glitch, scanlines, chromatic, pixel_sort, strobe, vhs


class Sequencer:
    """Selects effect combinations based on energy level."""

    def __init__(self):
        self._last_selection = []

    def select(self, energy_level):
        """Return a list of effect IDs based on energy level (0-1).

        Args:
            energy_level: Combined energy from motion + audio (0.0 to 1.0)

        Returns:
            List of effect IDs to activate
        """
        if energy_level < 0.3:
            # Low energy: 1 subtle effect
            pool = POOL_LOW
            count = 1
        elif energy_level < 0.7:
            # Mid energy: 2 moderate effects
            pool = POOL_MID
            count = 2
        else:
            # High energy: 2-3 intense effects
            pool = POOL_HIGH
            count = random.choice([2, 3])

        # Pick random effects, avoid repeating same combo
        selection = random.sample(pool, min(count, len(pool)))

        # Try to avoid exact same selection as last time
        if selection == self._last_selection and len(pool) > count:
            selection = random.sample(pool, min(count, len(pool)))

        self._last_selection = selection
        return selection
