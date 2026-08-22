# 🎮 Desktop Companion Dashboard UI

The AI Companion includes a modern, high-performance dark-mode Web Dashboard featuring glassmorphism visuals, real-time WebSocket state synchronization, live hardware sensor badges, and dynamic personality sliders.

---

## 🏛️ UI Architecture (Section 31 & 32 Compliance)

```
[ Gaming Companion Agent ] ──► [ DashboardState (Observable) ]
                                            │
                                            ▼
                               [ FastAPI Server (Port 8080) ]
                                            │
                                  (WebSocket Broadcast)
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │      HTML5 / CSS3 Glassmorphism Dashboard     │
                    ├──────────────────────┬────────────────────────┤
                    │ • Sensor Status Bar  │ • Live Transcript Feed │
                    │ • Telemetry Grid     │ • Personality Sliders  │
                    │ • VRAM RTX 3070 MB   │ • Privacy Controls     │
                    └──────────────────────┴────────────────────────┘
```

---

## 🚀 Launching the Dashboard

Run the companion in GUI / dashboard mode:
```bash
python -m gaming_ai.main --mode gui --port 8080
```
Open **[http://127.0.0.1:8080](http://127.0.0.1:8080)** in your browser or secondary gaming monitor!

---

## 🧩 Key Dashboard Capabilities

1. **Live Sensor Indicator Bar**:
   * `🎤 MIC: LISTENING` (Green) / `MUTED` (Red)
   * `📷 CAMERA: ON` (Green) / `OFF` (Red)
   * `🖥️ SCREEN: ACTIVE` (Cyan) / `PAUSED` (Amber)
   * `🧠 AI: THINKING` (Amber) / `IDLE` (Green)
   * `🔊 VOICE: SPEAKING` (Cyan) / `SILENT` (Green)

2. **Real-Time Transcript Feed**:
   * Color-coded chat bubbles with speaker icons (`🎤 Player`, `🤖 Glitch`, `⚔️ Game Event`).
   * Sub-millisecond latency counters for Speech-to-Text and LLM generation.

3. **Live Personality Sliders**:
   * Dynamically adjust **Sarcasm**, **Humor**, **Energy**, and **Talkativeness** with immediate zero-reload backend sync.

4. **One-Click Privacy & Memory Tools**:
   * *Toggle Camera* / *Mute Mic* / *Clear Session Memory*.
