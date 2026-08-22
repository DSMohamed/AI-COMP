# 🎯 Event Detection & Attention Engine

The Event Detection and Attention Engine is what prevents the AI companion from talking constantly or blurting out random noise. It observes gameplay events, classifies their severity, calculates an interestingness score, and respects dynamic speech cooldowns.

---

## 🏛️ Event Pipeline

```
[ Structured VLM Analysis ] + [ Frame Motion Delta ]
                         │
                         ▼
             [ EventDetector Engine ]
                         │
            (Classifies Event & Score)
     e.g., DEATH: 0.95 | BOSS: 0.85 | EXPLORATION: 0.20
                         │
                         ▼
              [ DecisionEngine ]
                         │
   ┌─────────────────────┴─────────────────────┐
   │ Score < Threshold or In Cooldown          │ Score >= Threshold & Cooldown Ready
   ▼                                           ▼
[ Ignore Event ]                     [ Trigger Autonomous Commentary ]
(Keep Quiet)                                   │
                                               ▼
                                   [ Speak via Streaming TTS ]
                                               │
                                               ▼
                                    [ Reset Speech Cooldown ]
```

---

## 📊 1. Attention Scoring Scale (Section 12 Compliance)

| Score Range | Classification | Action | Examples |
|---|---|---|---|
| **0.00 – 0.30** | Minor / Routine | **Ignore** | Navigating menus, inventory, standing still, loading screen |
| **0.30 – 0.60** | Low Interest | **Probably Ignore** | Normal movement, routine combat against basic trash mobs |
| **0.60 – 0.80** | Moderate Interest | **Consider Commenting** | Low health (HP $<20\%$), entering a new area, cutscenes |
| **0.80 – 1.00** | Major Event | **Strong Reason to Comment** | Boss fight encounter, boss defeat / victory, player death |

---

## ⚡ 2. Decision Engine & Speech Cooldowns (`gaming_ai.agent.decision`)

* **Dynamic Threshold Adjustment**:
  The threshold is dynamically shifted by the user's `personality.talkativeness` setting ($0 - 100$):
  $$\text{Threshold} = 0.70 - \left(\frac{\text{Talkativeness} - 50}{250}\right)$$
  * Talkativeness = 100 $\implies$ Threshold $\sim 0.50$ (talks frequently)
  * Talkativeness = 0 $\implies$ Threshold $\sim 0.90$ (speaks only on deaths/victories)
* **Speech Cooldowns**:
  Autonomous comments are constrained by `min_speech_interval` (default: 8.0 seconds) to prevent talking over gameplay.
* **User Interruption Override**:
  When the player speaks into the microphone, all autonomous cooldowns are bypassed immediately.
