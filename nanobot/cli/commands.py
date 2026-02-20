"""CLI commands for nanobot - simplified version."""

import asyncio
import os
import signal
from pathlib import Path
import select
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

from nanobot import __version__, __logo__
from nanobot.config.schema import Config

app = typer.Typer(
    name="nanobot",
    help=f"{__logo__} nanobot - Personal AI Assistant",
    no_args_is_help=True,
)

console = Console()
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q"}

# ---------------------------------------------------------------------------
# CLI input: prompt_toolkit for editing, paste, history, and display
# ---------------------------------------------------------------------------

_PROMPT_SESSION: PromptSession | None = None
_SAVED_TERM_ATTRS = None


def _flush_pending_tty_input() -> None:
    """Drop unread keypresses typed while the model was generating output."""
    try:
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return
    except Exception:
        return

    try:
        import termios
        termios.tcflush(fd, termios.TCIFLUSH)
        return
    except Exception:
        pass

    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0)
            if not ready:
                break
            if not os.read(fd, 4096):
                break
    except Exception:
        return


def _restore_terminal() -> None:
    """Restore terminal to its original state."""
    if _SAVED_TERM_ATTRS is None:
        return
    try:
        import termios
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _SAVED_TERM_ATTRS)
    except Exception:
        pass


def _init_prompt_session() -> None:
    """Create the prompt_toolkit session with persistent file history."""
    global _PROMPT_SESSION, _SAVED_TERM_ATTRS

    try:
        import termios
        _SAVED_TERM_ATTRS = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        pass

    history_file = Path.home() / ".nanobot" / "history" / "cli_history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    _PROMPT_SESSION = PromptSession(
        history=FileHistory(str(history_file)),
        enable_open_in_editor=False,
        multiline=False,
    )


def _print_agent_response(response: str, render_markdown: bool) -> None:
    """Render assistant response."""
    content = response or ""
    body = Markdown(content) if render_markdown else Text(content)
    console.print()
    console.print(f"[cyan]{__logo__} nanobot[/cyan]")
    console.print(body)
    console.print()


def _is_exit_command(command: str) -> bool:
    """Return True when input should end interactive chat."""
    return command.lower() in EXIT_COMMANDS


async def _read_interactive_input_async() -> str:
    """Read user input using prompt_toolkit."""
    if _PROMPT_SESSION is None:
        raise RuntimeError("Call _init_prompt_session() first")
    try:
        with patch_stdout():
            return await _PROMPT_SESSION.prompt_async(
                HTML("<b fg='ansiblue'>You:</b> "),
            )
    except EOFError as exc:
        raise KeyboardInterrupt from exc


