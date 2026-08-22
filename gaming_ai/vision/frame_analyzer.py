"""Fast, lightweight frame differencing to eliminate redundant VLM inferences."""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("gaming_ai.vision.frame_analyzer")


class FrameAnalyzer:
    """Calculates visual delta between consecutive game frames."""

    def __init__(
        self,
        change_threshold: float = 0.12,
        downscale_dim: Tuple[int, int] = (160, 90),
    ) -> None:
        self.change_threshold = change_threshold
        self.downscale_dim = downscale_dim
        self._prev_small_gray: Optional[np.ndarray] = None

    def compute_difference(self, current_frame_rgb: np.ndarray) -> float:
        """
        Compute visual delta (0.0 to 1.0) between current and previous frame.
        """
        if current_frame_rgb is None or len(current_frame_rgb) == 0:
            return 0.0

        # Convert to small grayscale for ultra-fast delta calculation (<1ms)
        gray = cv2.cvtColor(current_frame_rgb, cv2.COLOR_RGB2GRAY)
        small_gray = cv2.resize(gray, self.downscale_dim, interpolation=cv2.INTER_AREA)

        if self._prev_small_gray is None:
            self._prev_small_gray = small_gray
            return 1.0  # Initial frame is considered 100% new

        # Compute absolute difference
        diff = cv2.absdiff(small_gray, self._prev_small_gray)
        # Ratio of pixels with significant change (> 25 pixel intensity)
        change_mask = diff > 25
        change_ratio = float(np.sum(change_mask) / change_mask.size)

        self._prev_small_gray = small_gray
        return change_ratio

    def has_significant_change(self, current_frame_rgb: np.ndarray) -> Tuple[bool, float]:
        """
        Determine if the visual change exceeds the threshold.

        Returns:
            Tuple of (has_changed, change_ratio)
        """
        delta = self.compute_difference(current_frame_rgb)
        is_significant = delta >= self.change_threshold
        return is_significant, delta

    def reset(self) -> None:
        """Reset previous frame reference."""
        self._prev_small_gray = None
