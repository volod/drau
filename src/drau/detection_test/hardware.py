"""Hardware profile: speaker and calibration-microphone type selection.

The profile is collected once before calibration and stored on the
:class:`~drau.detection_test.calibrate.Calibration` object.  It drives:

* the minimum reliable playback gain (and therefore ``max_reliable_distance``),
* low-frequency reproduction warnings for laptop speakers at range,
* calibration instructions tailored to the microphone placement.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.prompt import Prompt

from drau.settings.constants import (
    MIC_TYPE_EXTERNAL,
    MIC_TYPE_INTERNAL,
    SPEAKER_MIN_GAIN_HIFI,
    SPEAKER_MIN_GAIN_LAPTOP,
    SPEAKER_MIN_GAIN_PORTABLE,
    SPEAKER_TYPE_HIFI,
    SPEAKER_TYPE_LAPTOP,
    SPEAKER_TYPE_PORTABLE,
)

_SPEAKER_MIN_GAIN: dict[str, float] = {
    SPEAKER_TYPE_LAPTOP:   SPEAKER_MIN_GAIN_LAPTOP,
    SPEAKER_TYPE_PORTABLE: SPEAKER_MIN_GAIN_PORTABLE,
    SPEAKER_TYPE_HIFI:     SPEAKER_MIN_GAIN_HIFI,
}


@dataclass(frozen=True)
class HardwareProfile:
    """Speaker and calibration-microphone types chosen by the operator."""

    speaker: str  # one of SPEAKER_TYPE_*
    mic: str      # one of MIC_TYPE_*


def min_playback_gain(hardware: HardwareProfile) -> float:
    """Return the minimum reliable playback gain for this hardware profile."""
    return _SPEAKER_MIN_GAIN.get(hardware.speaker, SPEAKER_MIN_GAIN_PORTABLE)


def select_hardware(console: Console) -> HardwareProfile:
    """Interactively identify the playback speaker and calibration microphone."""
    console.print("\n[bold]Step 1 — Hardware Setup[/bold]")
    console.print(
        "Identifying your hardware lets the simulator set the right volume floor\n"
        "and display accurate warnings about simulation accuracy.\n"
    )

    console.print("[dim]Speaker connected to this computer:[/dim]")
    console.print(
        "  [bold]l[/bold]  Laptop / notebook built-in speaker\n"
        "  [bold]p[/bold]  Portable or Bluetooth powered speaker\n"
        "  [bold]h[/bold]  Hi-fi, studio monitor, or 5.1 system\n"
    )
    s = Prompt.ask("  Speaker", choices=["l", "p", "h"], default="l", console=console)
    speaker = {
        "l": SPEAKER_TYPE_LAPTOP,
        "p": SPEAKER_TYPE_PORTABLE,
        "h": SPEAKER_TYPE_HIFI,
    }[s]

    console.print(
        "\n[dim]Microphone used to measure tone level during the next calibration step:[/dim]"
    )
    console.print(
        "  [bold]i[/bold]  Internal / built-in laptop mic\n"
        "  [bold]e[/bold]  External mic (headset, wired, or standalone on a stand)\n"
    )
    m = Prompt.ask("  Microphone", choices=["i", "e"], default="i", console=console)
    mic = MIC_TYPE_INTERNAL if m == "i" else MIC_TYPE_EXTERNAL

    return HardwareProfile(speaker=speaker, mic=mic)
