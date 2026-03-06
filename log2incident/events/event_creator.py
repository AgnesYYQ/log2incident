from log2incident.models import TaggedLog, Event
from datetime import datetime
import uuid

class EventCreator:
    def create_event(self, log: TaggedLog) -> Event:
        return Event(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            log_id=log.id,
            type='log_event',
            severity='high' if 'error' in log.tags else 'medium',
            description=f"Event from log: {log.message}"
        )