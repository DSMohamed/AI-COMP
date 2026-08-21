"""Main command-line interface for the Local AI Gaming Companion."""

from __future__ import annotations

import argparse
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig, get_config
from gaming_ai.app.logging import log_event, setup_logging

console = Console()


def print_banner(config: AppConfig) -> None:
    """Render startup dashboard banner."""
    header = f"""[bold magenta]🎮 LOCAL AI GAMING COMPANION (Phase 1 — Voice)[/bold magenta]
[cyan]Companion Name:[/cyan] {config.personality.name} | [cyan]LLM Model:[/cyan] {config.ai.model} | [cyan]STT:[/cyan] {config.speech.stt_model}
[cyan]Personality:[/cyan] Sarcasm: {config.personality.sarcasm}% | Humor: {config.personality.humor}% | Energy: {config.personality.energy}%
[green]Target GPU:[/green] NVIDIA RTX 3070 8GB | [green]Privacy:[/green] 100% Local (Zero Cloud)"""
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


def main() -> None:
    """Application CLI entry point."""
    parser = argparse.ArgumentParser(description="Local AI Gaming Companion")
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="text",
        help="Interaction mode: 'voice' (microphone) or 'text' (console interactive)",
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
        if args.mode == "voice":
            asyncio.run(run_voice_mode(agent))
        else:
            asyncio.run(run_text_mode(agent))
    except KeyboardInterrupt:
        console.print("\n[yellow]Companion shut down cleanly. GG![/yellow]")


if __name__ == "__main__":
    main()
