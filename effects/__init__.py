from .color_posterize import ColorPosterize
from .contours_glow import ContoursGlow
from .feedback_glitch import FeedbackGlitch
from .mirror_kaleido import MirrorKaleido
from .scanlines_rgbshift import ScanlinesRGBShift
from .motion_trails import MotionTrails



EFFECTS_FACTORY = {
    1: ColorPosterize,
    2: ContoursGlow,
    3: FeedbackGlitch,
    4: MirrorKaleido,
    5: ScanlinesRGBShift,
    6: MotionTrails,
}