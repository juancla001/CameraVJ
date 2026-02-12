from .color_posterize import ColorPosterize
from .contours_glow import ContoursGlow
from .feedback_glitch import FeedbackGlitch
from .mirror_kaleido import MirrorKaleido
from .scanlines_rgbshift import ScanlinesRGBShift
from .motion_trails import MotionTrails
from .chromatic_aberration import ChromaticAberration
from .pixel_sort import PixelSort
from .thermal_vision import ThermalVision
from .strobe_flash import StrobeFlash
from .edge_neon import EdgeNeon
from .vhs_retro import VHSRetro


EFFECTS_FACTORY = {
    1: ColorPosterize,
    2: ContoursGlow,
    3: FeedbackGlitch,
    4: MirrorKaleido,
    5: ScanlinesRGBShift,
    6: MotionTrails,
    7: ChromaticAberration,
    8: PixelSort,
    9: ThermalVision,
    10: StrobeFlash,
    11: EdgeNeon,
    12: VHSRetro,
}
