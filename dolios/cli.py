"""Dolios CLI — the main entry point for the Dolios agent.

Wraps Hermes Agent commands and adds Dolios-specific subcommands
for sandbox management, policy control, evolution, and AI-DLC workflow.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(invoke_without_command=True)
@click.option("--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING, ERROR)")
@click.option("--no-sandbox", is_flag=True, help="Disable NemoClaw sandbox")
@click.pass_context
def cli(ctx: click.Context, log_level: str, no_sandbox: bool) -> None:
    """Dolios — The Crafty Agent. Scheme. Execute. Deliver."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s | %(name)s | %(message)s",
    )

    from dolios.config import DoliosConfig

    ctx.ensure_object(dict)
    ctx.obj["no_sandbox"] = no_sandbox
    ctx.obj["config"] = DoliosConfig.load(Path.cwd())

    if ctx.invoked_subcommand is None:
        # Default: start interactive agent
        ctx.invoke(start)


@cli.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """Start the Dolios interactive agent."""
    from dolios.orchestrator import DoliosOrchestrator

    config = ctx.obj["config"]
    if ctx.obj.get("no_sandbox"):
        config.sandbox.enabled = False

    console.print("[bold]Δ Dolios[/bold] — The Crafty Agent", style="bold blue")
    console.print("Scheme. Execute. Deliver.\n", style="dim")

    orchestrator = DoliosOrchestrator(config, Path.cwd())
    asyncio.run(orchestrator.start())


