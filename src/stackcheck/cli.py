"""
CLI Interface for StackCheck.
Provides commands for searching, analyzing, exporting, and launching the Web Dashboard.
"""

import sys
import os

# Ensure safe UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from stackcheck import __version__
from stackcheck.models import SearchQuery, WorkplaceType, ExperienceLevel, Region
from stackcheck.client.hiringcafe import HiringCafeClient
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.repository import JobRepository
from stackcheck.storage.sync import CommunitySyncClient
from stackcheck.storage.exporters import ReportExporter

console = Console(legacy_windows=False)


@click.group(invoke_without_command=True)
@click.version_option(__version__, "-v", "--version", message="StackCheck v%(version)s")
@click.pass_context
def main(ctx):
    """StackCheck: Tech Stack Intelligence Engine & Data Analytics Dashboard."""
    if ctx.invoked_subcommand is None:
        # Default behavior: Launch Web Dashboard
        from stackcheck.launcher import launch
        launch()


@main.command()
def stop():
    """Stop the running StackCheck server and release ports."""
    from stackcheck.launcher import stop_running_instance, get_running_instance
    info = get_running_instance()
    if info:
        pid = info.get("pid")
        port = info.get("port")
        with console.status("[bold cyan]Stopping StackCheck server...", spinner="dots"):
            stopped = stop_running_instance()
        if stopped:
            console.print(f"[bold green]✔[/bold green] Stopped StackCheck server (PID {pid}, port {port} released).")
        else:
            console.print("[bold red]✘[/bold red] [yellow]Could not stop server process cleanly.[/]")
    else:
        console.print("[dim]ℹ️  StackCheck is not currently running.[/]")


@main.command()
def status():
    """Check the health and runtime status of the StackCheck dashboard."""
    import time
    from stackcheck.launcher import get_running_instance, STACKCHECK_DIR
    info = get_running_instance()
    if info:
        uptime_s = int(time.time() - info.get("start_time", time.time()))
        mins, secs = divmod(uptime_s, 60)
        uptime_display = f"{mins}m {secs}s" if mins else f"{secs}s"

        table = Table(title="StackCheck Server Status", border_style="green", header_style="bold green")
        table.add_column("Property", style="bold white")
        table.add_column("Value", style="cyan")
        table.add_row("Status", "[bold green]Active (Listening)[/]")
        table.add_row("Local URL", f"[underline cyan]{info.get('url')}[/]")
        table.add_row("Port", str(info.get("port")))
        table.add_row("Process PID", f"[yellow]{info.get('pid')}[/]")
        table.add_row("Uptime", uptime_display)
        table.add_row("Data Directory", f"[dim]{STACKCHECK_DIR}[/]")
        console.print(table)
        console.print("[dim]Tip: Run '[bold magenta]stackcheck stop[/]' to shut down this server.[/]")
    else:
        console.print(Panel(
            "[bold yellow]StackCheck server is currently STOPPED.[/]\n\n"
            "Run [bold cyan]stackcheck[/] to launch the interactive dashboard.",
            title="StackCheck Server Status",
            border_style="yellow",
            padding=(1, 2)
        ))


@main.command()
def check():
    """Verify runtime environment and all core web dashboard dependencies."""
    console.print("[bold cyan]Verifying StackCheck runtime dependencies & C-extensions...[/]")
    modules = [
        ("NumPy Core Engine", "import numpy as np; from numpy import _core; _ = np.__version__"),
        ("Pandas Analytics", "import pandas as pd; _ = pd.DataFrame({'a': [1]})"),
        ("Streamlit Web Runtime", "import streamlit as st; _ = st.__version__"),
        ("Altair Visualization", "import altair as alt; _ = alt.__version__"),
        ("Matplotlib & Seaborn", "import matplotlib, seaborn; _ = matplotlib.__version__"),
        ("Streamlit Static Frontend Assets", "from pathlib import Path; import streamlit; p = Path(streamlit.__file__).parent / 'static'; assert p.exists(), f'Static dir missing at {p}'"),
        ("Web Dashboard Entrypoint", "import stackcheck.web.app"),
        ("Web Charts Engine", "import stackcheck.web.charts"),
    ]
    failed = False
    for label, code in modules:
        try:
            exec(code, {})
            console.print(f"  [bold green]✔[/] {label}")
        except Exception as e:
            console.print(f"  [bold red]✘[/] {label}: {e}")
            failed = True

    if failed:
        console.print("\n[bold red]✘ Runtime verification failed! Missing compiled libraries.[/]")
        sys.exit(1)
    console.print("\n[bold green]✔ All core web runtime dependencies and extensions verified successfully![/]")


