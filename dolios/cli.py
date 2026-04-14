"""Dolios CLI — the main entry point for the Dolios agent.

Wraps Hermes Agent commands and adds Dolios-specific subcommands
for sandbox management, policy control, evolution, and AI-DLC workflow.

Subcommand groups for upstream, model, and evolve live in cli_commands.py
to keep this file under the 400-line project convention (CQ-M2).
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from dolios.cli_commands import evolve, model, upstream

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


# Register subcommand groups from cli_commands.py
cli.add_command(upstream)
cli.add_command(model)
cli.add_command(evolve)


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

    for name, model_name, env, has_key in providers_status:
        status = "[green]Ready[/green]" if has_key else f"[red]Set {env}[/red]"
        table.add_row(name, model_name, env or "(none)", status)

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
@click.pass_context
def aidlc(ctx: click.Context) -> None:
    """Show the current AI-DLC workflow phase."""
    from dolios.aidlc_engine import AIDLCEngine

    config = ctx.obj["config"]
    engine = AIDLCEngine(config)

    console.print(f"[bold]AI-DLC Phase:[/bold] {engine.current_phase.value.upper()}")
    console.print(f"\n{engine.get_phase_prompt()}")


@cli.group()
def verify() -> None:
    """Run release-readiness verification checks."""


@verify.command("release")
@click.pass_context
def verify_release(ctx: click.Context) -> None:
    """Run production-grade release checks."""
    from dolios.release_verifier import ReleaseVerifier

    verifier = ReleaseVerifier(ctx.obj["config"], Path.cwd())
    results = verifier.run_checks()

    table = Table(title="Release Verification")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    for item in results:
        status = "[green]PASS[/green]" if item.passed else "[red]FAIL[/red]"
        table.add_row(item.name, status, item.details)

    console.print(table)

    if ReleaseVerifier.is_ready(results):
        console.print("\n[green]Release verification passed.[/green]")
        return

    raise click.ClickException("Release verification failed")


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
        (
            "vendor/hermes-agent-self-evolution",
            Path("vendor/hermes-agent-self-evolution").is_dir(),
        ),
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