@cli.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Run the Dolios setup wizard."""
    console.print("[bold]Δ Dolios Setup Wizard[/bold]\n", style="bold blue")

    config = ctx.obj["config"]

    # Check for required API keys
    import os

    providers_status = []
    for name, provider in config.inference.providers.items():
        api_key_env = provider.get("api_key_env", "")
        has_key = bool(not api_key_env or os.environ.get(api_key_env))
        providers_status.append((name, provider.get("model", ""), api_key_env, has_key))

    table = Table(title="Inference Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="dim")
    table.add_column("API Key Env", style="dim")
    table.add_column("Status", style="bold")

    for name, model, env, has_key in providers_status:
        status = "[green]Ready[/green]" if has_key else f"[red]Set {env}[/red]"
        table.add_row(name, model, env or "(none)", status)

    console.print(table)

    # Check sandbox prerequisites
    console.print("\n[bold]Sandbox Status[/bold]")
    # TODO: Check if OpenShell/Docker is available
    console.print("  NemoClaw sandbox: [yellow]Not yet configured[/yellow]")
    console.print("  Run [bold]dolios sandbox status[/bold] after M1 implementation\n")

    console.print("[green]Setup complete.[/green] Run [bold]dolios[/bold] to start.")


@cli.group()
def sandbox() -> None:
    """Manage the NemoClaw sandbox."""


@sandbox.command("status")
def sandbox_status() -> None:
    """Check sandbox health, policy state, and resource usage."""
    console.print("[bold]Sandbox Status[/bold]\n")
    # TODO (M1): Query NemoClaw sandbox state
    console.print("  Sandbox: [yellow]Not bootstrapped[/yellow]")
    console.print("  Blueprint: v0.1.0 (target)")
    console.print("  Policy: dolios-default.yaml")
    console.print("\n  [dim]Sandbox integration is planned for M1 (Week 3-4)[/dim]")


@sandbox.command("policy")
@click.pass_context
def sandbox_policy(ctx: click.Context) -> None:
    """View the current network policy."""
    from dolios.io import load_yaml

    policy_path = Path("policies/generated/dolios-active.yaml")
    if not policy_path.exists():
        # Generate default policy
        from dolios.policy_bridge import PolicyBridge

        config = ctx.obj["config"]
        bridge = PolicyBridge(config)
        policy_path = bridge.generate_policy()

    policy = load_yaml(policy_path, default={})

    console.print("[bold]Active Network Policy[/bold]\n")

    # NemoClaw format: network_policies with named blocks
    network_policies = policy.get("network_policies", {})
    if not network_policies:
        # Legacy format fallback
        console.print("  [yellow]No network policies defined[/yellow]")
        return

    table = Table(title="Network Policies")
    table.add_column("Policy", style="cyan")
    table.add_column("Host", style="dim")
    table.add_column("Port", style="dim")
    table.add_column("Enforcement", style="bold")

    for name, block in network_policies.items():
        for endpoint in block.get("endpoints", []):
            table.add_row(
                name,
                endpoint.get("host", ""),
                str(endpoint.get("port", 443)),
                endpoint.get("enforcement", "enforce"),
            )

    console.print(table)


@sandbox.command("approve")
@click.pass_context
def sandbox_approve(ctx: click.Context) -> None:
    """Approve pending endpoint requests."""
    from dolios.io import load_yaml, save_yaml

    config = ctx.obj["config"]
    pending_file = config.home / "pending_approvals.yaml"

    if not pending_file.exists():
        console.print("[green]No pending approvals.[/green]")
        return

    pending = load_yaml(pending_file, default=[])

    pending_items = [p for p in pending if p.get("status") == "pending"]
    if not pending_items:
        console.print("[green]No pending approvals.[/green]")
        return

    for item in pending_items:
        console.print(
            f"\n  [yellow]Pending:[/yellow] {item['host']}:{item['port']}"
            f"\n  Tool: {item['tool']}"
            f"\n  Reason: {item['reason']}"
        )
        if click.confirm("  Approve?"):
            item["status"] = "approved"
            console.print("  [green]Approved[/green]")
        else:
            item["status"] = "denied"
            console.print("  [red]Denied[/red]")

    save_yaml(pending_file, pending)


@cli.command()
@click.option("--provider", help="Override inference provider")
@click.pass_context
def model(ctx: click.Context, provider: str | None) -> None:
    """Show or switch the inference provider/model."""
    from dolios.inference_router import InferenceRouter

    config = ctx.obj["config"]
    router = InferenceRouter(config)
    router.configure()

    if provider:
        route = router.route(preferred_provider=provider)
        console.print(f"Switched to [bold]{route.provider}[/bold]: {route.model}")
    else:
        table = Table(title="Inference Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Model", style="dim")
        table.add_column("Available", style="bold")

        for p in router.list_providers():
            status = "[green]Yes[/green]" if p["available"] else "[red]No[/red]"
            table.add_row(p["name"], p["model"], status)

        console.print(table)


@cli.group()
def evolve() -> None:
    """Run or inspect the self-evolution pipeline."""


@evolve.command("status")
def evolve_status() -> None:
    """Show self-evolution pipeline status."""
    console.print("[bold]Self-Evolution Pipeline[/bold]\n")
    console.print("  Status: [yellow]Not yet initialized[/yellow]")
    console.print("  Optimizer: DSPy + GEPA")
    console.print("  Targets: skills, tool descriptions, system prompts, code")
    console.print("\n  [dim]Self-evolution integration is planned for M5 (Week 11-12)[/dim]")


@evolve.command("run")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--target", help="Specific skill or target to evolve")
@click.option("--iterations", default=10, help="Number of GEPA iterations")
@click.option("--eval-model", default="openai/gpt-4.1-mini", help="Model for evaluation")
def evolve_run(dry_run: bool, target: str | None, iterations: int, eval_model: str) -> None:
    """Run an evolution cycle on a skill or target."""
    from evolution.dolios_targets import evolve_skill, get_all_targets

    mode = "DRY RUN" if dry_run else "LIVE"
    console.print(f"[bold]Evolution Cycle ({mode})[/bold]\n")

    if not target:
        # Show available targets
        targets = get_all_targets()
        table = Table(title="Available Evolution Targets")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Tier", style="bold")
        table.add_column("Description")
        for t in targets:
            table.add_row(t.name, t.target_type, str(t.tier), t.description)
        console.print(table)
        console.print("\nRun with --target <name> to evolve a specific target.")
        return

    console.print(f"  Target: [cyan]{target}[/cyan]")
    console.print(f"  Iterations: {iterations}")
    console.print(f"  Eval model: {eval_model}")
    console.print()

    result = evolve_skill(
        skill_name=target,
        iterations=iterations,
        eval_model=eval_model,
        dry_run=dry_run,
        project_dir=Path.cwd(),
    )

    if "error" in result:
        console.print(f"  [red]Error: {result['error']}[/red]")
        if "hint" in result:
            console.print(f"  [dim]{result['hint']}[/dim]")
    else:
        if "improvement" in result:
            imp = result["improvement"]
            color = "green" if imp > 0 else "red"
            console.print(f"  Baseline score: {result.get('baseline_score', 'N/A')}")
            console.print(f"  Evolved score: {result.get('evolved_score', 'N/A')}")
            console.print(f"  Improvement: [{color}]{imp:+.1%}[/{color}]")
        else:
            console.print(f"  [green]Completed[/green]: {result}")


@cli.command()
@click.pass_context
def aidlc(ctx: click.Context) -> None:
    """Show the current AI-DLC workflow phase."""
    from dolios.aidlc_engine import AIDLCEngine

    config = ctx.obj["config"]
    engine = AIDLCEngine(config)

    console.print(f"[bold]AI-DLC Phase:[/bold] {engine.current_phase.value.upper()}")
    console.print(f"\n{engine.get_phase_prompt()}")


@cli.command()
def doctor() -> None:
    """Diagnose Dolios installation issues."""
    import shutil

    console.print("[bold]Δ Dolios Doctor[/bold]\n")

    checks = [
        ("Python 3.12+", sys.version_info >= (3, 12)),
        ("uv available", shutil.which("uv") is not None),
        ("Docker available", shutil.which("docker") is not None),
        ("git available", shutil.which("git") is not None),
        ("CLAUDE.md exists", Path("CLAUDE.md").exists()),
        ("SOUL.md exists", Path("brand/SOUL.md").exists()),
        ("pyproject.toml exists", Path("pyproject.toml").exists()),
        ("vendor/hermes-agent", Path("vendor/hermes-agent").is_dir()),
        ("vendor/nemoclaw", Path("vendor/nemoclaw").is_dir()),
        ("vendor/hermes-agent-self-evolution", Path("vendor/hermes-agent-self-evolution").is_dir()),
    ]

    all_pass = True
    for name, result in checks:
        status = "[green]OK[/green]" if result else "[red]MISSING[/red]"
        if not result:
            all_pass = False
        console.print(f"  {status}  {name}")

    console.print()
    if all_pass:
        console.print("[green]All checks passed.[/green]")
    else:
        console.print("[yellow]Some checks failed. Fix the issues above.[/yellow]")


if __name__ == "__main__":
    cli()