@main.command()
@click.option("--yes", "-y", is_flag=True, default=False, help="Automatically download and install updates without asking.")
def update(yes):
    """Check for latest release updates and upgrade in-place."""
    from stackcheck.updater import UpdateChecker
    from stackcheck import __version__
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

    with console.status(f"[bold cyan]Checking for latest updates on GitHub...[/] (Current: v{__version__})", spinner="dots"):
        res = UpdateChecker.check_for_update()

    if not res:
        console.print(f"[bold green]✔ StackCheck is up to date (v{__version__}).[/]")
        return

    if not res.get("has_update"):
        console.print(f"[bold green]✔ StackCheck is up to date (v{__version__}).[/]")
        return

    latest_ver = res["latest_version"]
    console.print(Panel(
        f"[bold green]✨ New version v{latest_ver} available![/] (Current: v{__version__})\n\n"
        f"[white]{res['release_title']}[/]\n"
        f"Release page: [cyan]{res['html_url']}[/]",
        title="Update Available",
        border_style="green"
    ))

    target_asset = res.get("target_asset")
    if not target_asset or not target_asset.get("download_url"):
        console.print(f"[yellow]No prebuilt binary matched your platform. Visit {res['html_url']} to update manually.[/]")
        return

    if not yes:
        if not click.confirm(f"Do you want to download and install v{latest_ver} ({target_asset['name']}) now?", default=True):
            console.print("[dim]Update skipped.[/]")
            return

    target_path = UpdateChecker.get_install_target_path()
    console.print(f"[cyan]Installing update to:[/] [bold]{target_path}[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=36),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Downloading {target_asset['name']}...", total=target_asset.get("size_bytes", 0))

        def progress_cb(chunk_size, total_bytes):
            if total_bytes and progress.tasks[task].total != total_bytes:
                progress.update(task, total=total_bytes)
            progress.advance(task, chunk_size)

        try:
            UpdateChecker.download_asset(
                download_url=target_asset["download_url"],
                dest_path=target_path,
                progress_callback=progress_cb
            )
            console.print(f"[bold green]✔ Successfully updated StackCheck to v{latest_ver}![/]")
            console.print("[dim]Restart StackCheck or run 'stackcheck' to use the new version.[/]")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to download update:[/] {e}")



