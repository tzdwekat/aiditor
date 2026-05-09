import json
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table

from .analyzer import analyze_script
from .approval import write_approval_markdown, read_approved_shots
from .shot_lister import generate_production_prompts
from .models import ScriptAnalysis
from .generators import dispatch_generation
from .shot_lister import ShotList


console = Console()


@click.group()
def cli():
    """aiditor — AI-assisted video essay production pipeline."""
    pass


@cli.command()
@click.argument("script_path", type=click.Path(exists=True, path_type=Path))
def analyze(script_path: Path):
    """Stage 1: Analyze a script and produce structured production guidance."""
    console.print(f"[bold]Analyzing[/bold] {script_path.name}...")
    
    script_text = script_path.read_text()
    analysis = analyze_script(script_text)
    
    base = script_path.stem
    analysis_path = script_path.parent / f"{base}_analysis.json"
    approval_path = script_path.parent / f"{base}_approval.md"
    
    analysis_path.write_text(analysis.model_dump_json(indent=2))
    write_approval_markdown(analysis, approval_path)
    
    console.print(f"\n[green]✓[/green] Analysis written to [cyan]{analysis_path}[/cyan]")
    console.print(f"[green]✓[/green] Approval file written to [cyan]{approval_path}[/cyan]")
    
    # Tool breakdown — useful so you see at a glance what kind of work this script needs
    tool_counts = {}
    for shot in analysis.broll_opportunities:
        tool_counts[shot.tool_recommendation] = tool_counts.get(shot.tool_recommendation, 0) + 1
    
    table = Table(title="Summary")
    table.add_column("Category")
    table.add_column("Count", justify="right")
    table.add_row("Structural suggestions", str(len(analysis.structural_suggestions)))
    table.add_row("Line edits", str(len(analysis.line_edits)))
    table.add_row("B-roll opportunities", str(len(analysis.broll_opportunities)))
    for tool, count in tool_counts.items():
        table.add_row(f"  → {tool}", str(count))
    table.add_row("Music tone sections", str(len(analysis.music_tone_per_section)))
    console.print(table)
    
    console.print(f"\n[bold]Next:[/bold] Edit [cyan]{approval_path.name}[/cyan] to check the shots you want, then run:")
    console.print(f"  [yellow]aiditor approve {approval_path}[/yellow]")


@cli.command()
@click.argument("approval_path", type=click.Path(exists=True, path_type=Path))
def approve(approval_path: Path):
    """Stage 2: Read approved shots and generate production-ready prompts."""
    base = approval_path.stem.replace("_approval", "")
    analysis_path = approval_path.parent / f"{base}_analysis.json"
    
    if not analysis_path.exists():
        console.print(f"[red]Error:[/red] Could not find analysis file at {analysis_path}")
        raise click.Abort()
    
    analysis_data = json.loads(analysis_path.read_text())
    analysis = ScriptAnalysis.model_validate(analysis_data)
    
    approved = read_approved_shots(approval_path, analysis)
    
    if not approved:
        console.print("[yellow]No shots approved.[/yellow] Edit the approval file and check some boxes.")
        return
    
    console.print(f"[bold]Generating production prompts[/bold] for {len(approved)} approved shots...")
    
    shot_list = generate_production_prompts(approved)
    
    output_path = approval_path.parent / f"{base}_approved_prompts.json"
    output_path.write_text(shot_list.model_dump_json(indent=2))
    
    console.print(f"\n[green]✓[/green] Production prompts written to [cyan]{output_path}[/cyan]\n")
    
    # Group output by tool so the user can see what they need to do
    by_tool = {}
    for shot in shot_list.shots:
        by_tool.setdefault(shot.tool, []).append(shot)
    
    for tool, shots in by_tool.items():
        console.print(f"[bold magenta]━━━ {tool.upper()} ({len(shots)} shot{'s' if len(shots) != 1 else ''}) ━━━[/bold magenta]")
        for shot in shots:
            console.print(f"\n[bold cyan]Shot {shot.shot_index}[/bold cyan]")
            console.print(f"  {shot.production_prompt}")
            if shot.alternates:
                console.print(f"  [dim]Alternates:[/dim]")
                for alt in shot.alternates:
                    console.print(f"  [dim]  • {alt}[/dim]")
        console.print()


@cli.command()
@click.argument("prompts_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Where to write generated assets (defaults to <script>_generated/)",
)
def generate(prompts_path: Path, output_dir: Path | None):
    """Stage 3: Generate assets for all approved shots."""
    base = prompts_path.stem.replace("_approved_prompts", "")
    
    if output_dir is None:
        output_dir = prompts_path.parent / f"{base}_generated"
    
    prompts_data = json.loads(prompts_path.read_text())
    shot_list = ShotList.model_validate(prompts_data)
    
    if not shot_list.shots:
        console.print("[yellow]No shots to generate.[/yellow]")
        return
    
    # Show what's about to happen
    tool_counts = {}
    for shot in shot_list.shots:
        tool_counts[shot.tool] = tool_counts.get(shot.tool, 0) + 1
    
    console.print(f"[bold]Generating {len(shot_list.shots)} assets[/bold] to [cyan]{output_dir}[/cyan]")
    for tool, count in tool_counts.items():
        console.print(f"  • {tool}: {count}")
    
    if "veo" in tool_counts:
        console.print(
            f"\n[yellow]Note:[/yellow] {tool_counts['veo']} Veo generation(s) will run. "
            f"Each takes 1-3 minutes and incurs API costs."
        )
    
    console.print()
    
    with console.status("[bold]Running generators..."):
        results = dispatch_generation(shot_list, output_dir)
    
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    
    console.print(f"\n[green]✓ {len(successes)} succeeded[/green]")
    for result in successes:
        console.print(f"  Shot {result.shot_index} ({result.tool}) → [cyan]{result.output_path}[/cyan]")
    
    if failures:
        console.print(f"\n[red]✗ {len(failures)} failed[/red]")
        for result in failures:
            console.print(f"  Shot {result.shot_index} ({result.tool}): {result.error}")
    
    console.print(f"\n[bold]Output directory:[/bold] {output_dir}")