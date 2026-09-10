"""``DEMON chat`` — interactive multi-turn chat REPL."""

from __future__ import annotations

import sys
from typing import List, Optional

import click
from rich.console import Console
from rich.markdown import Markdown

from OpenDEMON.cli._tool_names import resolve_tool_names
from OpenDEMON.core.config import load_config
from OpenDEMON.core.types import Message, Role


def _read_input(prompt: str = "You> ") -> Optional[str]:
    """Read user input with graceful EOF handling."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return None


def _build_catalog_xml_for_subset(skill_manager, names: list[str]) -> str:
    """Build <available_skills> XML containing only the named skills."""
    import html as _html
    lines = ["<available_skills>"]
    for name in names:
        try:
            manifest = skill_manager.resolve(name)
        except KeyError:
            continue
        if getattr(manifest, "disable_model_invocation", False):
            continue
        lines.append(
            f"  <skill name={_html.escape(name)!r}"
            f" description={_html.escape(manifest.description or name)!r} />"
        )
    lines.append("</available_skills>")
    return "\n".join(lines)


def _build_few_shot_for_subset(skill_manager, names: list[str]) -> list[str]:
    """Return few-shot examples only for the named skills."""
    examples: list[str] = []
    for name in names:
        try:
            manifest = skill_manager.resolve(name)
        except KeyError:
            continue
        oj = manifest.metadata.get("DEMON", {}) if manifest.metadata else {}
        for ex in oj.get("few_shot", []) or []:
            if not isinstance(ex, dict):
                continue
            inp = str(ex.get("input", ""))
            out = str(ex.get("output", ""))
            if inp or out:
                examples.append(f"### {name}\nInput: {inp}\nOutput: {out}")
    return examples


@click.command()
@click.option("-e", "--engine", "engine_key", default=None, help="Engine backend.")
@click.option("-m", "--model", "model_name", default=None, help="Model to use.")
@click.option("-a", "--agent", "agent_name", default=None, help="Agent type.")
@click.option("--tools", default=None, help="Comma-separated tool names.")
@click.option("--system", "system_prompt", default=None, help="Custom system prompt.")
@click.option(
    "--persona",
    "persona_name",
    default=None,
    help=(
        "Named persona dir under ~/.DEMON/personas/<name>/ "
        "(overrides config). Pass 'none' to disable all persona files."
    ),
)
@click.option(
    "--skill",
    "skill_names",
    multiple=True,
    help="Skill name to enable (repeatable). e.g. --skill cuopt-install",
)
def chat(
    engine_key: str | None,
    model_name: str | None,
    agent_name: str | None,
    tools: str | None,
    system_prompt: str | None,
    persona_name: str | None,
    skill_names: tuple[str, ...] = (),
) -> None:
    """Start an interactive multi-turn chat session.

    Commands during chat:
      /quit, /exit  — end session
      /clear        — clear conversation history
      /model        — show current model
      /help         — show available commands
      /history      — show conversation history
    """
    console = Console(stderr=True)

    config = load_config()

    # --- Skill selection ---------------------------------------------------
    _combined_skills: list[str] = list(skill_names)
    active_skill_names: list[str] | None = None
    if _combined_skills:
        active_skill_names = list(dict.fromkeys(_combined_skills))

    _skill_manager = None
    _active_skill_tools: list | None = None
    _active_catalog_xml: str | None = None
    _active_few_shot: list[str] | None = None
    if active_skill_names is not None:
        try:
            from OpenDEMON.core.events import EventBus as _EB
            from OpenDEMON.skills.manager import SkillManager as _SM
            from OpenDEMON.skills.validation import (
                UnknownSkillsError as _USE,
                resolve_skill_names as _rsn,
            )
            import pathlib as _pathlib

            _skill_manager = _SM(_EB())
            _skill_paths = []
            try:
                _skill_paths = [
                    _pathlib.Path(p)
                    for p in (getattr(config.skills, "paths", None) or [])
                ]
            except Exception:
                pass
            if _skill_paths:
                _skill_manager.discover(_skill_paths)
            else:
                _skill_manager.discover()

            try:
                active_skill_names = _rsn(
                    active_skill_names,
                    _skill_manager,
                    catalog_is_empty=len(_skill_manager.skill_names()) == 0,
                )
            except _USE as _exc:
                console.print(f"[red]{_exc}[/red]")
                sys.exit(1)

            _active_skill_tools = _skill_manager.get_filtered_skill_tools(active_skill_names)
            _active_catalog_xml = _build_catalog_xml_for_subset(_skill_manager, active_skill_names)
            _active_few_shot = _build_few_shot_for_subset(_skill_manager, active_skill_names)
        except ImportError:
            console.print("[yellow]Skills subsystem unavailable; ignoring --skill.[/yellow]")
    # --- End skill selection ----------------------------------------------

    import dataclasses as _dc

    effective_mf = (
        _dc.replace(config.memory_files, persona_name=persona_name)
        if persona_name is not None
        else config.memory_files
    )

    # Resolve engine
    from OpenDEMON.engine import get_engine
    from OpenDEMON.intelligence import register_builtin_models

    register_builtin_models()

    resolved = get_engine(config, engine_key)
    if resolved is None:
        console.print("[red]No inference engine available.[/red]")
        sys.exit(1)

    engine_name, engine = resolved
    model = model_name or config.intelligence.default_model
    if not model:
        from OpenDEMON.engine import discover_engines, discover_models

        all_engines = discover_engines(config)
        all_models = discover_models(all_engines)
        engine_models = all_models.get(engine_name, [])
        if engine_models:
            model = engine_models[0]
        else:
            console.print("[red]No model available.[/red]")
            sys.exit(1)

    # Resolve agent (optional)
    agent = None
    agent_key = agent_name or config.agent.default_agent
    if agent_key and agent_key != "none":
        try:
            import OpenDEMON.agents  # noqa: F401 — trigger registration
            from OpenDEMON.core.events import EventBus
            from OpenDEMON.core.registry import AgentRegistry

            if AgentRegistry.contains(agent_key):
                agent_cls = AgentRegistry.get(agent_key)
                kwargs: dict = {"bus": EventBus()}

                if getattr(agent_cls, "accepts_tools", False):
                    tool_names_list = resolve_tool_names(
                        tools,
                        getattr(config.tools, "enabled", None),
                        getattr(config.agent, "tools", None),
                    )
                    tool_instances = []
                    if tool_names_list:
                        import OpenDEMON.tools  # noqa: F401 — trigger registration
                        from OpenDEMON.core.registry import ToolRegistry
                        from OpenDEMON.tools._stubs import BaseTool

                        for tname in tool_names_list:
                            if ToolRegistry.contains(tname):
                                tcls = ToolRegistry.get(tname)
                                if isinstance(tcls, type) and issubclass(
                                    tcls, BaseTool
                                ):
                                    tool_instances.append(tcls())
                                elif isinstance(tcls, BaseTool):
                                    tool_instances.append(tcls)
                    if _active_skill_tools:
                        existing_names = {t.spec.name for t in tool_instances}
                        for _st in _active_skill_tools:
                            if _st.spec.name not in existing_names:
                                tool_instances.append(_st)
                                existing_names.add(_st.spec.name)
                    if tool_instances:
                        kwargs["tools"] = tool_instances
                    kwargs["max_turns"] = config.agent.max_turns

                    def _confirm(prompt: str) -> bool:
                        console.print(
                            f"[yellow]Confirm:[/yellow] {prompt} [y/N] ",
                            end="",
                        )
                        ans = input().strip().lower()
                        return ans in ("y", "yes")

                    kwargs["interactive"] = True
                    kwargs["confirm_callback"] = _confirm

                import inspect as _inspect

                if (
                    "prompt_builder"
                    in _inspect.signature(agent_cls.__init__).parameters
                ):
                    from OpenDEMON.prompt.builder import SystemPromptBuilder

                    kwargs["prompt_builder"] = SystemPromptBuilder(
                        agent_template=config.agent.default_system_prompt or "",
                        memory_files_config=effective_mf,
                        system_prompt_config=config.system_prompt,
                        skill_catalog_xml=_active_catalog_xml,
                        skill_few_shot_examples=_active_few_shot or [],
                    )

                if getattr(agent_cls, "accepts_tools", False) and _active_skill_tools:
                    existing_tools = kwargs.get("tools", [])
                    kwargs["tools"] = list(_active_skill_tools) + list(existing_tools)

                agent = agent_cls(engine, model, **kwargs)
        except Exception as exc:
            console.print(f"[yellow]Agent '{agent_key}' failed: {exc}[/yellow]")

    # Print banner
    console.print(
        f"[green bold]DEMON Chat[/green bold]\n"
        f"  Engine: [cyan]{engine_name}[/cyan]  Model: [cyan]{model}[/cyan]"
        f"  Agent: [cyan]{agent_key or 'direct'}[/cyan]\n"
        f"  Type /help for commands, /quit to exit.\n"
    )
    if active_skill_names:
        console.print(
            "[dim]Active skills: " + ", ".join(active_skill_names) + "[/dim]"
        )

    # Background-work status banner (disappears after first user message)
    from OpenDEMON.cli._bg_state import get_status
    from OpenDEMON.cli._chat_banner import render_startup_banner

    _banner = render_startup_banner(get_status())
    if _banner:
        console.print(f"[dim cyan]{_banner}[/dim cyan]")

    # Completion-notification dispatcher (fires once per task per session)
    from OpenDEMON.cli._chat_notifications import NotificationDispatcher

    _notifications = NotificationDispatcher(get_status())

    # Conversation state
    if not system_prompt:
        from OpenDEMON.prompt.builder import SystemPromptBuilder

        builder = SystemPromptBuilder(
            agent_template=config.agent.default_system_prompt or "",
            memory_files_config=effective_mf,
            system_prompt_config=config.system_prompt,
            skill_catalog_xml=_active_catalog_xml,
            skill_few_shot_examples=_active_few_shot or [],
        )
        system_prompt = builder.build()

    history: List[Message] = []
    if system_prompt:
        history.append(Message(role=Role.SYSTEM, content=system_prompt))

    # REPL loop
    while True:
        for note in _notifications.diff(get_status()):
            console.print(f"[dim cyan]{note}[/dim cyan]")

        user_input = _read_input()
        if user_input is None:
            console.print("\n[dim]Goodbye![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle slash commands
        cmd = user_input.lower()
        if cmd in ("/quit", "/exit", "/q"):
            console.print("[dim]Goodbye![/dim]")
            break
        elif cmd == "/clear":
            history = []
            if system_prompt:
                history.append(Message(role=Role.SYSTEM, content=system_prompt))
            console.print("[dim]History cleared.[/dim]")
            continue
        elif cmd == "/model":
            console.print(
                f"Model: [cyan]{model}[/cyan]  Engine: [cyan]{engine_name}[/cyan]"
            )
            continue
        elif cmd == "/help":
            console.print(
                "[bold]Commands:[/bold]\n"
                "  /quit, /exit  — end session\n"
                "  /clear        — clear conversation\n"
                "  /model        — show model info\n"
                "  /history      — show conversation\n"
                "  /help         — this message"
            )
            continue
        elif cmd == "/history":
            if not history:
                console.print("[dim]No history yet.[/dim]")
            else:
                for msg in history:
                    role_str = msg.role if isinstance(msg.role, str) else msg.role.value
                    role = role_str.upper()
                    console.print(f"[bold]{role}:[/bold] {msg.content[:200]}")
            continue

        # Add user message
        history.append(Message(role=Role.USER, content=user_input))

        # Generate response
        try:
            if agent is not None:
                response = agent.run(user_input)
                content = (
                    response.content if hasattr(response, "content") else str(response)
                )
            else:
                result = engine.generate(history, model=model)
                content = (
                    result.get("content", "")
                    if isinstance(result, dict)
                    else str(result)
                )

            history.append(Message(role=Role.ASSISTANT, content=content))
            console.print()
            console.print(Markdown(content))
            console.print()
        except KeyboardInterrupt:
            console.print("\n[dim]Generation interrupted.[/dim]")
        except Exception as exc:
            console.print(f"\n[red]Error: {exc}[/red]\n")


__all__ = ["chat"]
