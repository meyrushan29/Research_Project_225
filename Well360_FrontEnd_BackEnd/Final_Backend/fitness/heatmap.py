import cv2
import numpy as np
from collections import deque

# MediaPipe landmark index → human-readable name (33 total)
_LANDMARK_NAMES = [
    "Nose", "Left Eye Inner", "Left Eye", "Left Eye Outer",
    "Right Eye Inner", "Right Eye", "Right Eye Outer",
    "Left Ear", "Right Ear", "Mouth Left", "Mouth Right",
    "Left Shoulder", "Right Shoulder", "Left Elbow", "Right Elbow",
    "Left Wrist", "Right Wrist", "Left Pinky", "Right Pinky",
    "Left Index", "Right Index", "Left Thumb", "Right Thumb",
    "Left Hip", "Right Hip", "Left Knee", "Right Knee",
    "Left Ankle", "Right Ankle", "Left Heel", "Right Heel",
    "Left Foot Index", "Right Foot Index"
]

# Build reverse lookup: name → landmark index (lowercase for robust matching)
_NAME_TO_IDX = {name.lower(): i for i, name in enumerate(_LANDMARK_NAMES)}


class HeatmapVisualizer:
    """
    Motion + SHAP-Weighted Heatmap Visualizer.

    Modes:
      "motion" — classic Gaussian blob per joint, weighted by movement delta
                 (backward-compatible, requires no SHAP data)
      "shap"   — Gaussian blob per joint, SHAP importance replaces the static
                 joint weight, so AI-critical joints glow brighter
    """

    def __init__(self, decay=0.92, kernel_size=21, sigma=4):
        self.heatmap = None
        self.prev_landmarks = None
        self.decay = decay
        self.kernel_size = kernel_size
        self.sigma = sigma
        self.show_heatmap = True

        # SHAP state
        # Dict: landmark_index (int) → normalized SHAP importance (float 0-1)
        self._shap_weights: dict = {}  # empty = motion mode
        self.mode: str = "motion"      # "motion" | "shap"

    # ------------------------------------------------------------------
    # Public API: SHAP weight injection
    # ------------------------------------------------------------------

    def update_shap_weights(self, joint_importance: dict) -> None:
        """
        Feed SHAP joint importance scores into the heatmap.

        Parameters
        ----------
        joint_importance : dict
            Mapping of joint name (str, e.g. "Right Elbow") → importance
            score (float). Values are automatically normalised to [0.1, 1.0]
            so every joint still gets at least a faint glow.
        """
        if not joint_importance:
            return

        # Normalise scores to [0.1 … 1.0] to keep faint glow everywhere
        max_score = max(joint_importance.values()) or 1.0
        self._shap_weights = {}
        for name, score in joint_importance.items():
            idx = _NAME_TO_IDX.get(name.lower())
            if idx is not None:
                normalised = max(0.1, score / max_score)
                self._shap_weights[idx] = normalised

        if self._shap_weights:
            self.mode = "shap"
            print(f"[HeatmapVisualizer] SHAP mode activated — "
                  f"{len(self._shap_weights)} joints weighted.")

    def reset_shap_weights(self) -> None:
        """Revert to pure motion mode (clears SHAP weights)."""
        self._shap_weights = {}
        self.mode = "motion"

    # ------------------------------------------------------------------
    # Gaussian kernel helper
    # ------------------------------------------------------------------

    def create_gaussian_kernel(self, size, sigma):
        ax = np.arange(-size // 2 + 1., size // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
        return kernel / kernel.sum()

    # ------------------------------------------------------------------
    # Core update
    # ------------------------------------------------------------------

    def update_heatmap(self, landmarks, frame_shape):
        h, w = frame_shape[:2]

        # Handle resolution change mid-video
        if self.heatmap is not None:
            if self.heatmap.shape[0] != h or self.heatmap.shape[1] != w:
                self.heatmap = None
                self.prev_landmarks = None

        # Temporal decay
        if self.heatmap is not None:
            self.heatmap *= self.decay
        else:
            self.heatmap = np.zeros((h, w), dtype=np.float32)

        if landmarks is not None:
            # Compute total movement across all joints (used for motion factor)
            total_movement = 0
            if self.prev_landmarks is not None and len(landmarks) == len(self.prev_landmarks):
                for i in range(len(landmarks)):
                    dx = landmarks[i].x - self.prev_landmarks[i].x
                    dy = landmarks[i].y - self.prev_landmarks[i].y
                    total_movement += np.sqrt(dx * dx + dy * dy)

            movement_factor = min(total_movement * 120, 6.0) + 0.3

            kernel = self.create_gaussian_kernel(self.kernel_size, self.sigma)
            half_kernel = self.kernel_size // 2

            for i in range(len(landmarks)):
                x_px = int(landmarks[i].x * w)
                y_px = int(landmarks[i].y * h)

                if x_px < 0 or x_px >= w or y_px < 0 or y_px >= h:
                    continue

                x_start = max(x_px - half_kernel, 0)
                x_end   = min(x_px + half_kernel + 1, w)
                y_start = max(y_px - half_kernel, 0)
                y_end   = min(y_px + half_kernel + 1, h)

                kx_start = max(half_kernel - x_px, 0)
                kx_end   = self.kernel_size - max(x_px + half_kernel + 1 - w, 0)
                ky_start = max(half_kernel - y_px, 0)
                ky_end   = self.kernel_size - max(y_px + half_kernel + 1 - h, 0)

                # ── Joint weight: SHAP mode vs motion mode ──────────────
                if self.mode == "shap" and self._shap_weights:
                    # SHAP importance drives the glow intensity
                    joint_weight = self._shap_weights.get(i, 0.05)
                else:
                    # Legacy static weights (original implementation)
                    if i in [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:
                        joint_weight = 1.1   # key body joints
                    elif i in list(range(11)):
                        joint_weight = 0.2   # face landmarks
                    else:
                        joint_weight = 0.7   # rest

                self.heatmap[y_start:y_end, x_start:x_end] += (
                    kernel[ky_start:ky_end, kx_start:kx_end]
                    * movement_factor * joint_weight
                )

            self.prev_landmarks = landmarks

        return self.heatmap

    # ------------------------------------------------------------------
    # Overlay rendering
    # ------------------------------------------------------------------

    def apply_heatmap_overlay(self, frame):
        if not self.show_heatmap or self.heatmap is None:
            return frame.copy()

        frame_h, frame_w = frame.shape[:2]
        heatmap_h, heatmap_w = self.heatmap.shape[:2]

        if frame_h != heatmap_h or frame_w != heatmap_w:
            heatmap_display = cv2.resize(self.heatmap, (frame_w, frame_h))
        else:
            heatmap_display = self.heatmap.copy()

        heatmap_min = heatmap_display.min()
        heatmap_max = heatmap_display.max()

        if heatmap_max > heatmap_min:
            heatmap_display = (
                (heatmap_display - heatmap_min) / (heatmap_max - heatmap_min) * 255
            )
        else:
            heatmap_display = np.zeros_like(heatmap_display)

        heatmap_display = heatmap_display.astype(np.uint8)

        # Use INFERNO colormap for SHAP mode (purple→yellow = low→high importance)
        # Use classic JET for motion mode (blue→red = low→high movement)
        colormap = cv2.COLORMAP_INFERNO if self.mode == "shap" else cv2.COLORMAP_JET
        heatmap_color = cv2.applyColorMap(heatmap_display, colormap)

        if heatmap_color.shape != frame.shape:
            heatmap_color = cv2.resize(heatmap_color, (frame_w, frame_h))

        try:
            blended = cv2.addWeighted(frame, 0.7, heatmap_color, 0.5, 0)

            # ── SHAP mode: burn a small label onto the frame ──────────
            if self.mode == "shap":
                label = "SHAP Heatmap"
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale, thickness = 0.55, 1
                (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
                # Bottom-right corner
                tx = frame_w - tw - 10
                ty = frame_h - 10
                cv2.rectangle(blended,
                              (tx - 4, ty - th - 4),
                              (tx + tw + 4, ty + 4),
                              (0, 0, 0), -1)
                cv2.putText(blended, label, (tx, ty),
                            font, scale, (255, 215, 0), thickness,
                            cv2.LINE_AA)

            return blended

        except cv2.error as e:
            print(f"Heatmap overlay error: {e}")
            return frame.copy()

    # ------------------------------------------------------------------
    # Lifecycle helpers (called by Predict_main.py)
    # ------------------------------------------------------------------

    def reset(self):
        self.heatmap = None
        self.prev_landmarks = None
        # Keep SHAP weights if they were loaded — they still apply

    def toggle(self):
        self.show_heatmap = not self.show_heatmap
        return self.show_heatmap
