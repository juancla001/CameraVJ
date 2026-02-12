import cv2
import mediapipe as mp
import numpy as np


class PoseEstimator:
    """
    MediaPipe Pose wrapper:
    - update(frame_bgr) -> pose_dict (landmarks normalizados + algunos scores)
    """
    def __init__(self, model_complexity=1, smooth=True, det_conf=0.5, track_conf=0.5):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=int(model_complexity),
            smooth_landmarks=bool(smooth),
            min_detection_confidence=float(det_conf),
            min_tracking_confidence=float(track_conf),
        )

    def update(self, frame_bgr):
        # MediaPipe usa RGB
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = self.pose.process(rgb)

        if not res.pose_landmarks:
            return None

        lm = res.pose_landmarks.landmark

        # landmarks normalizados (x,y en 0..1)
        # devolvemos solo los que vamos a usar
        def pt(i):
            return (float(lm[i].x), float(lm[i].y), float(lm[i].visibility))

        # índices relevantes
        # 11 L shoulder, 12 R shoulder
        # 13 L elbow, 14 R elbow
        # 15 L wrist, 16 R wrist
        # 23 L hip, 24 R hip
        data = {
            "l_shoulder": pt(11),
            "r_shoulder": pt(12),
            "l_elbow": pt(13),
            "r_elbow": pt(14),
            "l_wrist": pt(15),
            "r_wrist": pt(16),
            "l_hip": pt(23),
            "r_hip": pt(24),
            "all": lm,  # por si querés dibujar todo
        }
        return data


def _to_px(p, w, h):
    x, y, v = p
    return int(x * w), int(y * h), v


class NeonSkeletonRenderer:
    """
    Dibuja un skeleton “neon” y trails simples.
    - render(frame, pose_data) -> frame_out
    """
    def __init__(self, trail_len=12, glow=2):
        self.trail_len = int(trail_len)
        self.glow = int(glow)
        self.trails = {"l_wrist": [], "r_wrist": []}

        # conexiones básicas (para mantenerlo barato)
        self.edges = [
            ("l_shoulder", "l_elbow"),
            ("l_elbow", "l_wrist"),
            ("r_shoulder", "r_elbow"),
            ("r_elbow", "r_wrist"),
            ("l_shoulder", "r_shoulder"),
            ("l_hip", "r_hip"),
            ("l_shoulder", "l_hip"),
            ("r_shoulder", "r_hip"),
        ]

    def _push_trail(self, key, xy):
        t = self.trails[key]
        t.append(xy)
        if len(t) > self.trail_len:
            t.pop(0)

    def render(self, frame, pose_data):
        if pose_data is None:
            return frame

        h, w = frame.shape[:2]
        out = frame.copy()

        # capa glow (dibujamos en una máscara y la mezclamos)
        glow_layer = np.zeros_like(frame)

        # trails: muñecas
        lw = _to_px(pose_data["l_wrist"], w, h)
        rw = _to_px(pose_data["r_wrist"], w, h)

        if lw[2] > 0.4:
            self._push_trail("l_wrist", (lw[0], lw[1]))
        if rw[2] > 0.4:
            self._push_trail("r_wrist", (rw[0], rw[1]))

        # dibujar edges
        for a, b in self.edges:
            ax, ay, av = _to_px(pose_data[a], w, h)
            bx, by, bv = _to_px(pose_data[b], w, h)
            if av > 0.4 and bv > 0.4:
                cv2.line(glow_layer, (ax, ay), (bx, by), (0, 255, 255), 6, cv2.LINE_AA)
                cv2.line(out, (ax, ay), (bx, by), (255, 255, 255), 2, cv2.LINE_AA)

        # trails glow
        for key in ("l_wrist", "r_wrist"):
            pts = self.trails[key]
            for i in range(1, len(pts)):
                p1 = pts[i - 1]
                p2 = pts[i]
                thickness = 2 + i  # crece hacia el final
                cv2.line(glow_layer, p1, p2, (255, 0, 255), thickness + 4, cv2.LINE_AA)
                cv2.line(out, p1, p2, (255, 255, 255), thickness, cv2.LINE_AA)

        # blur para “glow”
        k = 9 + 2 * self.glow
        if k % 2 == 0:
            k += 1
        glow_blur = cv2.GaussianBlur(glow_layer, (k, k), 0)

        # mezcla aditiva
        out = cv2.addWeighted(out, 1.0, glow_blur, 0.6, 0.0)
        return out


def detect_gestures(pose_data):
    """
    Gestos simples:
    - hands_up: muñecas por arriba de hombros
    - arms_open: muñecas muy separadas horizontalmente
    """
    if pose_data is None:
        return {"hands_up": False, "arms_open": False}

    ls = pose_data["l_shoulder"]
    rs = pose_data["r_shoulder"]
    lw = pose_data["l_wrist"]
    rw = pose_data["r_wrist"]

    # visibilidad mínima
    if min(ls[2], rs[2], lw[2], rw[2]) < 0.4:
        return {"hands_up": False, "arms_open": False}

    hands_up = (lw[1] < ls[1]) and (rw[1] < rs[1])  # y menor = más arriba
    arms_open = abs(lw[0] - rw[0]) > 0.65           # separación grande

    return {"hands_up": hands_up, "arms_open": arms_open}
