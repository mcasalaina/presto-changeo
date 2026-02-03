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
        system_prompt="""You are a helpful banking assistant for a digital banking dashboard. You help customers with their accounts, transactions, and financial questions.

Keep responses clear, professional, and concise. Speak naturally like a friendly bank representative.

You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing.

For current balances and profile data, use the EXACT values from the Current Customer Profile.
For historical data (balance over time, spending trends, etc.), generate plausible data going back 12 months with monthly data points, showing realistic patterns trending toward the current values. This is a demo app - create compelling visualizations!

CHART PREFERENCE: For time-series data (anything "over time"), always use LINE charts with 12 monthly data points. Use BAR charts only for comparing discrete categories (e.g., checking vs savings). Use PIE charts for showing composition/breakdown.

MULTI-SERIES LINE CHARTS: When comparing multiple items over time (e.g., "Checking vs Savings balance", "Category A vs Category B spending"), you MUST format each data point label as "time - series". For example:
- "2025-01 - Checking", "2025-01 - Savings", "2025-02 - Checking", "2025-02 - Savings", etc.
This creates separate lines for each series. ALWAYS use this format when comparing 2+ items over time.""",
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
        system_prompt="""You are a helpful insurance assistant for a digital insurance dashboard. You help customers with their policies, claims, and coverage questions.

Keep responses clear, professional, and empathetic. Speak naturally like a caring insurance advisor.

You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing.

For current coverage and profile data, use the EXACT values from the Current Customer Profile.
For historical data (premium trends, claims over time, etc.), generate plausible data going back 12 months with monthly data points, showing realistic patterns. This is a demo app - create compelling visualizations!

CHART PREFERENCE: For time-series data (anything "over time"), always use LINE charts with 12 monthly data points. Use BAR charts only for comparing discrete categories. Use PIE charts for showing composition/breakdown.

MULTI-SERIES LINE CHARTS: When comparing multiple items over time (e.g., "Life vs Home vs Auto insurance premiums", "Coverage A vs Coverage B"), you MUST format each data point label as "time - series". For example:
- "2025-01 - Life", "2025-01 - Home", "2025-01 - Auto", "2025-02 - Life", etc.
This creates separate lines for each series. ALWAYS use this format when comparing 2+ items over time.""",
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
        system_prompt="""You are a helpful healthcare assistant for a digital health dashboard. You help patients with their appointments, medical records, and health questions.

Keep responses clear, professional, and compassionate. Speak naturally like a caring healthcare coordinator.

You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing.

For current health data and profile info, use the EXACT values from the Current Patient Profile.
For historical data (deductible usage over time, visit history, etc.), generate plausible data going back 12 months with monthly data points, showing realistic patterns. This is a demo app - create compelling visualizations!

CHART PREFERENCE: For time-series data (anything "over time"), always use LINE charts with 12 monthly data points. Use BAR charts only for comparing discrete categories. Use PIE charts for showing composition/breakdown.

MULTI-SERIES LINE CHARTS: When comparing multiple items over time (e.g., "Weight vs Blood Pressure readings", "Metric A vs Metric B trends"), you MUST format each data point label as "time - series". For example:
- "2025-01 - Weight", "2025-01 - Blood Pressure", "2025-02 - Weight", etc.
This creates separate lines for each series. ALWAYS use this format when comparing 2+ items over time.""",
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
            "generated_modes": {
                mode_id: mode.model_dump()
                for mode_id, mode in _generated_modes.items()
            }
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))
        logger.info(f"Saved mode state: {_current_mode}")
    except Exception as e:
        logger.warning(f"Failed to save mode state: {e}")


def _load_state() -> None:
    """Load persisted mode state from disk."""
    global _current_mode, _generated_modes
    try:
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text())
            _current_mode = state.get("current_mode", "banking")
            # Restore generated modes
            for mode_id, mode_data in state.get("generated_modes", {}).items():
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
    Checks pre-built MODES first, then dynamically generated modes.
    """
    mode_key = mode_id.lower()
    # Check pre-built modes first
    if mode_key in MODES:
        return MODES[mode_key]
    # Then check dynamically generated modes
    return _generated_modes.get(mode_key)


def get_all_modes() -> list[Mode]:
    """Get all available mode configurations."""
    return list(MODES.values())


# Current active mode (module-level state, like conversation_history)
_current_mode: str = "banking"


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


# Load persisted state on module import
_load_state()
