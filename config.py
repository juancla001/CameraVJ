CAMERA_INDEX = 0
CAPTURE_BACKEND = "MSMF"  # o "DSHOW" (dejá el que te dio mejores FPS)

WINDOW_NAME = "CameraVJ"

# Perfil: perf = sin overlays/prints, debug = logs
PROFILE = "perf"

# Preview: si querés bajar carga de render, podés usar 0.5 (mitad) o 1.0 (full)
PREVIEW_SCALE = 1.0

# UI / modo show
SHOW_HUD_DEFAULT = False
PERF_MODE_DEFAULT = True

# Preview scale: 1.0 full, 0.75 o 0.5 si querés más FPS
PREVIEW_SCALE_PERF = 1.2
PREVIEW_SCALE_DEBUG = 1.2

# --- FASE 2: Motion tuning ---
MOTION_SCALE = 0.5        # resolución interna del detector (0.4–0.7 recomendado)
MOTION_SMOOTH = 0.2       # suavizado EMA (0.1–0.3)
MOTION_GAIN = 2.5         # multiplica sensibilidad (1.0–4.0)
MOTION_DEADZONE = 0.02    # ignora movimiento chiquito (0.01–0.05)

