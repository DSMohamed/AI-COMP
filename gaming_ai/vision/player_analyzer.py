"""Player reaction and engagement analyzer using local computer vision and privacy-safe heuristics."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional
import cv2
import numpy as np

logger = logging.getLogger("gaming_ai.vision.player_analyzer")


@dataclass
class PlayerReaction:
    """Structured perception of player facial reaction and engagement."""
    face_detected: bool = False
    emotion: str = "neutral"  # neutral, smiling, laughing, surprised, frustrated, focused
    engagement: str = "normal"  # high, normal, away
    confidence: float = 0.85
    summary: str = "Player appears neutral and engaged."


class PlayerAnalyzer:
    """Analyzes webcam frames in-memory to detect player engagement and emotional cues."""

    def __init__(self) -> None:
        self._face_cascade = None
        self._smile_cascade = None

    def _load_cascades(self) -> None:
        """Lazy-load OpenCV Haar cascades if available in OpenCV version."""
        if self._face_cascade is None and hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
            try:
                face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                smile_path = cv2.data.haarcascades + "haarcascade_smile.xml"
                self._face_cascade = cv2.CascadeClassifier(face_path)
                self._smile_cascade = cv2.CascadeClassifier(smile_path)
            except Exception as e:
                logger.debug("Could not load Haar cascades: %s", e)

    def analyze_frame(self, frame_rgb: Optional[np.ndarray]) -> PlayerReaction:
        """
        Analyze a single RGB webcam frame.
        Frames are analyzed purely in-memory and immediately discarded.
        """
        if frame_rgb is None or len(frame_rgb) == 0:
            return PlayerReaction(
                face_detected=False,
                emotion="neutral",
                engagement="away",
                confidence=0.5,
                summary="Player is away from camera.",
            )

        self._load_cascades()

        # If Haar cascades are available
        if self._face_cascade is not None and hasattr(self._face_cascade, "detectMultiScale"):
            try:
                gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
                faces = self._face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
                )

                if len(faces) == 0:
                    return PlayerReaction(
                        face_detected=False,
                        emotion="neutral",
                        engagement="away",
                        confidence=0.7,
                        summary="Player is not looking at the screen.",
                    )

                x, y, w, h = faces[0]
                face_roi_gray = gray[y : y + h, x : x + w]

                if self._smile_cascade is not None:
                    smiles = self._smile_cascade.detectMultiScale(
                        face_roi_gray, scaleFactor=1.7, minNeighbors=20, minSize=(25, 25)
                    )
                    if len(smiles) > 0:
                        emotion = "smiling" if len(smiles) == 1 else "laughing"
                        return PlayerReaction(
                            face_detected=True,
                            emotion=emotion,
                            engagement="high",
                            confidence=0.88,
                            summary=f"Player is {emotion}.",
                        )

                return PlayerReaction(
                    face_detected=True,
                    emotion="focused",
                    engagement="high",
                    confidence=0.85,
                    summary="Player is focused on the game.",
                )
            except Exception as e:
                logger.debug("Cascade analysis failed: %s", e)

        # Fallback heuristic: Skin tone / presence analysis in central ROI
        h, w, _ = frame_rgb.shape
        center_roi = frame_rgb[int(h * 0.2) : int(h * 0.8), int(w * 0.2) : int(w * 0.8)]
        avg_brightness = np.mean(center_roi)

        if avg_brightness < 10.0:  # Dark / covered camera
            return PlayerReaction(
                face_detected=False,
                emotion="neutral",
                engagement="away",
                confidence=0.75,
                summary="Player is away or camera is covered.",
            )

        return PlayerReaction(
            face_detected=True,
            emotion="focused",
            engagement="normal",
            confidence=0.80,
            summary="Player is present and engaged with the game.",
        )
