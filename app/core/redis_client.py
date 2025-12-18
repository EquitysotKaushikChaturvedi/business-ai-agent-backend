import redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._pool = None

    def get_connection(self) -> redis.Redis:
        if not self._pool:
            try:
                self._pool = redis.ConnectionPool(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True
                )
                logger.info(f"Redis connection pool created for {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"Failed to create Redis pool: {e}")
                raise e
        return redis.Redis(connection_pool=self._pool)

    def is_alive(self) -> bool:
        try:
            client = self.get_connection()
            return client.ping()
        except Exception:
            return False

# Singleton instance
redis_client = RedisClient()

def get_redis() -> redis.Redis:
    """Dependency for FastAPI to get redis connection"""
    return redis_client.get_connection()
