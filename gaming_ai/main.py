"""Main command-line interface for the Local AI Gaming Companion."""

from __future__ import annotations

import argparse
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.agent.observer import ContinuousObserver
from gaming_ai.app.config import AppConfig, get_config
from gaming_ai.app.logging import log_event, setup_logging
from gaming_ai.vision.event_detector import GameEvent

console = Console()


def print_banner(config: AppConfig) -> None:
    """Render startup dashboard banner."""
    header = f"""[bold magenta]🎮 LOCAL AI GAMING COMPANION (Multimodal AI Companion)[/bold magenta]
[cyan]Companion Name:[/cyan] {config.personality.name} | [cyan]LLM Model:[/cyan] {config.ai.model} | [cyan]STT:[/cyan] {config.speech.stt_model}
[cyan]Personality:[/cyan] Sarcasm: {config.personality.sarcasm}% | Humor: {config.personality.humor}% | Energy: {config.personality.energy}% | Talkativeness: {config.personality.talkativeness}%
[green]Target GPU:[/green] NVIDIA RTX 3070 8GB | [green]Privacy:[/green] 100% Local (In-Memory Processing)"""
    console.print(Panel(header, border_style="bright_blue"))


async def run_text_mode(agent: GamingCompanionAgent) -> None:
    """Interactive text chat test mode."""
    console.print("[bold yellow]Running in Text Simulation Mode. Type 'exit' to quit.[/bold yellow]\n")
    while True:
        try:
            user_input = Prompt.ask("[bold green]Player[/bold green]")
            if not user_input or user_input.strip().lower() in ("exit", "quit"):
                break

            console.print(f"[bold magenta]{agent.config.personality.name}:[/bold magenta] ", end="")
            response = await agent.respond_to_text(user_input, speak=True)
            console.print(f"[italic]{response}[/italic]\n")
        except (KeyboardInterrupt, EOFError):
            break


async def run_voice_mode(agent: GamingCompanionAgent) -> None:
    """Live interactive voice mode with microphone and interruption."""
    console.print("[bold green]● Microphone ACTIVE. Start speaking naturally![/bold green]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    def on_stt(text: str, latency: float) -> None:
        console.print(f"\n[bold green]🎤 You:[/bold green] {text} [dim]({latency:.0f}ms)[/dim]")

    def on_reply(text: str) -> None:
        console.print(f"[bold magenta]🔊 {agent.config.personality.name}:[/bold magenta] {text}\n")

    await agent.run_voice_loop(on_transcription=on_stt, on_response=on_reply)


async def run_companion_mode(agent: GamingCompanionAgent) -> None:
    """Full multimodal continuous observation mode (Voice + Screen + Webcam + Autonomous Commentary)."""
    console.print("[bold green]● MULTIMODAL COMPANION ACTIVE[/bold green]")
    console.print("[cyan]👁️ Screen Watcher:[/cyan] Active | [cyan]🎤 Microphone:[/cyan] Active | [cyan]🧠 Brain:[/cyan] Ready")
    console.print("[dim]Play your game! The companion will watch, listen, and comment when interesting events occur. Press Ctrl+C to exit.[/dim]\n")

    def on_stt(text: str, latency: float) -> None:
        console.print(f"\n[bold green]🎤 You:[/bold green] {text} [dim]({latency:.0f}ms)[/dim]")

    def on_reply(text: str) -> None:
        console.print(f"[bold magenta]🔊 {agent.config.personality.name}:[/bold magenta] {text}\n")

    def on_game_event(event: GameEvent) -> None:
        console.print(f"[bold yellow]⚔️ [EVENT: {event.event_type.value.upper()} (Score: {event.interestingness:.2f})][/bold yellow] [dim]{event.description}[/dim]")

    observer = ContinuousObserver(
        agent=agent,
        screen_interval=2.0,
        webcam_interval=4.0,
        on_event_detected=on_game_event,
    )

    try:
        await observer.start(on_transcription=on_stt, on_response=on_reply)
    finally:
        await observer.stop()


def main() -> None:
    """Application CLI entry point."""
    parser = argparse.ArgumentParser(description="Local AI Gaming Companion")
    parser.add_argument(
        "--mode",
        choices=["companion", "voice", "text"],
        default="companion",
        help="Interaction mode: 'companion' (full multimodal), 'voice' (microphone only), or 'text' (console)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file",
    )
    args = parser.parse_args()

    setup_logging()
    config = get_config(args.config)
    print_banner(config)

    agent = GamingCompanionAgent(config=config)

    try:
        if args.mode == "companion":
            asyncio.run(run_companion_mode(agent))
        elif args.mode == "voice":
            asyncio.run(run_voice_mode(agent))
        else:
            asyncio.run(run_text_mode(agent))
    except KeyboardInterrupt:
        console.print("\n[yellow]Companion shut down cleanly. GG![/yellow]")


if __name__ == "__main__":
    main()
