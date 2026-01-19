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
