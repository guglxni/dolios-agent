"""Extra CLI subcommand groups extracted from cli.py to stay under 400 lines (CQ-M2)."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def upstream() -> None:
    """Manage upstream repositories used by Dolios integrations."""


@upstream.command("status")
@click.option("--include-aidlc", is_flag=True, help="Include awslabs/aidlc-workflows")
@click.option("--refresh-remote", is_flag=True, help="Resolve remote HEAD refs")
def upstream_status(include_aidlc: bool, refresh_remote: bool) -> None:
    """Show local and remote commit state for upstream dependencies."""
    from dolios.upstream_manager import UpstreamManager

    manager = UpstreamManager(Path.cwd())
    statuses = manager.status(include_aidlc=include_aidlc, refresh_remote=refresh_remote)

    table = Table(title="Upstream Repositories")
    table.add_column("Repo", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Local SHA", style="bold")
    table.add_column("Remote HEAD", style="bold")

    for item in statuses:
        local_sha = item["local_sha"][:12] if item["local_sha"] else "(missing)"
        remote_sha = (
            item["remote_sha"][:12]
            if item.get("remote_sha")
            else "(skipped)" if not refresh_remote else "(unavailable)"
        )
        table.add_row(item["name"], item["path"], local_sha, remote_sha)

    console.print(table)


@upstream.command("sync")
@click.option("--include-aidlc", is_flag=True, help="Include awslabs/aidlc-workflows")
@click.option(
    "--sync-aidlc-rules/--no-sync-aidlc-rules",
    default=True,
    help="Sync .aidlc-rule-details from aidlc-workflows when included",
)
def upstream_sync(include_aidlc: bool, sync_aidlc_rules: bool) -> None:
    """Clone/fetch upstream repos to latest HEAD and write a manifest."""
    from dolios.upstream_manager import UpstreamManager

    manager = UpstreamManager(Path.cwd())
    manifest_path, manifest = manager.sync(
        include_aidlc=include_aidlc,
        sync_aidlc_rules=sync_aidlc_rules,
    )

    table = Table(title="Synced Upstreams")
    table.add_column("Repo", style="cyan")
    table.add_column("SHA", style="bold")
    table.add_column("Changed", style="bold")

    for item in manifest.get("repos", []):
        changed = "[yellow]Yes[/yellow]" if item.get("changed") else "[green]No[/green]"
        table.add_row(item["name"], item["synced_sha"][:12], changed)

    console.print(table)

    if aidlc := manifest.get("aidlc_rules"):
        console.print(
            "\n[bold]AI-DLC Rules[/bold]"
            f"\n  Files synced: {aidlc.get('files_synced', 0)}"
            f"\n  Version: {aidlc.get('version', '(unknown)')}"
            f"\n  Source SHA: {aidlc.get('source_sha', '(unknown)')[:12]}"
        )

    console.print(f"\n[green]Manifest written:[/green] {manifest_path}")


@upstream.command("compat")
@click.pass_context
def upstream_compat(ctx: click.Context) -> None:
    """Check fused Dolios runtime compatibility with synced upstream symbols."""
    from dolios.integrations import DoliosFusionRuntime

    runtime = DoliosFusionRuntime(ctx.obj["config"])
    snapshot = runtime.compatibility_snapshot()

    table = Table(title="Fusion Runtime Compatibility")
    table.add_column("Component", style="cyan")
    table.add_column("Symbol", style="dim")
    table.add_column("Available", style="bold")

    for symbol, ok in snapshot.get("hermes", {}).items():
        table.add_row("hermes", symbol, "[green]Yes[/green]" if ok else "[red]No[/red]")

    for symbol, ok in snapshot.get("evolution", {}).items():
        table.add_row("self-evolution", symbol, "[green]Yes[/green]" if ok else "[red]No[/red]")

    sandbox_enabled = snapshot.get("sandbox", {}).get("enabled", False)
    table.add_row(
        "nemoclaw",
        "sandbox adapter enabled",
        "[green]Yes[/green]" if sandbox_enabled else "[yellow]Disabled[/yellow]",
    )

    console.print(table)


@click.command()
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


@click.group()
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
@click.pass_context
def evolve_run(
    ctx: click.Context,
    dry_run: bool,
    target: str | None,
    iterations: int,
    eval_model: str,
) -> None:
    """Run an evolution cycle on a skill or target."""
    from dolios.integrations import EvolutionRuntimeAdapter

    runtime = EvolutionRuntimeAdapter(ctx.obj["config"])

    mode = "DRY RUN" if dry_run else "LIVE"
    console.print(f"[bold]Evolution Cycle ({mode})[/bold]\n")

    if not target:
        targets = runtime.list_targets()
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

    result = runtime.evolve_skill(
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
