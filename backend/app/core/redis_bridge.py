import asyncio
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import REDIS_URL

logger = logging.getLogger(__name__)

REDIS_EVENT_CHANNEL = "agent_events"

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def publish_event(event_data: dict[str, Any]) -> None:
    """Publish an event to Redis pub/sub for cross-process delivery."""
    try:
        r = get_redis()
        payload = json.dumps(event_data)
        await r.publish(REDIS_EVENT_CHANNEL, payload)
    except Exception:
        logger.exception("Failed to publish event to Redis")


class RedisEventSubscriber:
    """Subscribes to Redis pub/sub and forwards events to a callback."""

    def __init__(self, on_event: callable):
        self.on_event = on_event
        self._running = False
        self._task: asyncio.Task | None = None
        self._pubsub: redis.client.PubSub | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen())
        logger.info("Redis event subscriber started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._pubsub:
            try:
                await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None
        logger.info("Redis event subscriber stopped")

    async def _listen(self) -> None:
        r = get_redis()
        self._pubsub = r.pubsub()
        await self._pubsub.subscribe(REDIS_EVENT_CHANNEL)
        logger.info(f"Subscribed to Redis channel {REDIS_EVENT_CHANNEL}")

        try:
            while self._running:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message is None:
                    continue
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        await self.on_event(event_data)
                    except json.JSONDecodeError:
                        logger.exception("Failed to parse event from Redis")
                    except Exception:
                        logger.exception("Error processing event from Redis")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Subscriber task failed")
            raise
        finally:
            try:
                await self._pubsub.unsubscribe(REDIS_EVENT_CHANNEL)
                await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None
            logger.info("Subscriber cleanup complete")
