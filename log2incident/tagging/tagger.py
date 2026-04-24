from typing import Dict, List


from botocore.exceptions import BotoCoreError, ClientError

from config.config import get_aws_region, get_dynamodb_rules_table
from log2incident.models import RawLog, TaggedLog


DEFAULT_RULES: Dict[str, List[str]] = {
    'error': ['ERROR', 'Exception'],
    'warning': ['WARN', 'WARNING'],
    'info': ['INFO'],
}

class Tagger:
    def __init__(self):
        # Rules are loaded from DynamoDB when configured; otherwise defaults are used.
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, List[str]]:
        table_name = get_dynamodb_rules_table()
        if not table_name:
            return DEFAULT_RULES


        import boto3
        dynamodb = boto3.resource('dynamodb', region_name=get_aws_region())
        table = dynamodb.Table(table_name)

        try:
            response = table.scan()
            items = response.get('Items', [])
        except (BotoCoreError, ClientError):
            return DEFAULT_RULES

        rules: Dict[str, List[str]] = {}
        for item in items:
            tag = str(item.get('tag', '')).strip().lower()
            keywords = item.get('keywords', [])

            if not tag:
                continue
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            if isinstance(keywords, list) and keywords:
                rules[tag] = [str(keyword) for keyword in keywords if str(keyword).strip()]

        return rules or DEFAULT_RULES

    def tag_log(self, log: RawLog) -> TaggedLog:
        tags = []
        message = log.message.lower()
        for tag, keywords in self.rules.items():
            if any(keyword.lower() in message for keyword in keywords):
                tags.append(tag)
        return TaggedLog(**log.model_dump(), tags=tags)