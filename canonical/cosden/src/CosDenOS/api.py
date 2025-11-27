from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from . import CosDenOS
from .ai_planner import CosmeticPlannerAgent
from .user_profile import CosmeticUserProfile
from .errors import CosDenError
from .api_models import (
    PlanRequest,
    PlanResponse,
    SimulateRequest,
    SimulateResponse,
    SimulationData,
    SimulationEffect,
    InterpretedGoal,
)
from .logging_utils import log_event
from .stegcore_integration import (
    initialize_stegcore_integration,
    send_stegcore_heartbeat,
)


# -------------------------
# StegCore integration config
# -------------------------

COSDEN_NODE_NAME = os.getenv("COSDEN_NODE_NAME", "CosDenOS")
COSDEN_VERSION = os.getenv("COSDEN_VERSION", "0.1.0")
COSDEN_PUBLIC_ENDPOINT = os.getenv("COSDEN_PUBLIC_ENDPOINT", "")


# -------------------------
# App + engine initialization
# -------------------------

app = FastAPI(
    title="CosDenOS Cosmetic Engine API",
    version=COSDEN_VERSION,
    description=(
        "CosDenOS cosmetic-only engine + StegVerse AI Cosmetic Planner.\n\n"
        "Important: This API is cosmetic-only and does not diagnose, treat, "
        "or prevent any disease or condition."
    ),
)

_engine = CosDenOS()
_engine.load_default_catalog()

# Planner with no external LLM client yet (rule-based interpretation).
_planner = CosmeticPlannerAgent(engine=_engine, llm_client=None)

# Initialize StegCore integration (no-op if stegcore is not installed).
initialize_stegcore_integration(
    node_name=COSDEN_NODE_NAME,
    version=COSDEN_VERSION,
    endpoint=COSDEN_PUBLIC_ENDPOINT or None,
)


# -------------------------
# Health check
# -------------------------

@app.get("/health")
def health() -> dict:
    """
    Simple health endpoint to verify the service is up.
    Also sends a heartbeat to StegCore if integration is available.
    """
    log_event("health_check", extra={"endpoint": "/health"})

    # Heartbeat into StegCore, if enabled.
    send_stegcore_heartbeat(
        version=COSDEN_VERSION,
        endpoint=COSDEN_PUBLIC_ENDPOINT or None,
    )

    return {
        "status": "ok",
        "engine_twin_loaded": _engine.twin_loaded,
        "cosmetic_only": True,
        "node": COSDEN_NODE_NAME,
        "version": COSDEN_VERSION,
    }


# -------------------------
# /plan endpoint
# -------------------------

@app.post("/plan", response_model=PlanResponse)
def plan_cosmetic_stack(payload: PlanRequest):
    """
    High-level AI Cosmetic Planner endpoint.

    - Interprets a user's natural language request
    - Recommends a cosmetic stack for that user
    - Simulates the cosmetic effect
    """
    log_event(
        "plan_request",
        extra={
            "endpoint": "/plan",
            "age_years": payload.user.age_years,
        },
    )

    try:
        user_info = payload.user

        user_profile = CosmeticUserProfile.from_age(
            age_years=user_info.age_years,
            tone_preference=user_info.tone_preference,
            sensitivity_flag=user_info.sensitivity_flag,
            event_time_hours=user_info.event_time_hours,
            notes=user_info.notes,
        )

        plan_dict = _planner.plan_for_request(
            user=user_profile,
            request_text=payload.request_text,
        )

        # Extract and normalize simulation section into pydantic model
        sim = plan_dict["simulation"]
        agg = sim["aggregated_effect"]

        simulation = SimulationData(
            stack_codes=sim["stack_codes"],
            aggregated_effect=SimulationEffect(
                brightness_delta=agg["brightness_delta"],
                gloss_delta=agg["gloss_delta"],
                tone_shift=agg["tone_shift"],
                opalescence_delta=agg["opalescence_delta"],
            ),
            notes=sim["notes"],
            cosmetic_only=sim["cosmetic_only"],
        )

        goal = plan_dict["interpreted_goal"]

        return PlanResponse(
            version=plan_dict["version"],
            cosmetic_only=plan_dict["cosmetic_only"],
            raw_request=plan_dict["raw_request"],
            user=plan_dict["user"],
            interpreted_goal=InterpretedGoal(
                goal_type=goal["goal_type"],
                tone_preference=goal["tone_preference"],
                max_steps=goal["max_steps"],
                target_event_hours=goal["target_event_hours"],
            ),
            recommended_stack=plan_dict["recommended_stack"],
            simulation=simulation,
            legal_disclaimer=plan_dict["legal_disclaimer"],
        )

    except CosDenError as exc:
        # Known CosDenOS errors → 400-series to the caller
        log_event(
            "plan_request_error",
            level="WARN",
            extra={
                "endpoint": "/plan",
                "error": str(exc),
                "age_years": payload.user.age_years,
            },
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:  # pragma: no cover - generic guardrail
        log_event(
            "plan_request_error_internal",
            level="ERROR",
            extra={
                "endpoint": "/plan",
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# -------------------------
# /simulate endpoint
# -------------------------

@app.post("/simulate", response_model=SimulateResponse)
def simulate_stack(payload: SimulateRequest):
    """
    Lower-level endpoint: directly simulate a given product code stack
    for a user, without natural-language planning.
    """
    log_event(
        "simulate_request",
        extra={
            "endpoint": "/simulate",
            "age_years": payload.user.age_years,
            "codes": payload.codes,
        },
    )

    try:
        user_info = payload.user

        user_profile = CosmeticUserProfile.from_age(
            age_years=user_info.age_years,
            tone_preference=user_info.tone_preference,
            sensitivity_flag=user_info.sensitivity_flag,
            event_time_hours=user_info.event_time_hours,
            notes=user_info.notes,
        )

        # Build stack from product codes
        stack = _engine.build_stack(payload.codes)

        # Simulate cosmetic-only effect
        sim_result = _engine.simulate_stack(
            stack=stack,
            age_profile=user_profile.age_profile,
            age_years=user_profile.age_years,
        )

        agg = sim_result.aggregated_effect

        simulation = SimulationData(
            stack_codes=sim_result.stack_codes,
            aggregated_effect=SimulationEffect(
                brightness_delta=agg.brightness_delta,
                gloss_delta=agg.gloss_delta,
                tone_shift=agg.tone_shift,
                opalescence_delta=agg.opalescence_delta,
            ),
            notes=sim_result.notes,
            cosmetic_only=sim_result.cosmetic_only,
        )

        return SimulateResponse(
            cosmetic_only=True,
            simulation=simulation,
        )

    except CosDenError as exc:
        log_event(
            "simulate_request_error",
            level="WARN",
            extra={
                "endpoint": "/simulate",
                "error": str(exc),
                "age_years": payload.user.age_years,
                "codes": payload.codes,
            },
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:  # pragma: no cover
        log_event(
            "simulate_request_error_internal",
            level="ERROR",
            extra={
                "endpoint": "/simulate",
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
