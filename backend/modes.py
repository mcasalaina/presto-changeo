"""
Mode Configuration Models
Pydantic models for mode definitions that control industry theming and AI behavior.
"""
import json
import logging
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# State file for persisting mode across restarts
STATE_FILE = Path(__file__).parent / ".mode_state.json"


class ModeTheme(BaseModel):
    primary: str
    secondary: str
    background: str
    surface: str
    text: str
    text_muted: str


class ModeTab(BaseModel):
    id: str
    label: str
    icon: str


class ModeMetric(BaseModel):
    label: str
    value: str | int | float
    unit: str | None = None


class Mode(BaseModel):
    id: str
    name: str
    company_name: str  # Fake company name for branding
    tagline: str  # Company tagline for welcome area
    theme: ModeTheme
    tabs: list[ModeTab]
    system_prompt: str
    default_metrics: list[ModeMetric]
    background_image: str | None = None
    hero_image: str | None = None
    chat_image: str | None = None


# Pre-built mode configurations
MODES: dict[str, Mode] = {
    "banking": Mode(
        id="banking",
        name="Banking",
        company_name="Meridian Trust Bank",
        tagline="Your trusted financial partner since 1952",
        theme=ModeTheme(
            primary="#1E88E5",      # Blue - trust, stability
            secondary="#43A047",    # Green - money, growth
            background="#f8fafc",
            surface="#ffffff",
            text="#0f172a",
            text_muted="#64748b"
        ),
        tabs=[
            ModeTab(id="dashboard", label="Dashboard", icon="📊"),
            ModeTab(id="accounts", label="Accounts", icon="💳"),
            ModeTab(id="transfers", label="Transfers", icon="💸"),
            ModeTab(id="payments", label="Payments", icon="📋"),
            ModeTab(id="settings", label="Settings", icon="⚙️"),
        ],
        system_prompt="""You are a banking assistant at Meridian Trust Bank.

RESPONSE RULES - FOLLOW EXACTLY:
1. Be BRIEF. One sentence max when showing a chart. Example: "Here's your balance trend."
2. NEVER say "I don't have data", "sample", "demo", "hypothetical", "simulated", "for demonstration", or similar. The data IS real.
3. NEVER ask if they want to adjust or dive deeper. Just show the chart.
4. NEVER explain what you're about to do. Just do it.

TOOLS: show_chart (line, bar, pie, area) and show_metrics.

DATA RULES:
- Use the EXACT balance from Current Customer Profile for the most recent month.
- Historical data trends toward current values (e.g., $22K → $23K → $24K → current $24,856).
- NEVER show zero values.

CHARTS: LINE for time-series. Format multi-series as "2025-01 - Checking", "2025-01 - Savings".""",
        default_metrics=[
            ModeMetric(label="Account Balance", value="$24,856.42"),
            ModeMetric(label="Recent Transactions", value=12),
            ModeMetric(label="Pending Payments", value=3),
            ModeMetric(label="Credit Score", value=742),
        ]
    ),
    "insurance": Mode(
        id="insurance",
        name="Insurance",
        company_name="Guardian Shield Insurance",
        tagline="Protecting what matters most",
        theme=ModeTheme(
            primary="#7B1FA2",      # Purple - protection, premium
            secondary="#00897B",    # Teal - calm, trust
            background="#faf5ff",
            surface="#ffffff",
            text="#1e1b4b",
            text_muted="#6b7280"
        ),
        tabs=[
            ModeTab(id="dashboard", label="Dashboard", icon="📊"),
            ModeTab(id="policies", label="Policies", icon="📄"),
            ModeTab(id="claims", label="Claims", icon="📝"),
            ModeTab(id="coverage", label="Coverage", icon="🛡️"),
            ModeTab(id="settings", label="Settings", icon="⚙️"),
        ],
        system_prompt="""You are an insurance assistant at Guardian Shield Insurance.

RESPONSE RULES - FOLLOW EXACTLY:
1. Be BRIEF. One sentence max when showing a chart. Example: "Here's your coverage breakdown."
2. NEVER say "I don't have data", "sample", "demo", "hypothetical", "simulated", or similar. The data IS real.
3. NEVER ask if they want to adjust or dive deeper. Just show the chart.
4. NEVER explain what you're about to do. Just do it.

TOOLS: show_chart (line, bar, pie, area) and show_metrics.

DATA RULES:
- Use EXACT values from Current Customer Profile.
- Historical data uses realistic values matching the profile scale.
- NEVER show zero values.

CHARTS: LINE for time-series. Format multi-series as "2025-01 - Life", "2025-01 - Auto".""",
        default_metrics=[
            ModeMetric(label="Active Policies", value=3),
            ModeMetric(label="Total Coverage", value="$750,000"),
            ModeMetric(label="Pending Claims", value=1),
            ModeMetric(label="Next Premium", value="$245", unit="/mo"),
        ]
    ),
    "healthcare": Mode(
        id="healthcare",
        name="Healthcare",
        company_name="Vitality Health Partners",
        tagline="Your health, our priority",
        theme=ModeTheme(
            primary="#00ACC1",      # Cyan - clean, medical
            secondary="#E53935",    # Red - health, urgency
            background="#f0fdfa",
            surface="#ffffff",
            text="#134e4a",
            text_muted="#64748b"
        ),
        tabs=[
            ModeTab(id="dashboard", label="Dashboard", icon="📊"),
            ModeTab(id="appointments", label="Appointments", icon="📅"),
            ModeTab(id="records", label="Records", icon="📋"),
            ModeTab(id="prescriptions", label="Prescriptions", icon="💊"),
            ModeTab(id="settings", label="Settings", icon="⚙️"),
        ],
        system_prompt="""You are a healthcare assistant at Vitality Health Partners.

RESPONSE RULES - FOLLOW EXACTLY:
1. Be BRIEF. One sentence max when showing a chart. Example: "Here's your deductible usage this year."
2. NEVER say "I don't have data", "sample", "demo", "hypothetical", "simulated", or similar. The data IS real.
3. NEVER ask if they want to adjust or dive deeper. Just show the chart.
4. NEVER explain what you're about to do. Just do it.

TOOLS: show_chart (line, bar, pie, area) and show_metrics.

DATA RULES:
- Use EXACT values from Current Patient Profile.
- Historical data uses realistic values matching the profile scale.
- NEVER show zero values.

CHARTS: LINE for time-series. Format multi-series as "2025-01 - Weight", "2025-01 - BP".""",
        default_metrics=[
            ModeMetric(label="Upcoming Appointments", value=2),
            ModeMetric(label="Active Prescriptions", value=4),
            ModeMetric(label="Deductible Met", value="68%"),
            ModeMetric(label="Out-of-Pocket", value="$1,240"),
        ]
    ),
}


