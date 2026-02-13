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
from .glitch_blocks import GlitchBlocks
from .ascii_art import ASCIIArt
from .particle_rain import ParticleRain
from .color_invert_pulse import ColorInvertPulse
from .datamosh import Datamosh
from .zoom_pulse import ZoomPulse
from .duotone import Duotone
from .slit_scan import SlitScan


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
    13: GlitchBlocks,
    14: ASCIIArt,
    15: ParticleRain,
    16: ColorInvertPulse,
    17: Datamosh,
    18: ZoomPulse,
    19: Duotone,
    20: SlitScan,
}
