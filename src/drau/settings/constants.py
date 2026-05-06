"""Project-wide constants that change rarely.

Values that are operational defaults (paths, tunable thresholds, CLI defaults)
live in environment variables and are exposed via :mod:`drau.env`.
"""

# ── Audio ─────────────────────────────────────────────────────────────────────
AUDIO_SAMPLE_RATE_HZ = 16_000

# Guard value used wherever log10 of a near-zero amplitude must not blow up.
LOG_EPSILON = 1e-10

# ── Calibration ───────────────────────────────────────────────────────────────
CALIBRATION_TONE_FREQ_HZ = 1_000
CALIBRATION_TONE_DURATION_S = 2.0
# Fraction of the current gain applied to the raw sine wave (headroom margin).
CALIBRATION_TONE_AMPLITUDE = 0.7
# Seconds of recorded audio discarded at the start of each tone capture.
CALIBRATION_RECORDING_SKIP_S = 0.3
# Mic-measured dBFS below which the level readout is suppressed (probably inaudible).
CALIBRATION_MIC_QUIET_DBFS = -90.0
CALIBRATION_INITIAL_GAIN = 0.6
CALIBRATION_GAIN_STEP = 0.2
CALIBRATION_GAIN_MAX = 1.0
CALIBRATION_GAIN_MIN = 0.1
# Below this raw inverse-distance gain the distance simulation is unreliable (~−52 dBFS floor).
MIN_PLAYBACK_GAIN = 0.02

# ── Speaker types ─────────────────────────────────────────────────────────────
SPEAKER_TYPE_LAPTOP   = "laptop"    # Internal laptop / notebook speaker
SPEAKER_TYPE_PORTABLE = "portable"  # Portable or Bluetooth powered speaker
SPEAKER_TYPE_HIFI     = "hifi"      # Hi-fi / studio monitor / 5.1 system

# Minimum reliable playback gain per speaker type.
# Below this gain, noise or distortion dominates and distance simulation is meaningless.
SPEAKER_MIN_GAIN_LAPTOP   = 0.03   # Higher floor: laptop speakers distort early at low gain
SPEAKER_MIN_GAIN_PORTABLE = 0.02   # Standard floor (same as legacy MIN_PLAYBACK_GAIN)
SPEAKER_MIN_GAIN_HIFI     = 0.005  # Lower floor: clean reproduction at very low levels

# Distance above which a laptop speaker cannot reliably reproduce the low-frequency
# content that dominates real drone audio at range (bass below ~200 Hz is inaudible).
SPEAKER_LAPTOP_LF_WARNING_DISTANCE_M = 30.0

# ── Microphone types ──────────────────────────────────────────────────────────
MIC_TYPE_INTERNAL = "internal"  # Built-in laptop / co-located mic
MIC_TYPE_EXTERNAL = "external"  # Headset, wired, or standalone mic placed at 1 m

# ── Air absorption (ISO 9613-1, 20 °C, 70 % RH, outdoor) ─────────────────────
# Absorption coefficient at 4 kHz in dB per metre.
# Used to derive the first-order lowpass cutoff that matches measured attenuation.
AIR_ABSORPTION_COEFF_4KHZ_DB_PER_M = 0.028
# Below this distance the absorption-induced attenuation is < 0.5 dB even at 8 kHz —
# no filtering is applied.
AIR_ABSORPTION_MIN_DISTANCE_M = 10.0
# Minimum cutoff for the absorption filter (prevents complete silence at extreme range).
AIR_ABSORPTION_MIN_CUTOFF_HZ = 200.0
# Number of taps in the Hann-windowed sinc FIR lowpass.
AIR_ABSORPTION_FIR_TAPS = 65

# ── Playback ──────────────────────────────────────────────────────────────────
# All source audio is normalised to this RMS level before distance gain is applied.
PLAYBACK_NORM_DBFS = -18.0
# Calibration is measured at this distance; gains are scaled relative to it.
PLAYBACK_REFERENCE_DISTANCE_M = 1.0

# ── Form (terminal UI) ────────────────────────────────────────────────────────
# Distance edits smaller than this (metres) are ignored to avoid spurious replays.
FORM_MIN_DISTANCE_CHANGE_M = 0.01

# ── Feature extraction (audio analytics) ─────────────────────────────────────
FEATURE_ANALYSIS_WINDOW_S = 5        # Seconds of audio used for the spectral window
FEATURE_FRAME_SAMPLES = 512          # Frame length for per-frame silence detection
FEATURE_SILENCE_THRESHOLD_DBFS = -40.0
FEATURE_SPECTRAL_LOW_HZ = 500
FEATURE_SPECTRAL_HIGH_HZ = 4_000
# Fraction of cumulative spectral power that defines the rolloff frequency.
FEATURE_SPECTRAL_ROLLOFF_FRACTION = 0.85
FEATURE_ANALYTICS_PROGRESS_INTERVAL = 10_000  # Log extraction progress every N files

# ── Distance grading ──────────────────────────────────────────────────────────
# Fractions of max_dist used to compute the four grade-zone boundaries.
GRADE_ZONE_FRACTION_B1 = 0.20
GRADE_ZONE_FRACTION_B2 = 0.33
GRADE_ZONE_FRACTION_B3 = 0.67

# Distance thresholds for the _nice() rounding function in metrics.
# Below each threshold the corresponding rounding granularity is applied.
GRADE_NICE_THRESHOLD_FINE   = 5    # Round to nearest metre
GRADE_NICE_THRESHOLD_MEDIUM = 20   # Round to nearest 5 m
GRADE_NICE_THRESHOLD_LARGE  = 100  # Round to nearest 10 m
GRADE_NICE_THRESHOLD_XLARGE = 500  # Round to nearest 25 m

# ── Interpretation thresholds (detection report) ──────────────────────────────
INTERP_STRONG_ACCURACY_MIN   = 0.85
INTERP_STRONG_RECALL_MIN     = 0.80
INTERP_STRONG_FPR_MAX        = 0.20
INTERP_MODERATE_ACCURACY_MIN = 0.70
# Grade-to-grade accuracy change below this magnitude is considered "stable".
INTERP_STABLE_GRADE_DELTA    = 0.10
# Minimum accuracy for a distance grade to be labelled "reliable".
INTERP_RELIABLE_ACCURACY_MIN = 0.70
# FPR / FNR above this is described as "high" in the interpretation text.
INTERP_HIGH_ERROR_RATE       = 0.30

# ── Display / reporting ───────────────────────────────────────────────────────
DISPLAY_BAR_WIDTH          = 22
REPORT_WIDTH_ANALYTICS     = 72   # Character width of the audio-analytics text report
REPORT_WIDTH_DETECTION     = 62   # Character width of the detection-test text report

# ── Plots ─────────────────────────────────────────────────────────────────────
PLOT_DPI = 120
PLOT_MIC_COLORS = ["#2ecc71", "#3498db", "#9b59b6", "#e74c3c", "#f39c12", "#1abc9c"]
PLOT_GRID_ALPHA = 0.3
# Use white text in a confusion-matrix cell when its value exceeds this fraction of the cell maximum.
PLOT_CONFUSION_COLOR_THRESHOLD = 0.55
# Y-axis ceiling for the metrics-overview bar chart (slightly above 1.0 for label headroom).
PLOT_METRICS_YLIM_MAX = 1.12
# Bottom rect margin for the distance-performance plot — reserves space for the caption.
PLOT_DISTANCE_CAPTION_BOTTOM = 0.13
# Bottom rect margin for the by-class performance plot.
PLOT_CLASS_CAPTION_BOTTOM = 0.02
