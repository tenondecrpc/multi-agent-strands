import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Coroutine

from app.core.config import EVENT_RETENTION_LIMIT
from app.core.logging import get_logger
from app.models.events import EventType

logger = get_logger(__name__)


@dataclass
class Event:
    id: str
    type: EventType
    ticket_id: str
    agent_id: str | None
    payload: dict[str, Any]
    timestamp: datetime

    @classmethod
    def create(
        cls,
        event_type: EventType,
        ticket_id: str,
        agent_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> "Event":
        return cls(
            id=str(uuid.uuid4()),
            type=event_type,
            ticket_id=ticket_id,
            agent_id=agent_id,
            payload=payload or {},
            timestamp=datetime.utcnow(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "ticket_id": self.ticket_id,
            "agent_id": self.agent_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self, retention_limit: int = EVENT_RETENTION_LIMIT):
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._ticket_subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_store: list[Event] = []
        self._retention_limit = retention_limit
        self._lock = asyncio.Lock()

    async def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to {event_type.value}")

    async def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from {event_type.value}")

    async def subscribe_ticket(
        self, ticket_id: str, last_event_id: str | None = None
    ) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()

        async def ticket_handler(event: Event) -> None:
            if event.ticket_id == ticket_id:
                await queue.put(event)

        self._ticket_subscribers[ticket_id].append(ticket_handler)

        try:
            if last_event_id:
                async with self._lock:
                    for event in self._event_store:
                        if event.id > last_event_id:
                            await queue.put(event)

            while True:
                event = await queue.get()
                yield event
        finally:
            if ticket_handler in self._ticket_subscribers[ticket_id]:
                self._ticket_subscribers[ticket_id].remove(ticket_handler)

    async def publish(self, event: Event) -> None:
        async with self._lock:
            self._event_store.append(event)
            if len(self._event_store) > self._retention_limit:
                self._event_store = self._event_store[-self._retention_limit :]

        logger.debug(
            f"Publishing event {event.type.value} for ticket {event.ticket_id}"
        )

        handlers = list(self._subscribers.get(event.type, []))
        for handler in handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

        ticket_handlers = list(self._ticket_subscribers.get(event.ticket_id, []))
        for handler in ticket_handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error in ticket event handler: {e}")

    async def publish_ticket_event(
        self,
        event_type: EventType,
        ticket_id: str,
        agent_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Event:
        event = Event.create(
            event_type=event_type,
            ticket_id=ticket_id,
            agent_id=agent_id,
            payload=payload,
        )
        await self.publish(event)
        return event

    def get_recent_events(
        self, ticket_id: str | None = None, limit: int = 100
    ) -> list[Event]:
        events = self._event_store
        if ticket_id:
            events = [e for e in events if e.ticket_id == ticket_id]
        return events[-limit:]

    async def clear_ticket_events(self, ticket_id: str) -> None:
        async with self._lock:
            self._event_store = [
                e for e in self._event_store if e.ticket_id != ticket_id
            ]


event_bus = EventBus()