@main.command()
@click.argument("keywords", default="Data Analyst")
@click.option("--location", "-l", default="", help="Filter by location (e.g. 'United States', 'London', 'India').")
@click.option("--workplace", "-w", type=click.Choice(["remote", "hybrid", "onsite", "any"]), default="any", help="Filter by workplace type.")
@click.option("--experience", "-e", type=click.Choice(["entry", "mid", "senior", "lead", "any"]), default="any", help="Filter by experience level.")
@click.option("--limit", "-n", default=25, help="Number of job postings to analyze.")
@click.option("--project", "-P", default="default", help="Project ID or name to scope this research to.")
@click.option("--export", "-x", type=click.Choice(["json", "csv", "md", "none"]), default="none", help="Export results to file.")
@click.option("--use-llm", is_flag=True, default=False, help="Use LLM for deep extraction (requires GEMINI_API_KEY or OPENAI_API_KEY).")
def search(keywords, location, workplace, experience, limit, project, export, use_llm):
    """Scrape and analyze jobs for specific keywords and filters."""
    workplace_enum = WorkplaceType(workplace) if workplace != "any" else None
    exp_enum = ExperienceLevel(experience) if experience != "any" else None

    # Ensure project exists
    repo = JobRepository()
    repo.create_project(project_id=project, name=project)

    query = SearchQuery(
        keywords=keywords,
        location=location,
        workplace_type=workplace_enum,
        experience_level=exp_enum,
        limit=limit,
        project_id=project
    )

    console.print(Panel(
        f"[bold cyan]StackCheck Data Pipeline[/]\n\n"
        f"  🎯 Query:     [bold yellow]{keywords}[/] (Limit: {limit})\n"
        f"  📍 Location:  [magenta]{location or 'Global'}[/]\n"
        f"  🏢 Workplace: [green]{workplace}[/] | Exp: [blue]{experience}[/]\n"
        f"  📁 Project:   [cyan]{project}[/]",
        title="[bold cyan]Search Pipeline[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))

    client = HiringCafeClient(use_llm_if_available=use_llm)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=32),
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Ingesting and cleaning job postings...", total=limit)

        def cb(curr, total, msg):
            progress.update(task, completed=curr, total=total, description=f"[dim]{msg}[/]")

        jobs = client.search_jobs(query, progress_callback=cb)

    if not jobs:
        console.print("[bold red]✘ No matching job postings found.[/]")
        return

    console.print(f"[bold green]✔[/bold green] Ingested and parsed [bold white]{len(jobs)}[/bold white] postings for [bold yellow]'{keywords}'[/].")

    # Save to SQLite repository scoped to project
    run_id = repo.save_search_run(query, len(jobs), project_id=project)
    repo.save_jobs(jobs, search_run_id=run_id, project_id=project)

    # Compute multidimensional analytics
    stats = MetricsEngine.aggregate(jobs, query_keywords=keywords)

    # 1. Top Skills Table
    table = Table(
        title=f"🔥 Top Demanded Skills for '{keywords}' ({len(jobs)} jobs) [Project: {project}]",
        border_style="cyan",
        header_style="bold cyan"
    )
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Technology", style="bold white")
    table.add_column("Category", style="cyan")
    table.add_column("Demand % (Count)", justify="right", style="green")
    table.add_column("Priority Score", justify="right", style="yellow")

    for idx, item in enumerate(stats.top_skills_overall[:15], 1):
        table.add_row(
            str(idx),
            item["skill"],
            item["category"],
            f"{item['percentage']}% ({item['count']})",
            str(item["weighted_score"])
        )
    console.print(table)

    # 2. Co-occurrence Synergies Table
    if stats.co_occurrences:
        co_table = Table(title="🔗 Top Tech Stack Pairings (Co-Occurrences)", border_style="yellow", header_style="bold yellow")
        co_table.add_column("Primary Tech", style="bold white")
        co_table.add_column("Paired Tech", style="bold white")
        co_table.add_column("Shared Jobs", justify="right", style="cyan")
        co_table.add_column("Synergy %", justify="right", style="green")

        for pair in stats.co_occurrences[:8]:
            co_table.add_row(pair.skill_a, pair.skill_b, str(pair.count), f"{pair.percentage}%")
        console.print(co_table)

    # 3. Export Handling
    if export == "json":
        p = ReportExporter.export_json(stats, jobs)
        console.print(f"[bold green]✔[/bold green] Saved JSON report to: [cyan]{p}[/]")
    elif export == "csv":
        p = ReportExporter.export_csv(jobs)
        console.print(f"[bold green]✔[/bold green] Saved CSV jobs to: [cyan]{p}[/]")
    elif export == "md":
        p = ReportExporter.export_markdown(stats)
        console.print(f"[bold green]✔[/bold green] Saved Markdown summary to: [cyan]{p}[/]")


@main.command()
@click.option("--limit", "-n", default=100, help="Number of cached jobs to aggregate.")
@click.option("--project", "-P", default=None, help="Filter cached jobs by project ID.")
@click.option("--region", "-r", default="All", help="Filter by region (USA, Europe, India, APAC, Latin America).")
def analyze(limit, project, region):
    """Generate deep metrics and insights from previously scraped jobs."""
    repo = JobRepository()
    jobs = repo.get_all_jobs(limit=limit, project_id=project, region=region if region != "All" else None)

    if not jobs:
        target = f"in project '{project}'" if project else "in local database"
        console.print(f"[yellow]No cached jobs found {target}. Run `stackcheck search` first![/]")
        return

    stats = MetricsEngine.aggregate(jobs, query_keywords=f"Cached Intelligence ({len(jobs)} jobs)")

    scope_title = f"Project: {project}" if project else "All Projects"
    console.print(Panel(
        f"[bold green]Database Summary ({scope_title})[/]\n"
        f"Analyzed Postings: [cyan]{stats.total_jobs}[/] | Unique Companies: [yellow]{stats.unique_companies}[/] | "
        f"Remote: [magenta]{stats.workplace_distribution.get('remote', 0)}[/] | "
        f"Hybrid: [blue]{stats.workplace_distribution.get('hybrid', 0)}[/] | "
        f"Onsite: [white]{stats.workplace_distribution.get('onsite', 0)}[/]",
        border_style="green"
    ))

    # Print Category Highlights
    for cat_name, skill_list in stats.category_breakdown.items():
        if not skill_list:
            continue
        cat_table = Table(title=f"📁 {cat_name}", border_style="blue")
        cat_table.add_column("Skill", style="bold white")
        cat_table.add_column("Demand %", justify="right", style="green")
        cat_table.add_column("Count", justify="right", style="cyan")
        for s in skill_list[:6]:
            cat_table.add_row(s["skill"], f"{s['percentage']}%", str(s["count"]))
        console.print(cat_table)


@main.command()
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv", "md", "all"]), default="all")
@click.option("--project", "-P", default=None, help="Export jobs from specific project.")
def export(fmt, project):
    """Export current cached database to files."""
    repo = JobRepository()
    jobs = repo.get_all_jobs(project_id=project)
    if not jobs:
        console.print("[yellow]No jobs in database to export.[/]")
        return

    stats = MetricsEngine.aggregate(jobs, query_keywords="All Cached Jobs")

    if fmt in ("json", "all"):
        p = ReportExporter.export_json(stats, jobs)
        console.print(f"[bold green]✔ Exported JSON:[/] [cyan]{p}[/]")
    if fmt in ("csv", "all"):
        p = ReportExporter.export_csv(jobs)
        console.print(f"[bold green]✔ Exported CSV:[/] [cyan]{p}[/]")
    if fmt in ("md", "all"):
        p = ReportExporter.export_markdown(stats)
        console.print(f"[bold green]✔ Exported Markdown:[/] [cyan]{p}[/]")


@main.group()
def projects():
    """Manage research projects and scopes."""
    pass


@projects.command("list")
def list_projects():
    """List all research projects with job counts."""
    repo = JobRepository()
    proj_list = repo.get_projects()
    table = Table(title="🗂️ StackCheck Research Projects", border_style="cyan")
    table.add_column("Project ID", style="bold white")
    table.add_column("Name", style="yellow")
    table.add_column("Description", style="dim")
    table.add_column("Saved Jobs", justify="right", style="green")
    table.add_column("Created", style="cyan")

    for p in proj_list:
        count = repo.count_total_jobs(project_id=p.id)
        created_str = p.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(p.created_at, "strftime") else str(p.created_at)[:19]
        table.add_row(p.id, p.name, p.description or "-", str(count), created_str)
    console.print(table)


@projects.command("create")
@click.argument("project_id")
@click.option("--name", "-n", default=None, help="Friendly display name.")
@click.option("--desc", "-d", default="", help="Project description.")
def create_project(project_id, name, desc):
    """Create a new research workspace project."""
    repo = JobRepository()
    p = repo.create_project(project_id=project_id, name=name or project_id, description=desc)
    console.print(f"[bold green]✔ Created project '{p.id}' ({p.name})[/]")


@projects.command("delete")
@click.argument("project_id")
@click.confirmation_option(prompt="Are you sure you want to delete this project and all its jobs?")
def delete_project(project_id):
    """Delete a research project and its saved jobs."""
    if project_id == "default":
        console.print("[bold red]Cannot delete the default project.[/]")
        return
    repo = JobRepository()
    repo.delete_project(project_id)
    console.print(f"[bold green]✔ Deleted project '{project_id}'[/]")


@main.command()
def sync():
    """Sync telemetry and pull global community benchmark statistics."""
    sync_client = CommunitySyncClient()
    benchmarks = sync_client.fetch_community_benchmarks()

    console.print(Panel(
        f"[bold cyan]🌐 StackCheck Community Benchmark Hub[/]\n"
        f"Total Community Jobs Dataset: [green]{benchmarks.get('total_community_jobs', 0):,}[/] | "
        f"Last Baseline Updated: [yellow]{benchmarks.get('last_updated', 'N/A')}[/]",
        border_style="cyan"
    ))

    table = Table(title="Global Top Demanded Technologies (Community Baseline)", border_style="green")
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Skill", style="bold white")
    table.add_column("Category", style="cyan")
    table.add_column("Global Demand %", justify="right", style="green")

    for idx, item in enumerate(benchmarks.get("top_skills_global", []), 1):
        table.add_row(str(idx), item["skill"], item["category"], f"{item['percentage']}%")
    console.print(table)


if __name__ == "__main__":
    main()
