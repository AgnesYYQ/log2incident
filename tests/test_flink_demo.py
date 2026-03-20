from datetime import datetime

from log2incident.etl.flink_job import get_runtime_mode, run_flink_demo
from log2incident.models import RawLog


def test_run_flink_demo_local_fallback_filters_error_logs():
    logs = [
        RawLog(id="1", timestamp=datetime.now(), source="svc", message="INFO: all good"),
        RawLog(id="2", timestamp=datetime.now(), source="svc", message="ERROR: failure"),
        RawLog(id="3", timestamp=datetime.now(), source="svc", message="Exception occurred"),
    ]

    events = run_flink_demo(logs, prefer_flink=False)

    assert len(events) == 2
    assert {event.log_id for event in events} == {"2", "3"}
    assert all(event.severity == "high" for event in events)


def test_get_runtime_mode_returns_known_mode():
    mode = get_runtime_mode(prefer_flink=True)
    assert mode in {"pyflink", "local-fallback"}
