#!/usr/bin/env python3

from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from log2incident.models import RawLog
from log2incident.etl.flink_aggregation import run_stateful_aggregation


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


    # Convert RawLog objects to dicts for PyFlink
    log_dicts = [log.dict() for log in sample_logs]
    print("Running stateful aggregation (error count per source)...")
    run_stateful_aggregation(log_dicts)
    print("Results are printed by Flink job above.")


if __name__ == "__main__":
    main()
