"""
Mode Configuration Models
Pydantic models for mode definitions that control industry theming and AI behavior.
"""

from pydantic import BaseModel


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
    theme: ModeTheme
    tabs: list[ModeTab]
    system_prompt: str
    default_metrics: list[ModeMetric]


# Pre-built mode configurations
MODES: dict[str, Mode] = {
    "banking": Mode(
        id="banking",
        name="Banking",
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

CRITICAL: When showing customer data in charts or responses, use ONLY the exact values from the Current Customer Profile. Never invent or approximate numbers.""",
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

CRITICAL: When showing customer data in charts or responses, use ONLY the exact values from the Current Customer Profile. Never invent or approximate numbers.""",
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

CRITICAL: When showing patient data in charts or responses, use ONLY the exact values from the Current Patient Profile. Never invent or approximate numbers.""",
        default_metrics=[
            ModeMetric(label="Upcoming Appointments", value=2),
            ModeMetric(label="Active Prescriptions", value=4),
            ModeMetric(label="Deductible Met", value="68%"),
            ModeMetric(label="Out-of-Pocket", value="$1,240"),
        ]
    ),
}


def get_mode(mode_id: str) -> Mode | None:
    """Get a mode configuration by ID."""
    return MODES.get(mode_id.lower())


def get_all_modes() -> list[Mode]:
    """Get all available mode configurations."""
    return list(MODES.values())


# Current active mode (module-level state, like conversation_history)
_current_mode: str = "banking"


def get_current_mode() -> Mode:
    """Get the current active mode."""
    return MODES[_current_mode]


def set_current_mode(mode_id: str) -> Mode | None:
    """Set the current active mode. Returns the mode if valid, None if not found."""
    global _current_mode
    mode = get_mode(mode_id)
    if mode:
        _current_mode = mode_id.lower()
        return mode
    return None
