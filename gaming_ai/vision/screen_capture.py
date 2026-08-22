"""High-performance Windows screen capture module with fallback handling."""

from __future__ import annotations

import base64
import io
import logging
import time
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("gaming_ai.vision.screen_capture")


class ScreenCapture:
    """Fast desktop screen grabber with resolution downscaling and fallback handling."""

    def __init__(
        self,
        target_resolution: Tuple[int, int] = (1280, 720),
        monitor_index: int = 1,
        jpeg_quality: int = 80,
        mock_frame: Optional[np.ndarray] = None,
    ) -> None:
        self.target_resolution = target_resolution
        self.monitor_index = monitor_index
        self.jpeg_quality = jpeg_quality
        self.mock_frame = mock_frame
        self._sct = None

    def _get_sct(self):
        """Lazy-initialize mss instance."""
        if self._sct is None:
            import mss
            if hasattr(mss, "MSS"):
                self._sct = mss.MSS()
            else:
                self._sct = mss.mss()
        return self._sct

    def capture_frame_numpy(self) -> np.ndarray:
        """
        Capture primary display as an RGB numpy array (H, W, 3).
        Falls back gracefully if running in a headless or locked session.
        """
        if self.mock_frame is not None:
            frame = self.mock_frame.copy()
            if self.target_resolution is not None:
                from PIL import Image
                img = Image.fromarray(frame)
                img = img.resize(self.target_resolution, Image.Resampling.BILINEAR)
                return np.array(img)
            return frame

        # Try mss capture
        try:
            sct = self._get_sct()
            monitors = sct.monitors
            target_mon = monitors[self.monitor_index] if len(monitors) > self.monitor_index else monitors[0]
            raw_shot = sct.grab(target_mon)
            # Convert BGRA to RGB
            frame = np.array(raw_shot, dtype=np.uint8)[:, :, :3]
            frame = frame[:, :, ::-1]

            if self.target_resolution is not None:
                from PIL import Image
                img = Image.fromarray(frame)
                img = img.resize(self.target_resolution, Image.Resampling.BILINEAR)
                frame = np.array(img)
            return frame

        except Exception as e:
            logger.warning("Native screen capture unavailable (desktop may be locked or headless): %s. Using fallback frame.", e)
            # Create a 720p fallback frame
            w, h = self.target_resolution if self.target_resolution else (1280, 720)
            fallback = np.zeros((h, w, 3), dtype=np.uint8)
            return fallback

    def capture_base64(self) -> str:
        """
        Capture desktop frame and encode as a compressed base64 JPEG string.
        """
        frame_rgb = self.capture_frame_numpy()
        from PIL import Image

        img = Image.fromarray(frame_rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=self.jpeg_quality)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return encoded

    def capture_jpeg_bytes(self) -> bytes:
        """Capture desktop frame and return compressed JPEG raw bytes."""
        frame_rgb = self.capture_frame_numpy()
        from PIL import Image

        img = Image.fromarray(frame_rgb)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=self.jpeg_quality)
        return buffer.getvalue()

    def close(self) -> None:
        """Release screen capture resources."""
        if self._sct is not None:
            try:
                self._sct.close()
            except Exception as e:
                logger.error("Error closing screen capture: %s", e)
            finally:
                self._sct = None
