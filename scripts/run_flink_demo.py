#!/usr/bin/env python3

from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log2incident.etl.flink_job import get_runtime_mode, run_flink_demo
from log2incident.models import RawLog


def main() -> None:
    sample_logs = [
        RawLog(
            id="flink-demo-1",
            timestamp=datetime.utcnow(),
            source="demo-app",
            message="INFO: started",
            metadata={"env": "local"},
        ),
        RawLog(
            id="flink-demo-2",
            timestamp=datetime.utcnow(),
            source="demo-app",
            message="ERROR: database timeout",
            metadata={"env": "local"},
        ),
    ]

    mode = get_runtime_mode(prefer_flink=True)
    events = run_flink_demo(sample_logs, prefer_flink=True)

    print(f"ETL mode: {mode}")
    print(f"Input logs: {len(sample_logs)}")
    print(f"Generated events: {len(events)}")
    for event in events:
        print(f"- {event.id} | severity={event.severity} | log_id={event.log_id}")


if __name__ == "__main__":
    main()
