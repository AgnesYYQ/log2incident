from log2incident.models import RawLog, TaggedLog

class Tagger:
    def __init__(self):
        # Placeholder for model, e.g., ML model
        self.rules = {
            'error': ['ERROR', 'Exception'],
            'warning': ['WARN', 'WARNING'],
            'info': ['INFO']
        }

    def tag_log(self, log: RawLog) -> TaggedLog:
        tags = []
        for tag, keywords in self.rules.items():
            if any(keyword in log.message for keyword in keywords):
                tags.append(tag)
        return TaggedLog(**log.model_dump(), tags=tags)