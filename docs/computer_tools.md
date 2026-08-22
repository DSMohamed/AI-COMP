# 🛠️ Sandboxed Computer Control Tools & Action Logging

The AI Companion includes an opt-in, safe-by-default Computer Control Tool Framework (`gaming_ai.tools`). It allows the companion to take screenshots, set game timers, open wiki guides, and adjust volume while strictly blocking destructive actions.

---

## 🔒 Privilege & Safety Guardrails (Section 27–29 Compliance)

1. **Sandboxed & Opt-In**:
   * Tools are enabled/disabled via `config.yaml` (`tools.enabled: true`).
   * Privileged actions require explicit elevation (`tools.allow_privileged: true`).
2. **Restricted Operations**:
   * **Zero File Destruction**: No arbitrary shell command execution, file deletion, or registry modifications.
   * **Network Validation**: `BrowserGuideTool` restricts URLs to validated `http://` / `https://` schemas and blocks local loopback probes (`127.0.0.1`, `localhost`).
3. **Immutable Audit Logging**:
   * Every single tool execution records timestamp, parameters, outcome, and execution latency.

---

## 🧩 Built-in Tools

| Tool Name | Class | Description | Confirmation Required |
|---|---|---|---|
| `take_screenshot` | [`ScreenshotTool`](file:///e:/MohamedWorks/AI/gaming_ai/tools/builtin.py) | Captures active gaming display and saves PNG locally. | No |
| `set_timer` | [`TimerTool`](file:///e:/MohamedWorks/AI/gaming_ai/tools/builtin.py) | Non-blocking countdown timer for boss respawns and cooldowns. | No |
| `open_guide` | [`BrowserGuideTool`](file:///e:/MohamedWorks/AI/gaming_ai/tools/builtin.py) | Opens verified wiki URLs safely in the default browser. | No |
| `set_volume` | [`VolumeControlTool`](file:///e:/MohamedWorks/AI/gaming_ai/tools/builtin.py) | Reads or adjusts companion playback volume (0–100%). | No |
| `read_clipboard` | [`ClipboardTool`](file:///e:/MohamedWorks/AI/gaming_ai/tools/builtin.py) | Reads plain text from clipboard (e.g. game codes/coordinates). | No |

---

## 🎙️ Natural Voice Triggering

You can trigger tools conversationally during gameplay:
* *"Take a screenshot!"* $\implies$ Companion captures and saves screen.
* *"Set a timer for 5 minutes"* $\implies$ Companion starts background alert.
* *"Turn the volume down to 50"* $\implies$ Companion adjusts audio volume.
