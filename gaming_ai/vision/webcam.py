"""Local webcam capture with privacy safeguards and graceful degradation."""

from __future__ import annotations

import base64
import io
import logging
from typing import Optional, Tuple
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

logger = logging.getLogger("gaming_ai.vision.webcam")


class WebcamCapture:
    """Local-first, in-memory webcam frame grabber."""

    def __init__(
        self,
        device_index: int = 0,
        target_resolution: Tuple[int, int] = (640, 480),
        jpeg_quality: int = 75,
        mock_frame: Optional[np.ndarray] = None,
    ) -> None:
        self.device_index = device_index
        self.target_resolution = target_resolution
        self.jpeg_quality = jpeg_quality
        self.mock_frame = mock_frame
        self._cap = None
        self._is_active: bool = False

    def is_available(self) -> bool:
        """Check if webcam device is connected and accessible."""
        if self.mock_frame is not None:
            return True
        if not HAS_CV2:
            return False
        try:
            temp_cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if not temp_cap.isOpened():
                temp_cap = cv2.VideoCapture(self.device_index)
            is_open = temp_cap.isOpened()
            temp_cap.release()
            return is_open
        except Exception as e:
            logger.debug("Webcam availability check failed: %s", e)
            return False

    def start(self) -> bool:
        """Initialize camera stream."""
        if self.mock_frame is not None:
            self._is_active = True
            return True

        if self._cap is not None and self._cap.isOpened():
            self._is_active = True
            return True

        try:
            # Try DirectShow backend on Windows first for fast startup
            self._cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                self._cap = cv2.VideoCapture(self.device_index)

            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_resolution[0])
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_resolution[1])
                self._is_active = True
                logger.info("📷 CAMERA: ON (Device index: %d)", self.device_index)
                return True
            else:
                logger.warning("Camera unavailable. Continuing without webcam.")
                self._is_active = False
                return False
        except Exception as e:
            logger.warning("Failed to open webcam: %s. Continuing without webcam.", e)
            self._is_active = False
            return False

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame as an RGB numpy array (H, W, 3).
        Frames exist strictly in RAM and are never persisted to disk.
        """
        if self.mock_frame is not None:
            frame = self.mock_frame.copy()
            if self.target_resolution is not None:
                img = Image.fromarray(frame)
                img = img.resize(self.target_resolution, Image.Resampling.BILINEAR)
                return np.array(img)
            return frame

        if self._cap is None or not self._cap.isOpened():
            if not self.start():
                return None

        ret, bgr_frame = self._cap.read()
        if not ret or bgr_frame is None:
            return None

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)

        if self.target_resolution is not None:
            img = Image.fromarray(rgb_frame)
            img = img.resize(self.target_resolution, Image.Resampling.BILINEAR)
            rgb_frame = np.array(img)

        return rgb_frame

    def capture_base64(self) -> Optional[str]:
        """Capture frame and encode as a compressed base64 JPEG."""
        frame_rgb = self.capture_frame()
        if frame_rgb is None:
            return None

        img = Image.fromarray(frame_rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=self.jpeg_quality)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def stop(self) -> None:
        """Release camera and turn off sensor."""
        self._is_active = False
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception as e:
                logger.error("Error releasing webcam: %s", e)
            finally:
                self._cap = None
        logger.info("📷 CAMERA: OFF")

    @property
    def is_active(self) -> bool:
        return self._is_active
