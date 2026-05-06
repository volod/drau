"""Terminal UI for detection test data entry."""

from collections.abc import Callable

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


def show_sample(
    console: Console,
    sample_num: int,
    total: int,
    label: str,
    distance_m: float,
    filename: str,
    duration_s: float | None = None,
    warning: str | None = None,
) -> None:
    label_text = (
        "[bold red]DRONE[/bold red]"
        if label == "drone"
        else "[bold blue]NON-DRONE[/bold blue]"
    )
    dist_text = f"{distance_m:.1f} m"
    if warning:
        dist_text += f"  [bold yellow]{warning}[/bold yellow]"

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("key",   style="bold")
    table.add_column("value")
    table.add_row("Sample",   f"{sample_num} / {total}")
    table.add_row("Type",     label_text)
    table.add_row("Distance", dist_text)
    if duration_s is not None:
        mins = int(duration_s) // 60
        secs = duration_s - mins * 60
        table.add_row("Length",   f"{mins}:{secs:04.1f}")
    table.add_row("File",     filename)
    console.print(Panel(table, title="[bold yellow]Detection Test[/bold yellow]", border_style="yellow"))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _warning_text(distance_m: float, max_reliable: float) -> str | None:
    if distance_m > max_reliable:
        return f"⚠ beyond microphone range (≤ {max_reliable:.0f} m)"
    return None


def _ask_distance(console: Console, current: float) -> float | None:
    new_str = Prompt.ask(
        f"  New distance in metres [current: {current:.1f}]",
        default=f"{current:.1f}",
        console=console,
    )
    try:
        new_dist = float(new_str)
        if new_dist <= 0:
            raise ValueError
        return new_dist
    except ValueError:
        console.print("  [red]Enter a positive number.[/red]")
        return None


def _enter_all(console: Console, mic_num: int) -> tuple[list[str] | None, str | None]:
    console.print(
        "[bold]Enter detection results[/bold]  "
        "(y = identified  /  n = not identified  /  r = replay  /  d = distance):"
    )
    results = []
    for i in range(1, mic_num + 1):
        answer = Prompt.ask(f"  Mic {i}", choices=["y", "n", "r", "d"], console=console)
        if answer == "r":
            return None, "replay"
        if answer == "d":
            return None, "distance"
        results.append("identified" if answer == "y" else "not_identified")
    return results, None


def _show_review(
    console: Console,
    results: list[str],
    distance_m: float,
    warning: str | None,
) -> None:
    dist_line = f"  [bold]Distance[/bold]  {distance_m:.1f} m"
    if warning:
        dist_line += f"  [bold yellow]{warning}[/bold yellow]"

    mic_lines = []
    for i, r in enumerate(results, 1):
        if r == "identified":
            mic_lines.append(f"  Mic {i}   [green]✓  identified[/green]")
        else:
            mic_lines.append(f"  Mic {i}   [red]✗  not identified[/red]")

    body = dist_line + "\n\n" + "\n".join(mic_lines)
    console.print(Panel(body, title="[bold]Review[/bold]", border_style="dim"))


# ── Public API ────────────────────────────────────────────────────────────────

def collect_results(
    console: Console,
    mic_num: int,
    replay_fn: Callable[[float], bool],
    initial_distance: float,
    max_reliable_distance: float,
    refresh_panel_fn: Callable[[float, str | None], None],
) -> tuple[list[str], float]:
    """Collect per-mic results, then offer review (c=confirm  e=edit  r=replay  d=distance).

    Returns (results, final_distance).
    """
    current_distance = initial_distance
    results: list[str] | None = None

    while True:
        warning = _warning_text(current_distance, max_reliable_distance)

        if results is None:
            entered_results, command = _enter_all(console, mic_num)
            if command == "replay":
                console.print("[dim]Replaying…[/dim]")
                replay_fn(current_distance)
                continue
            if command == "distance":
                new_dist = _ask_distance(console, current_distance)
                if new_dist is not None and abs(new_dist - current_distance) >= 0.01:
                    current_distance = new_dist
                    new_warning = _warning_text(current_distance, max_reliable_distance)
                    refresh_panel_fn(current_distance, new_warning)
                    console.print("[dim]Replaying at new distance…[/dim]")
                    replay_fn(current_distance)
                continue
            results = entered_results

        else:
            _show_review(console, results, current_distance, warning)
            console.print(
                "[dim]  [bold]c[/bold] confirm and next   "
                "[bold]e[/bold] edit a mic   "
                "[bold]r[/bold] replay   "
                "[bold]d[/bold] change distance[/dim]"
            )
            action = Prompt.ask("  →", choices=["c", "e", "r", "d"], default="c", console=console)

            if action == "c":
                return results, current_distance

            elif action == "r":
                console.print("[dim]Replaying…[/dim]")
                replay_fn(current_distance)

            elif action == "e":
                console.print(f"  Edit which mic? (1–{mic_num}): ", end="")
                raw = input().strip()
                try:
                    idx = int(raw) - 1
                except ValueError:
                    console.print("  [red]Please enter a number.[/red]")
                    continue
                if not 0 <= idx < mic_num:
                    console.print(f"  [red]Enter a number between 1 and {mic_num}.[/red]")
                    continue
                answer = Prompt.ask(f"  Mic {idx + 1}", choices=["y", "n"], console=console)
                results[idx] = "identified" if answer == "y" else "not_identified"

            elif action == "d":
                new_dist = _ask_distance(console, current_distance)
                if new_dist is not None and abs(new_dist - current_distance) >= 0.01:
                    current_distance = new_dist
                    new_warning = _warning_text(current_distance, max_reliable_distance)
                    refresh_panel_fn(current_distance, new_warning)
                    console.print("[dim]Replaying at new distance…[/dim]")
                    replay_fn(current_distance)
                    console.print("[dim]Re-enter detection results for the new distance:[/dim]")
                    entered_results, command = _enter_all(console, mic_num)
                    if command == "replay":
                        console.print("[dim]Replaying…[/dim]")
                        replay_fn(current_distance)
                        results = None
                        continue
                    if command == "distance":
                        new_dist = _ask_distance(console, current_distance)
                        if new_dist is not None and abs(new_dist - current_distance) >= 0.01:
                            current_distance = new_dist
                            new_warning = _warning_text(current_distance, max_reliable_distance)
                            refresh_panel_fn(current_distance, new_warning)
                            console.print("[dim]Replaying at new distance…[/dim]")
                            replay_fn(current_distance)
                        results = None
                        continue
                    results = entered_results
