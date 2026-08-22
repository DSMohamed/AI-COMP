# 📷 Webcam & Player Reaction Pipeline

The webcam subsystem provides optional, privacy-respecting perception of the player's presence, engagement level, and emotional reactions (smiling, laughing, frustration, surprise) to make the AI companion feel genuinely present during gameplay.

---

## 🔒 Strict Privacy Safeguards (Section 10 Compliance)

1. **100% In-Memory Processing**: Frames exist temporarily in RAM while being analyzed, and are immediately garbage-collected.
2. **Zero Disk Storage**: Frames and camera video streams are **NEVER** saved to disk or uploaded to any cloud service.
3. **No Profiling or Medical Diagnosis**: The engine is strictly bounded to lightweight gaming engagement cues (e.g. smiling, focused, away) and never attempts sensitive demographic profiling.
4. **Explicit Status Indicators**: The UI clearly displays `📷 CAMERA: ON` when active and `📷 CAMERA: OFF` when disabled.

---

## 🏛️ Architecture

```
[ Webcam Device ] ──(640x480 RGB)──► [ WebcamCapture (OpenCV) ]
                                              │
                                       (In-Memory Frame)
                                              │
                                              ▼
                                     [ PlayerAnalyzer ]
                                (Face & Reaction Classifier)
                                              │
                                              ▼
                                      [ PlayerReaction ]
                          (emotion: "laughing", engagement: "high")
                                              │
                                              ▼
                                   [ Context Aggregator ]
                                              │
                                              ▼
                                     [ Companion Brain ]
              ("Why are you laughing so hard? Did you see that whiff?! 😭")
```

---

## 🧩 Components

### 1. Webcam Capture (`gaming_ai.vision.webcam.WebcamCapture`)
* High-speed Windows DirectShow capture backend.
* Low CPU footprint with downscaling to $640 \times 480$ or $320 \times 240$.
* Graceful fallback if no webcam is connected.

### 2. Player Reaction Analyzer (`gaming_ai.vision.player_analyzer.PlayerAnalyzer`)
* Detects player presence, face geometry, and smile/laughter activation.
* **Structured Output (`PlayerReaction`)**:
  ```python
  @dataclass
  class PlayerReaction:
      face_detected: bool = True
      emotion: str = "laughing"  # neutral, smiling, laughing, surprised, focused
      engagement: str = "high"   # high, normal, away
      confidence: float = 0.88
      summary: str = "Player is laughing."
  ```

---

## ⚙️ Configuration

In your `config.yaml`:
```yaml
vision:
  webcam_enabled: true                # Enable or disable camera observation
  capture_fps: 1                      # Polling frequency (1 frame / second)

privacy:
  save_webcam_frames: false           # Guaranteed false (zero disk persistence)
```
