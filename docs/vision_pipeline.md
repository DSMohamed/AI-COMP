# 👁️ Vision & Screen Perception Pipeline

The vision pipeline enables the AI gaming companion to observe the gameplay screen, parse HUD elements, track game scenes, and answer visual questions with minimal GPU overhead.

---

## 🏛️ Vision Architecture

```
[ Game Screen ] ──(1280x720)──► [ ScreenCapture (mss/PIL) ]
                                          │
                                   (RGB Numpy Array)
                                          │
                                          ▼
                                 [ FrameAnalyzer ]
                                 (Lightweight Delta)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  │ (Delta < Threshold)                           │ (Delta >= Threshold or Visual Query)
                  ▼                                               ▼
         [ Skip Inference ]                              [ Base64 JPEG Compression ]
         (Zero GPU / VRAM cost)                                   │
                                                                  ▼
                                                      [ Ollama VLM (llava / qwen2-vl) ]
                                                                  │
                                                      (Structured Scene JSON)
                                                                  │
                                                                  ▼
                                                      [ Context Aggregator ]
```

---

## 📸 1. Screen Capture (`gaming_ai.vision.screen_capture`)

* **Capture Engine**: `mss` with graceful fallback to `PIL.ImageGrab`.
* **Resolution Scaling**: Downscales native 1440p / 4K displays to **1280x720** (or 960x540) to preserve memory and minimize VLM latency.
* **JPEG Compression**: Compresses captured frames to quality 80 (~120 KB payload) before sending over HTTP.
* **Latency**: $< 15\text{ms}$ per frame capture.

---

## ⚡ 2. Cheap Frame Differencing (`gaming_ai.vision.frame_analyzer`)

Sending every frame to a Vision-Language Model at 60 FPS would cause extreme VRAM and GPU exhaustion. `FrameAnalyzer` eliminates redundant inferences:

1. Downsamples each frame to $160 \times 90$ grayscale.
2. Computes the pixel-wise absolute difference $\text{diff} = |\text{Frame}_t - \text{Frame}_{t-1}|$.
3. If the delta is below `change_threshold` (default: 12%), VLM inference is skipped.
4. **Execution Time**: $< 1\text{ms}$ on CPU.

---

## 🧠 3. Structured Vision-Language Model (`gaming_ai.vision.vision_model`)

Supports local models via Ollama (`llava:latest`, `qwen2-vl:2b`, `moondream2`):
* **Structured Output Schema**:
  ```json
  {
    "scene": "boss_fight",
    "important_event": true,
    "player_state": "low_health",
    "summary": "Player is dodging a massive boss swing with 15% HP remaining."
  }
  ```
* **Interactive Visual Queries**:
  When the player asks *"What is happening on my screen?"* or *"Look at this"*, the agent captures the screen and integrates the visual perception directly into the companion's response.
