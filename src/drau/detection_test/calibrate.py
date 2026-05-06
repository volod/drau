"""Speaker calibration for detection test.

Uses the default system microphone (embedded or wired) to measure speaker
output, then asks the user to confirm audibility. This handles all hardware
combinations without any microphone type configuration.
"""

import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from rich.console import Console
from rich.prompt import Prompt

RATE = 16_000
TONE_FREQ = 1_000
CALIB_DURATION = 2.0

# Below this gain the distance simulation is unreliable (~−52 dBFS floor).
MIN_PLAYBACK_GAIN = 0.02

_INITIAL_GAIN = 0.6
_GAIN_STEP    = 0.2


def _rms_dbfs(signal: np.ndarray) -> float:
    rms = np.sqrt(np.mean(signal.astype(np.float64) ** 2))
    return 20.0 * np.log10(max(float(rms), 1e-10))


def _play_tone(gain: float) -> float:
    """Play calibration tone; return mic-measured dBFS (−100 if unavailable)."""
    n    = int(CALIB_DURATION * RATE)
    t    = np.linspace(0.0, CALIB_DURATION, n, dtype=np.float32)
    tone = (gain * 0.7 * np.sin(2.0 * np.pi * TONE_FREQ * t)).astype(np.float32)
    try:
        recorded = sd.playrec(tone[:, np.newaxis], samplerate=RATE, channels=1, dtype="float32")
        sd.wait()
        return _rms_dbfs(recorded[int(0.3 * RATE):, 0])
    except sd.PortAudioError:
        sd.play(tone, RATE, blocking=True)
        return -100.0


@dataclass
class Calibration:
    """Result of the speaker calibration pass."""

    ref_scale:  float   # confirmed reference gain (maps to drone at 1 m)
    unity_dbfs: float   # mic-measured dBFS at ref_scale (informational only)

    @property
    def max_reliable_distance(self) -> float:
        """Distance at which raw gain would fall below MIN_PLAYBACK_GAIN."""
        return self.ref_scale / MIN_PLAYBACK_GAIN

    def gain_for_distance(self, distance_m: float) -> float:
        amplitude = self.ref_scale / max(float(distance_m), 1.0)
        return float(np.clip(amplitude, MIN_PLAYBACK_GAIN, 1.0))


def calibrate(console: Console) -> Calibration:
    """Adjust speaker volume interactively using the default system microphone."""
    console.print("\n[bold yellow]Speaker Volume Calibration[/bold yellow]")
    console.print(
        "The system microphone is used only here to help tune the speaker volume.\n"
        "[bold]Position the default computer microphone (built-in, headset, or wired) "
        "exactly 1 metre from the speaker.[/bold]  "
        "This distance is the reference for all simulated distances in the session.\n"
        "Set your system volume so the tone is [bold]clearly audible but not distorted[/bold].\n"
        "Press [bold]Enter[/bold] when ready."
    )
    input()

    gain       = _INITIAL_GAIN
    unity_dbfs = -100.0

    while True:
        console.print(f"  [dim]Playing tone at {gain:.0%}…[/dim]")
        unity_dbfs = _play_tone(gain)
        if unity_dbfs > -90.0:
            console.print(f"  [dim]Mic level: {unity_dbfs:.1f} dBFS[/dim]")

        console.print(
            "  [dim]y = clearly audible  "
            "n = too quiet (will increase)  "
            "l = too loud (will decrease)[/dim]"
        )
        answer = Prompt.ask(
            "  Can you clearly hear the tone?",
            choices=["y", "n", "l"],
            console=console,
        )

        if answer == "y":
            break
        elif answer == "n":
            if gain >= 1.0:
                console.print("  [yellow]Already at maximum. Proceeding.[/yellow]")
                break
            gain = min(1.0, gain + _GAIN_STEP)
        else:
            gain = max(0.1, gain - _GAIN_STEP)

    max_dist = gain / MIN_PLAYBACK_GAIN
    console.print(
        f"\n[green]Calibration complete.[/green] "
        f"Reference: [cyan]{gain:.0%}[/cyan]  "
        f"Reliable range: [cyan]≤ {max_dist:.0f} m[/cyan]\n"
    )
    return Calibration(ref_scale=gain, unity_dbfs=unity_dbfs)
