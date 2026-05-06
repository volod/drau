"""Speaker calibration for detection test.

The operator first identifies their hardware (speaker + microphone type), then
tunes the speaker volume interactively.  The resulting :class:`Calibration`
object carries both the confirmed reference gain and the hardware profile, so
that later playback can apply the correct volume floor and distance model.
"""

import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from rich.console import Console
from rich.prompt import Prompt

from drau.settings.constants import (
    AUDIO_SAMPLE_RATE_HZ,
    CALIBRATION_GAIN_MAX,
    CALIBRATION_GAIN_MIN,
    CALIBRATION_GAIN_STEP,
    CALIBRATION_INITIAL_GAIN,
    CALIBRATION_MIC_QUIET_DBFS,
    CALIBRATION_RECORDING_SKIP_S,
    CALIBRATION_TONE_AMPLITUDE,
    CALIBRATION_TONE_DURATION_S,
    CALIBRATION_TONE_FREQ_HZ,
    LOG_EPSILON,
    MIC_TYPE_INTERNAL,
    PLAYBACK_REFERENCE_DISTANCE_M,
)
from drau.detection_test.hardware import HardwareProfile, min_playback_gain, select_hardware


def _rms_dbfs(signal: np.ndarray) -> float:
    rms = np.sqrt(np.mean(signal.astype(np.float64) ** 2))
    return 20.0 * np.log10(max(float(rms), LOG_EPSILON))


def _play_tone(gain: float) -> float:
    """Play calibration tone; return mic-measured dBFS (−100 if unavailable)."""
    n    = int(CALIBRATION_TONE_DURATION_S * AUDIO_SAMPLE_RATE_HZ)
    t    = np.linspace(0.0, CALIBRATION_TONE_DURATION_S, n, dtype=np.float32)
    tone = (gain * CALIBRATION_TONE_AMPLITUDE * np.sin(2.0 * np.pi * CALIBRATION_TONE_FREQ_HZ * t)).astype(np.float32)
    try:
        skip     = int(CALIBRATION_RECORDING_SKIP_S * AUDIO_SAMPLE_RATE_HZ)
        recorded = sd.playrec(tone[:, np.newaxis], samplerate=AUDIO_SAMPLE_RATE_HZ, channels=1, dtype="float32")
        sd.wait()
        return _rms_dbfs(recorded[skip:, 0])
    except sd.PortAudioError:
        sd.play(tone, AUDIO_SAMPLE_RATE_HZ, blocking=True)
        return -100.0


@dataclass(frozen=True)
class Calibration:
    """Result of the speaker calibration pass."""

    ref_scale:  float            # confirmed reference gain (maps to drone at 1 m)
    unity_dbfs: float            # mic-measured dBFS at ref_scale (informational only)
    hardware:   HardwareProfile  # speaker and calibration-mic types

    @property
    def min_gain(self) -> float:
        """Minimum reliable playback gain for this speaker type."""
        return min_playback_gain(self.hardware)

    @property
    def max_reliable_distance(self) -> float:
        """Distance at which raw gain would fall below min_gain."""
        return self.ref_scale / self.min_gain

    def gain_for_distance(self, distance_m: float) -> float:
        amplitude = self.ref_scale / max(float(distance_m), PLAYBACK_REFERENCE_DISTANCE_M)
        return float(np.clip(amplitude, 0.0, 1.0))


def _print_calibration_instructions(console: Console, hardware: HardwareProfile) -> None:
    if hardware.mic == MIC_TYPE_INTERNAL:
        console.print(
            "Your [bold]built-in microphone is co-located with the laptop[/bold], so the\n"
            "measured dBFS level is informational only — it does not represent 1 m distance.\n"
            "[bold]Listen from 1 metre away from the speaker and use your ears to judge volume.[/bold]\n"
            "Set the system volume so the tone is [bold]clearly audible but not distorted[/bold].\n"
            "Press [bold]Enter[/bold] when ready."
        )
    else:
        console.print(
            "[bold]Position the external microphone exactly 1 metre from the speaker.[/bold]\n"
            "This distance is the reference for all simulated distances in the session.\n"
            "Set the system volume so the tone is [bold]clearly audible but not distorted[/bold].\n"
            "Press [bold]Enter[/bold] when ready."
        )


def calibrate(console: Console) -> Calibration:
    """Select hardware profile, then adjust speaker volume interactively."""
    hardware = select_hardware(console)

    console.print("\n[bold yellow]Step 2 — Speaker Volume Calibration[/bold yellow]")
    _print_calibration_instructions(console, hardware)
    input()

    gain       = CALIBRATION_INITIAL_GAIN
    unity_dbfs = -100.0

    while True:
        console.print(f"  [dim]Playing tone at {gain:.0%}…[/dim]")
        unity_dbfs = _play_tone(gain)
        if unity_dbfs > CALIBRATION_MIC_QUIET_DBFS:
            level_note = (
                " [dim](co-located mic — not a 1 m measurement)[/dim]"
                if hardware.mic == MIC_TYPE_INTERNAL
                else ""
            )
            console.print(f"  [dim]Mic level: {unity_dbfs:.1f} dBFS{level_note}[/dim]")

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
            if gain >= CALIBRATION_GAIN_MAX:
                console.print("  [yellow]Already at maximum. Proceeding.[/yellow]")
                break
            gain = min(CALIBRATION_GAIN_MAX, gain + CALIBRATION_GAIN_STEP)
        else:
            gain = max(CALIBRATION_GAIN_MIN, gain - CALIBRATION_GAIN_STEP)

    calib = Calibration(ref_scale=gain, unity_dbfs=unity_dbfs, hardware=hardware)
    console.print(
        f"\n[green]Calibration complete.[/green] "
        f"Reference: [cyan]{gain:.0%}[/cyan]  "
        f"Reliable range: [cyan]≤ {calib.max_reliable_distance:.0f} m[/cyan]\n"
    )
    return calib
