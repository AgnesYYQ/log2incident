from collections import defaultdict
from typing import Dict, Optional, Tuple

from redis import Redis
from redis.exceptions import RedisError

from config.config import get_auth_users, get_redis_url


class AuthService:
    """Handles login checks and tracks failed password attempts."""

    def __init__(self):
        self.users: Dict[str, str] = get_auth_users()
        self.redis = Redis.from_url(get_redis_url(), decode_responses=True)
        self._fallback_attempts = defaultdict(int)

    def _attempt_key(self, username: str) -> str:
        return f"auth:wrong_password:{username}"

    def _increment_attempts(self, username: str) -> int:
        key = self._attempt_key(username)
        try:
            attempts = self.redis.incr(key)
            self.redis.expire(key, 3600)
            return int(attempts)
        except RedisError:
            self._fallback_attempts[username] += 1
            return self._fallback_attempts[username]

    def _clear_attempts(self, username: str) -> None:
        key = self._attempt_key(username)
        try:
            self.redis.delete(key)
        except RedisError:
            self._fallback_attempts[username] = 0

    def username_exists(self, username: str) -> bool:
        return username in self.users

    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], int]:
        """
        Returns:
            success, error_message, wrong_password_attempts
        """
        if not self.username_exists(username):
            # Immediate username failure, no attempt accumulation.
            return False, "Unknown username", 0

        expected = self.users[username]
        if password != expected:
            attempts = self._increment_attempts(username)
            return False, f"Wrong password. Attempt #{attempts}", attempts

        self._clear_attempts(username)
        return True, None, 0
