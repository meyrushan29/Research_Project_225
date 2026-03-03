"""
Unit tests for SHAP-Weighted HeatmapVisualizer.

Run from Final_Backend/ with:
    python -m pytest tests/test_shap_heatmap.py -v
"""
import sys
import types
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Minimal landmark stub – avoids importing mediapipe in this unit test
# ---------------------------------------------------------------------------
class _FakeLandmark:
    def __init__(self, x, y, z=0.0, visibility=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


def _make_landmarks(n=33, seed=42):
    rng = np.random.default_rng(seed)
    coords = rng.uniform(0.1, 0.9, size=(n, 2))
    return [_FakeLandmark(float(x), float(y)) for x, y in coords]


# ---------------------------------------------------------------------------
# Import the module under test (relative path trick)
# ---------------------------------------------------------------------------
import importlib, pathlib, types as _types

_fitness_dir = pathlib.Path(__file__).parent.parent / "fitness"
sys.path.insert(0, str(_fitness_dir))

from heatmap import HeatmapVisualizer   # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
FRAME_SHAPE = (480, 640, 3)
_DUMMY_FRAME = np.zeros(FRAME_SHAPE, dtype=np.uint8)


def _run_frames(viz, landmarks, n=5):
    """Push *n* frames through the visualizer and return the final heatmap."""
    for _ in range(n):
        viz.update_heatmap(landmarks, FRAME_SHAPE)
    return viz.heatmap


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMotionMode:
    def test_heatmap_initialises_on_first_frame(self):
        viz = HeatmapVisualizer()
        lm = _make_landmarks()
        _run_frames(viz, lm, n=1)
        assert viz.heatmap is not None
        assert viz.heatmap.shape == (480, 640)

    def test_heatmap_nonzero_after_frames(self):
        viz = HeatmapVisualizer()
        lm = _make_landmarks()
        _run_frames(viz, lm, n=3)
        assert viz.heatmap.max() > 0, "Heatmap should be non-zero after landmark updates"

    def test_mode_default_is_motion(self):
        viz = HeatmapVisualizer()
        assert viz.mode == "motion"

    def test_toggle(self):
        viz = HeatmapVisualizer()
        assert viz.show_heatmap is True
        viz.toggle()
        assert viz.show_heatmap is False
        viz.toggle()
        assert viz.show_heatmap is True

    def test_reset_clears_heatmap(self):
        viz = HeatmapVisualizer()
        _run_frames(viz, _make_landmarks(), n=3)
        viz.reset()
        assert viz.heatmap is None
        assert viz.prev_landmarks is None


class TestSHAPMode:
    def test_mode_switches_to_shap_after_weights_set(self):
        viz = HeatmapVisualizer()
        viz.update_shap_weights({"Right Elbow": 1.0, "Left Elbow": 0.8})
        assert viz.mode == "shap"

    def test_shap_weights_ignored_for_unknown_names(self):
        viz = HeatmapVisualizer()
        viz.update_shap_weights({"NonexistentJoint": 1.0})
        # Should not switch to shap mode (no valid indices found)
        assert viz.mode == "motion"

    def test_high_shap_joints_brighter_than_low_shap_joints(self):
        """
        Elbow joints (indices 13, 14) get high SHAP weight (1.0).
        Face landmarks (indices 0-10) get very low weight (0.05 as fallback).
        After running frames, pixels near elbow positions should be brighter
        than pixels near face positions.
        """
        viz = HeatmapVisualizer()

        # Set high SHAP weight only on elbows
        viz.update_shap_weights({
            "Left Elbow": 1.0,
            "Right Elbow": 1.0,
        })
        assert viz.mode == "shap"

        # Use deterministic landmarks: place elbows at fixed positions
        landmarks = _make_landmarks(33)

        # Override elbows (idx 13, 14) to a corner well away from face (idx 0)
        landmarks[13] = _FakeLandmark(0.8, 0.8)  # Left Elbow  → bottom-right
        landmarks[14] = _FakeLandmark(0.8, 0.9)  # Right Elbow → bottom-right
        landmarks[0]  = _FakeLandmark(0.1, 0.1)  # Nose        → top-left

        _run_frames(viz, landmarks, n=8)

        h, w = FRAME_SHAPE[:2]

        # Sample brightness near elbow region (bottom-right)
        elbow_patch = viz.heatmap[
            int(0.75 * h) : int(0.95 * h),
            int(0.75 * w) : int(0.95 * w)
        ]
        # Sample brightness near face/nose region (top-left)
        face_patch = viz.heatmap[
            int(0.05 * h) : int(0.20 * h),
            int(0.05 * w) : int(0.20 * w)
        ]

        assert elbow_patch.mean() > face_patch.mean(), (
            f"Elbow (SHAP=1.0) mean={elbow_patch.mean():.4f} should be "
            f"greater than face (SHAP=fallback) mean={face_patch.mean():.4f}"
        )

    def test_reset_shap_weights_reverts_to_motion(self):
        viz = HeatmapVisualizer()
        viz.update_shap_weights({"Right Elbow": 1.0})
        assert viz.mode == "shap"
        viz.reset_shap_weights()
        assert viz.mode == "motion"

    def test_overlay_returns_frame_same_shape(self):
        viz = HeatmapVisualizer()
        viz.update_shap_weights({"Right Elbow": 1.0, "Left Elbow": 0.9})
        _run_frames(viz, _make_landmarks(), n=4)
        out = viz.apply_heatmap_overlay(_DUMMY_FRAME.copy())
        assert out.shape == FRAME_SHAPE, "Overlay output shape must match input frame shape"

    def test_overlay_returns_copy_when_heatmap_disabled(self):
        viz = HeatmapVisualizer()
        viz.show_heatmap = False
        out = viz.apply_heatmap_overlay(_DUMMY_FRAME.copy())
        assert out.shape == FRAME_SHAPE

    def test_normalisation_caps_minimum_at_0_1(self):
        """All joints should get at least 0.1 weight after normalisation."""
        viz = HeatmapVisualizer()
        joint_importance = {
            "Right Elbow": 100.0,
            "Left Elbow": 50.0,
            "Nose": 0.0,   # should be clamped to 0.1
        }
        viz.update_shap_weights(joint_importance)
        # Nose → idx 0; its normalised weight should be ≥ 0.1
        assert viz._shap_weights.get(0, 0) >= 0.1
