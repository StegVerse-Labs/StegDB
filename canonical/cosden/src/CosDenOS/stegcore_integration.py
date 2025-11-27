from __future__ import annotations

from typing import Optional, Dict, Any

from .logging_utils import log_event

try:
    # StegCore must be installed as a Python package for this to succeed.
    # If not installed, integration becomes a no-op (CosDenOS still works).
    from stegcore import StateEngine, Registry  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    StateEngine = None  # type: ignore[assignment]
    Registry = None  # type: ignore[assignment]


_engine = None
_registry = None
_node_name: Optional[str] = None


def _ensure_engine_and_registry() -> None:
    """
    Lazily initialize the in-process StegCore StateEngine and Registry,
    if the stegcore package is available.
    """
    global _engine, _registry
    if StateEngine is None or Registry is None:
        return
    if _engine is None:
        _engine = StateEngine()
        _registry = Registry(engine=_engine)


def initialize_stegcore_integration(
    node_name: str,
    version: Optional[str],
    endpoint: Optional[str],
) -> None:
    """
    Initialize StegCore integration for this CosDenOS instance.

    - If stegcore is not installed, logs an 'unavailable' event and returns.
    - Otherwise, creates an in-process StateEngine + Registry and registers
      this node as 'healthy'.
    """
    global _node_name
    _node_name = node_name

    if StateEngine is None or Registry is None:
        log_event(
            "stegcore_unavailable",
            level="WARN",
            extra={"node": node_name},
        )
        return

    _ensure_engine_and_registry()

    if _registry is None:
        log_event(
            "stegcore_registry_init_failed",
            level="ERROR",
            extra={"node": node_name},
        )
        return

    metadata: Dict[str, Any] = {}
    if endpoint:
        metadata["endpoint"] = endpoint
    if version:
        metadata["version"] = version

    _registry.register(
        node=node_name,
        version=version,
        metadata=metadata,
    )

    log_event(
        "stegcore_register",
        extra={
            "node": node_name,
            "version": version,
            "endpoint": endpoint,
        },
    )


def send_stegcore_heartbeat(
    version: Optional[str],
    endpoint: Optional[str],
) -> None:
    """
    Send a heartbeat to StegCore for this CosDenOS node, if integration
    is available and initialized.
    """
    if _registry is None or _node_name is None:
        return

    metadata: Dict[str, Any] = {}
    if endpoint:
        metadata["endpoint"] = endpoint
    if version:
        metadata["version"] = version

    _registry.heartbeat(
        node=_node_name,
        version=version,
        metadata=metadata,
    )

    log_event(
        "stegcore_heartbeat",
        extra={
            "node": _node_name,
            "version": version,
            "endpoint": endpoint,
        },
    )
