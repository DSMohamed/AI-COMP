# 🎮 Autonomous Commentary & Continuous Observation Loop

The Continuous Observer (`gaming_ai.agent.observer.ContinuousObserver`) is the central multimodal coordination engine. It runs non-blocking, decoupled async workers to monitor gameplay, evaluate events, observe player reactions, and provide natural autonomous commentary while respecting speech priority rules.

---

## 🏛️ Concurrent Worker Architecture (Section 34 & 35 Compliance)

```
                       ┌──────────────────────────────────────────────┐
                       │     ContinuousObserver (Async Orchestrator)  │
                       └──────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
         ▼                                    ▼                                    ▼
┌──────────────────┐                 ┌──────────────────┐                 ┌──────────────────┐
│ Voice Listener   │                 │ Screen Observer  │                 │ Webcam Observer  │
│ (Priority: HIGH) │                 │ (Interval: 2.0s) │                 │ (Interval: 4.0s) │
└────────┬─────────┘                 └────────┬─────────┘                 └────────┬─────────┘
         │ (Preempts Background Tasks)        │                                    │
         ▼                                    ▼                                    ▼
┌──────────────────┐                 ┌──────────────────┐                 ┌──────────────────┐
│ Mic + VAD + STT  │                 │ Frame Delta + VLM│                 │ Player Reaction  │
└────────┬─────────┘                 └────────┬─────────┘                 └────────┬─────────┘
         │                                    │                                    │
         └────────────────────────────────────┼────────────────────────────────────┘
                                              ▼
                                    [ Context Aggregator ]
                                              │
                                              ▼
                                    [ Decision Engine ]
                                              │
                                 (If Score >= Threshold)
                                              ▼
                                  [ Streaming LLM + TTS ]
```

---

## ⚡ 1. Priority Resolution & Preemption Rules

1. **User Direct Speech (Highest Priority)**:
   * When the user speaks into the microphone, `ContinuousObserver` immediately raises `_user_speaking_flag`.
   * Autonomous background screen and webcam commentary checks are paused.
   * If the companion was currently speaking, TTS is halted in $<20\text{ms}$.
   * The user's question or reaction is transcribed and answered first.
2. **Major Gameplay Events (High Priority)**:
   * Player deaths, boss encounters, and victories bypass normal cooldown timers ($>3.0\text{s}$) to react immediately.
3. **Minor / Routine Events (Lowest Priority)**:
   * Filtered out by the `DecisionEngine` attention threshold and dampened by cooldown timers.

---

## 🚀 2. Launching Full Companion Mode

Run the companion in full multimodal observation mode:
```bash
python -m gaming_ai.main --mode companion
```

### Dashboard Output:
```text
● MULTIMODAL COMPANION ACTIVE
👁️ Screen Watcher: Active | 🎤 Microphone: Active | 🧠 Brain: Ready
Play your game! The companion will watch, listen, and comment when interesting events occur.

⚔️ [EVENT: BOSS_ENCOUNTER (Score: 0.85)] Dragon boss health bar appeared.
🔊 Glitch: Oh great, a flying lizard. Don't tell me you forgot to bring fire resistance 😭
```
