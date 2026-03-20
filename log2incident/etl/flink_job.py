import json
from datetime import datetime
from typing import Iterable, List

from log2incident.events.event_creator import EventCreator
from log2incident.models import Event, RawLog, TaggedLog

try:
    from pyflink.common import Types
    from pyflink.datastream import StreamExecutionEnvironment
    _PYFLINK_AVAILABLE = True
except ImportError:
    Types = None
    StreamExecutionEnvironment = None
    _PYFLINK_AVAILABLE = False


def _serialize_raw_log(log: RawLog) -> str:
    payload = {
        "id": log.id,
        "timestamp": log.timestamp.isoformat(),
        "source": log.source,
        "message": log.message,
        "metadata": log.metadata or {},
    }
    return json.dumps(payload)


def _deserialize_raw_log(payload: str) -> RawLog:
    body = json.loads(payload)
    return RawLog(
        id=body["id"],
        timestamp=datetime.fromisoformat(body["timestamp"]),
        source=body["source"],
        message=body["message"],
        metadata=body.get("metadata", {}),
    )


def _is_error_payload(payload: str) -> bool:
    lowered = payload.lower()
    return "error" in lowered or "exception" in lowered


def _filter_payloads_locally(payloads: Iterable[str]) -> List[str]:
    return [payload for payload in payloads if _is_error_payload(payload)]


def _filter_payloads_with_flink(payloads: List[str]) -> List[str]:
    if not payloads:
        return []

    env = StreamExecutionEnvironment.get_execution_environment()
    stream = env.from_collection(payloads, type_info=Types.STRING())
    filtered = stream.filter(_is_error_payload)

    iterator = filtered.execute_and_collect(limit=len(payloads))
    try:
        return list(iterator)
    finally:
        iterator.close()


def get_runtime_mode(prefer_flink: bool = True) -> str:
    if prefer_flink and _PYFLINK_AVAILABLE:
        return "pyflink"
    return "local-fallback"


def run_flink_demo(raw_logs: List[RawLog], prefer_flink: bool = True) -> List[Event]:
    """Run a minimal ETL demo and emit events for error-like logs.

    - Uses PyFlink DataStream when available and requested.
    - Falls back to local filtering for environments without PyFlink.
    """
    payloads = [_serialize_raw_log(log) for log in raw_logs]

    if get_runtime_mode(prefer_flink) == "pyflink":
        filtered_payloads = _filter_payloads_with_flink(payloads)
    else:
        filtered_payloads = _filter_payloads_locally(payloads)

    creator = EventCreator()
    events: List[Event] = []
    for payload in filtered_payloads:
        raw_log = _deserialize_raw_log(payload)
        tagged = TaggedLog(**raw_log.model_dump(), tags=["error"])
        events.append(creator.create_event(tagged))
    return events


def flink_filter(raw_logs: List[RawLog], prefer_flink: bool = True) -> List[Event]:
    """Backward-compatible entry point for the ETL filter step."""
    return run_flink_demo(raw_logs=raw_logs, prefer_flink=prefer_flink)