from log2incident.models import Event, Incident
from collections import defaultdict
import uuid
from datetime import datetime

class IncidentManager:
    def __init__(self):
        self.incidents = []
        self.event_counts = defaultdict(int)

    def process_event(self, event: Event):
        self.event_counts[event.log_id] += 1

        # Instant incident if severity high
        if event.severity == 'high':
            incident = Incident(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                events=[event.id],
                status='open',
                summary=f"Instant incident from event: {event.description}"
            )
            self.incidents.append(incident)
        # Accumulated: if 3 events from same log
        elif self.event_counts[event.log_id] >= 3:
            # Create accumulated incident
            incident = Incident(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                events=[event.id],  # In real, collect all
                status='open',
                summary=f"Accumulated incident from log {event.log_id}"
            )
            self.incidents.append(incident)