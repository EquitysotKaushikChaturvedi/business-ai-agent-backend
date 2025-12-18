import json
from app.core.redis_client import get_redis
from app.core.config import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, business_id: str, session_id: str):
        self.business_id = business_id
        self.session_id = session_id
        self.redis = get_redis()
        # Key: memory:{business_id}:{session_id}
        self.key = f"memory:{business_id}:{session_id}"

    def add_message(self, role: str, content: str):
        """
        Add a message to the history. 
        Enforces strict window size and TTL.
        Redis List structure: RPUSH (append right), LTRIM (keep last N).
        """
        try:
            msg = json.dumps({"role": role, "content": content})
            pipe = self.redis.pipeline()
            pipe.rpush(self.key, msg)
            # Trim to keep only the last N messages
            # If window is 20, we keep indices: -20 to -1
            start = -settings.CHAT_HISTORY_WINDOW
            pipe.ltrim(self.key, start, -1)
            # Reset TTL
            pipe.expire(self.key, settings.CHAT_TTL_SECONDS)
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to add message to memory: {e}")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Retrieve chat history.
        """
        try:
            # Get all items in the list
            items = self.redis.lrange(self.key, 0, -1)
            return [json.loads(i) for i in items]
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []

    def clear_history(self):
        self.redis.delete(self.key)
