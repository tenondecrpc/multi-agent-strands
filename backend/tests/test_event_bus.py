import pytest
import asyncio
from app.core.event_bus import EventBus, Event
from app.models.events import EventType


class TestEventBus:
    @pytest.fixture
    def event_bus(self):
        return EventBus(retention_limit=10)

    @pytest.fixture
    def sample_event(self):
        return Event.create(
            event_type=EventType.TICKET_RECEIVED,
            ticket_id="TEST-123",
            agent_id="agent-1",
            payload={"test": "data"},
        )

    @pytest.mark.asyncio
    async def test_subscribe_and_unsubscribe(self, event_bus):
        async def handler(event):
            pass

        await event_bus.subscribe(EventType.TICKET_RECEIVED, handler)
        assert EventType.TICKET_RECEIVED in event_bus._subscribers
        assert handler in event_bus._subscribers[EventType.TICKET_RECEIVED]

        await event_bus.unsubscribe(EventType.TICKET_RECEIVED, handler)
        assert handler not in event_bus._subscribers[EventType.TICKET_RECEIVED]

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus, sample_event):
        handler_called = []

        async def handler(event):
            handler_called.append(event)

        await event_bus.subscribe(EventType.TICKET_RECEIVED, handler)
        await event_bus.publish(sample_event)

        await asyncio.sleep(0.1)

        assert len(handler_called) == 1
        assert handler_called[0].id == sample_event.id

    @pytest.mark.asyncio
    async def test_publish_ticket_event(self, event_bus):
        event = await event_bus.publish_ticket_event(
            event_type=EventType.TICKET_STAGE_CHANGED,
            ticket_id="TEST-456",
            agent_id="agent-2",
            payload={"old": "NEW", "new": "TRIAGED"},
        )

        assert event.ticket_id == "TEST-456"
        assert event.type == EventType.TICKET_STAGE_CHANGED
        assert event.payload["old"] == "NEW"

    @pytest.mark.asyncio
    async def test_event_retention_limit(self, event_bus):
        for i in range(15):
            await event_bus.publish_ticket_event(
                event_type=EventType.TICKET_UPDATED,
                ticket_id=f"TEST-{i}",
            )

        assert len(event_bus._event_store) == 10

    def test_get_recent_events(self, event_bus):
        asyncio.get_event_loop().run_until_complete(
            event_bus.publish_ticket_event(
                event_type=EventType.TICKET_RECEIVED,
                ticket_id="TEST-100",
            )
        )

        events = event_bus.get_recent_events(limit=5)
        assert len(events) <= 5

    def test_get_recent_events_by_ticket(self, event_bus):
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(
                event_bus.publish_ticket_event(
                    event_type=EventType.TICKET_RECEIVED,
                    ticket_id="TEST-FILTER",
                ),
                event_bus.publish_ticket_event(
                    event_type=EventType.TICKET_UPDATED,
                    ticket_id="TEST-FILTER",
                ),
                event_bus.publish_ticket_event(
                    event_type=EventType.TICKET_RECEIVED,
                    ticket_id="OTHER-123",
                ),
            )
        )

        events = event_bus.get_recent_events(ticket_id="TEST-FILTER")
        assert all(e.ticket_id == "TEST-FILTER" for e in events)

    @pytest.mark.asyncio
    async def test_clear_ticket_events(self, event_bus):
        await asyncio.gather(
            event_bus.publish_ticket_event(
                event_type=EventType.TICKET_RECEIVED,
                ticket_id="TEST-CLEAR",
            ),
            event_bus.publish_ticket_event(
                event_type=EventType.TICKET_UPDATED,
                ticket_id="TEST-CLEAR",
            ),
        )

        await event_bus.clear_ticket_events("TEST-CLEAR")

        events = event_bus.get_recent_events(ticket_id="TEST-CLEAR")
        assert len(events) == 0


class TestEvent:
    def test_event_create(self):
        event = Event.create(
            event_type=EventType.AGENT_STARTED,
            ticket_id="TEST-789",
            agent_id="agent-3",
            payload={"task": "test"},
        )

        assert event.id is not None
        assert event.type == EventType.AGENT_STARTED
        assert event.ticket_id == "TEST-789"
        assert event.agent_id == "agent-3"
        assert event.payload["task"] == "test"
        assert event.timestamp is not None

    def test_event_to_dict(self):
        event = Event.create(
            event_type=EventType.ARTIFACT_CREATED,
            ticket_id="TEST-DICT",
            payload={"artifact": "test.md"},
        )

        event_dict = event.to_dict()

        assert event_dict["id"] == event.id
        assert event_dict["type"] == EventType.ARTIFACT_CREATED.value
        assert event_dict["ticket_id"] == "TEST-DICT"
        assert event_dict["payload"]["artifact"] == "test.md"
        assert "timestamp" in event_dict
