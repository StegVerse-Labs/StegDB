from __future__ import annotations

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from .age import AgeGroup


# ---------- Shared models ----------

class UserInfo(BaseModel):
    """Minimal cosmetic user info for the API."""
    age_years: int = Field(..., ge=1, description="User age in years")
    tone_preference: Optional[str] = Field(
        None,
        description="Optional tone preference: 'cool', 'warm', 'neutral'"
    )
    sensitivity_flag: bool = Field(
        False,
        description="If True, planner biases to gentler stacks"
    )
    event_time_hours: Optional[int] = Field(
        None,
        description="Hours until the event (for event-focused plans)"
    )
    notes: Optional[str] = Field(
        None,
        description="Optional cosmetic-only notes (e.g. 'coffee drinker')"
    )


# ---------- /plan request & response ----------

class PlanRequest(BaseModel):
    """
    Request body for /plan endpoint:
      - user: cosmetic profile
      - request_text: natural language request from the user
    """
    user: UserInfo
    request_text: str = Field(
        ...,
        description="Free-text description of cosmetic goal, e.g. 'big event tomorrow, want cool white'"
    )


class ProductSummary(BaseModel):
    code: str
    name: str
    series: str
    intensity_level: int
    description: str


class InterpretedGoal(BaseModel):
    goal_type: str
    tone_preference: Optional[str]
    max_steps: int
    target_event_hours: Optional[int]


class SimulationEffect(BaseModel):
    brightness_delta: float
    gloss_delta: float
    tone_shift: Optional[str]
    opalescence_delta: float


class SimulationData(BaseModel):
    stack_codes: List[str]
    aggregated_effect: SimulationEffect
    notes: List[str]
    cosmetic_only: bool


class PlanResponse(BaseModel):
    """
    Response body for /plan endpoint.

    This mirrors the dict returned by CosmeticPlannerAgent.plan_for_request().
    """
    version: str
    cosmetic_only: bool
    raw_request: str
    user: Dict[str, Any]
    interpreted_goal: InterpretedGoal
    recommended_stack: Dict[str, Any]
    simulation: SimulationData
    legal_disclaimer: str


# ---------- /simulate request & response ----------

class SimulateRequest(BaseModel):
    """
    Request body for /simulate endpoint.

    - user: age, tone, etc. (tone not heavily used here yet, but kept for symmetry).
    - codes: product codes like ["A1", "C1", "E1"].
    """
    user: UserInfo
    codes: List[str] = Field(
        ...,
        description="List of CosDen product codes (e.g. ['A1', 'C1', 'E1'])"
    )


class SimulateResponse(BaseModel):
    cosmetic_only: bool
    simulation: SimulationData