# Storage for dynamically generated modes (session-level cache)
_generated_modes: dict[str, Mode] = {}


def _save_state() -> None:
    """Persist current mode and generated modes to disk."""
    try:
        state = {
            "current_mode": _current_mode,
            "voice_preference": _voice_preference,
            "generated_modes": {
                mode_id: mode.model_dump()
                for mode_id, mode in _generated_modes.items()
            }
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))
        logger.info(f"Saved mode state: {_current_mode}")
    except Exception as e:
        logger.warning(f"Failed to save mode state: {e}")


def _sanitize_presto(text: str) -> str:
    """Remove any variation of 'presto' from text - it's a trigger word, not a company name."""
    import re
    patterns = [
        r'\bpresto[-\s]?change[-\s]?o\b',
        r'\bpresto[-\s]?changer\b',
        r'\bpresto\b',
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', result).strip()


def _load_state() -> None:
    """Load persisted mode state from disk."""
    global _current_mode, _generated_modes, _voice_preference
    try:
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text())
            _current_mode = state.get("current_mode", "banking")
            loaded_voice = state.get("voice_preference", "verse")
            if loaded_voice in AVAILABLE_VOICES:
                _voice_preference = loaded_voice
            # Restore generated modes, sanitizing company names
            for mode_id, mode_data in state.get("generated_modes", {}).items():
                # CRITICAL: Strip "presto" from any company names on load
                if 'company_name' in mode_data:
                    original = mode_data['company_name']
                    mode_data['company_name'] = _sanitize_presto(original)
                    if len(mode_data['company_name']) < 3:
                        mode_data['company_name'] = f"{mode_data.get('name', 'Business')} Co."
                    if mode_data['company_name'] != original:
                        logger.warning(f"Sanitized loaded company_name: '{original}' -> '{mode_data['company_name']}'")
                _generated_modes[mode_id] = Mode(**mode_data)
            logger.info(f"Restored mode state: {_current_mode} ({len(_generated_modes)} generated modes)")
    except Exception as e:
        logger.warning(f"Failed to load mode state: {e}")
        _current_mode = "banking"


def store_generated_mode(mode: Mode) -> None:
    """Store a dynamically generated mode for session reuse."""
    _generated_modes[mode.id] = mode
    _save_state()


def get_generated_mode(mode_id: str) -> Mode | None:
    """Get a dynamically generated mode by ID, or None if not found."""
    return _generated_modes.get(mode_id.lower())


def get_mode(mode_id: str) -> Mode | None:
    """
    Get a mode configuration by ID.
    Checks dynamically generated modes first (user customizations take priority),
    then falls back to pre-built MODES.
    """
    mode_key = mode_id.lower()
    # Check dynamically generated modes first (user customizations shadow pre-built)
    generated = _generated_modes.get(mode_key)
    if generated:
        return generated
    # Then check pre-built modes
    if mode_key in MODES:
        return MODES[mode_key]
    return None


def get_all_modes() -> list[Mode]:
    """Get all available mode configurations."""
    return list(MODES.values())


# Current active mode (module-level state, like conversation_history)
_current_mode: str = "banking"

# Voice preference
AVAILABLE_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]
_voice_preference: str = "verse"


def get_current_mode() -> Mode:
    """Get the current active mode."""
    # Use get_mode to check both pre-built and dynamically generated modes
    mode = get_mode(_current_mode)
    if mode:
        return mode
    # Fallback to banking if current mode not found
    return MODES["banking"]


def set_current_mode(mode_id: str) -> Mode | None:
    """Set the current active mode. Returns the mode if valid, None if not found."""
    global _current_mode
    mode = get_mode(mode_id)
    if mode:
        _current_mode = mode_id.lower()
        _save_state()
        return mode
    return None


def get_voice_preference() -> str:
    """Get the current voice preference."""
    return _voice_preference


def set_voice_preference(voice: str) -> bool:
    """Set the voice preference. Returns True if valid, False otherwise."""
    global _voice_preference
    if voice in AVAILABLE_VOICES:
        _voice_preference = voice
        _save_state()
        return True
    return False


# Load persisted state on module import
_load_state()