def version_callback(value: bool):
    if value:
        console.print(f"{__logo__} nanobot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    """nanobot - Personal AI Assistant."""
    pass


# ============================================================================
# Onboard / Setup
# ============================================================================


@app.command()
def onboard():
    """Initialize nanobot configuration and workspace."""
    from nanobot.config.loader import get_config_path, load_config, save_config
    from nanobot.utils.helpers import get_workspace_path

    config_path = get_config_path()

    if config_path.exists():
        console.print(f"[yellow]Config already exists at {config_path}[/yellow]")
        console.print("  [bold]y[/bold] = overwrite with defaults")
        console.print("  [bold]N[/bold] = refresh config, keeping existing values")
        if typer.confirm("Overwrite?"):
            config = Config()
            save_config(config)
            console.print(f"[green]✓[/green] Config reset to defaults at {config_path}")
        else:
            config = load_config()
            save_config(config)
            console.print(f"[green]✓[/green] Config refreshed at {config_path}")
    else:
        save_config(Config())
        console.print(f"[green]✓[/green] Created config at {config_path}")

    workspace = get_workspace_path()

    if not workspace.exists():
        workspace.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created workspace at {workspace}")

    _create_workspace_templates(workspace)

    console.print(f"\n{__logo__} nanobot is ready!")
    console.print("\nNext steps:")
    console.print("  1. Add your API key to [cyan]~/.nanobot/config.json[/cyan]")
    console.print("     Get one at: https://openrouter.ai/keys")
    console.print("  2. Chat: [cyan]nanobot agent -m \"Hello!\"[/cyan]")


def _create_workspace_templates(workspace: Path) -> None:
    """Create template files in workspace."""
    skills_dir = workspace / "skills"
    skills_dir.mkdir(exist_ok=True)

    readme = skills_dir / "README.md"
    if not readme.exists():
        readme.write_text("""# Skills

Place your custom skills in this directory.

Each skill should be in its own folder with a `SKILL.md` file.

## Example

```
my-skill/
  SKILL.md
```

## SKILL.md Format

```markdown
---
name: My Skill
description: What this skill does
---

# Skill Instructions

Your custom instructions here...
```
""")


# ============================================================================
# Provider Helper
# ============================================================================


def _make_provider(config: Config, model: str | None = None):
    """Create LLM provider from config."""
    from nanobot.providers.litellm_provider import LiteLLMProvider
    from nanobot.providers.registry import find_by_model

    model = model or config.agents.defaults.model
    
    # Detect provider from model name
    model_only = model.split("/")[-1] if "/" in model else model
    spec = find_by_model(model_only)
    provider_name = spec.name if spec else None
    
    # Get API key and base based on provider
    if provider_name == "ollama":
        api_key = config.get_api_key("ollama") or ""  # Ollama doesn't require key
        api_base = config.get_api_base("ollama")
    else:
        api_key = config.get_api_key()
        api_base = config.get_api_base()

    if not api_key and provider_name != "ollama":
        console.print("[red]Error: No API key configured.[/red]")
        console.print("Set one in ~/.nanobot/config.json:")
        console.print('  {"providers": {"openrouter": {"apiKey": "sk-or-v1-xxx"}}}')
        console.print("\nOr use Ollama for local models:")
        console.print('  {"agents": {"defaults": {"model": "ollama/llama3.2"}}}')
        raise typer.Exit(1)

    return LiteLLMProvider(
        api_key=api_key,
        api_base=api_base,
        default_model=model,
        provider_name=provider_name,
    )


# ============================================================================
# Agent Commands
# ============================================================================


@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Message to send to the agent"),
    session_id: str = typer.Option("default", "--session", "-s", help="Session ID"),
    markdown: bool = typer.Option(True, "--markdown/--no-markdown", help="Render assistant output as Markdown"),
    logs: bool = typer.Option(False, "--logs/--no-logs", help="Show nanobot runtime logs during chat"),
):
    """Interact with the agent."""
    from nanobot.config.loader import load_config, get_data_dir
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop
    from loguru import logger

    config = load_config()

    bus = MessageBus()
    provider = _make_provider(config)

    if logs:
        logger.enable("nanobot")
    else:
        logger.disable("nanobot")

    agent_loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model,
        temperature=config.agents.defaults.temperature,
        max_tokens=config.agents.defaults.max_tokens,
        max_iterations=config.agents.defaults.max_tool_iterations,
        memory_window=config.agents.defaults.memory_window,
        brave_api_key=config.tools.web.search.api_key or None,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
    )

    def _thinking_ctx():
        if logs:
            from contextlib import nullcontext
            return nullcontext()
        return console.status("[dim]nanobot is thinking...[/dim]", spinner="dots")

    async def _cli_progress(content: str) -> None:
        console.print(f"  [dim]↳ {content}[/dim]")

    if message:
        async def run_once():
            with _thinking_ctx():
                response = await agent_loop.process_direct(message, session_id, on_progress=_cli_progress)
            _print_agent_response(response, render_markdown=markdown)

        asyncio.run(run_once())
    else:
        _init_prompt_session()
        console.print(f"{__logo__} Interactive mode (type [bold]exit[/bold] or [bold]Ctrl+C[/bold] to quit)\n")

        def _exit_on_sigint(signum, frame):
            _restore_terminal()
            console.print("\nGoodbye!")
            os._exit(0)

        signal.signal(signal.SIGINT, _exit_on_sigint)

        async def run_interactive():
            try:
                while True:
                    try:
                        _flush_pending_tty_input()
                        user_input = await _read_interactive_input_async()
                        command = user_input.strip()
                        if not command:
                            continue

                        if _is_exit_command(command):
                            _restore_terminal()
                            console.print("\nGoodbye!")
                            break

                        with _thinking_ctx():
                            response = await agent_loop.process_direct(user_input, session_id, on_progress=_cli_progress)
                        _print_agent_response(response, render_markdown=markdown)
                    except KeyboardInterrupt:
                        _restore_terminal()
                        console.print("\nGoodbye!")
                        break
                    except EOFError:
                        _restore_terminal()
                        console.print("\nGoodbye!")
                        break
            finally:
                pass

        asyncio.run(run_interactive())


# ============================================================================
# Status Commands
# ============================================================================


@app.command()
def status():
    """Show nanobot status."""
    from nanobot.config.loader import load_config, get_config_path

    config_path = get_config_path()
    config = load_config()
    workspace = config.workspace_path

    console.print(f"{__logo__} nanobot Status\n")

    console.print(f"Config: {config_path} {'[green]✓[/green]' if config_path.exists() else '[red]✗[/red]'}")
    console.print(f"Workspace: {workspace} {'[green]✓[/green]' if workspace.exists() else '[red]✗[/red]'}")

    if config_path.exists():
        console.print(f"Model: {config.agents.defaults.model}")

        # OpenRouter
        openrouter_key = config.get_api_key()
        has_openrouter_key = bool(openrouter_key)
        console.print(f"OpenRouter API Key: {'[green]✓[/green]' if has_openrouter_key else '[dim]not set[/dim]'}")

        # Ollama
        ollama_key = config.get_api_key("ollama")
        ollama_base = config.get_api_base("ollama")
        ollama_configured = bool(ollama_base) or bool(ollama_key)
        console.print(f"Ollama: {'[green]✓[/green] ' + ollama_base if ollama_configured else '[dim]http://localhost:11434 (default)[/dim]'}")


# ============================================================================
# Skills Commands
# ============================================================================


skills_app = typer.Typer(help="Manage skills")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def skills_list():
    """List available skills."""
    from nanobot.config.loader import load_config
    from nanobot.agent.skills import SkillsLoader

    config = load_config()
    loader = SkillsLoader(config.workspace_path)

    skills = loader.list_skills(filter_unavailable=False)

    if not skills:
        console.print("No skills found.")
        return

    table = typer.Table(title="Available Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Source", style="green")
    table.add_column("Available", style="yellow")

    for skill in skills:
        meta = loader.get_skill_metadata(skill["name"]) or {}
        skill_meta = loader._parse_nanobot_metadata(meta.get("metadata", ""))
        available = loader._check_requirements(skill_meta)
        status = "[green]✓[/green]" if available else "[dim]✗[/dim]"
        table.add_row(skill["name"], skill["source"], status)

    console.print(table)


@skills_app.command("show")
def skills_show(
    name: str = typer.Argument(..., help="Skill name"),
):
    """Show skill content."""
    from nanobot.config.loader import load_config
    from nanobot.agent.skills import SkillsLoader

    config = load_config()
    loader = SkillsLoader(config.workspace_path)

    content = loader.load_skill(name)
    if not content:
        console.print(f"[red]Skill '{name}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[cyan]# Skill: {name}[/cyan]\n")
    console.print(content)


if __name__ == "__main__":
    app()
