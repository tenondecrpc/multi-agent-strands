import logging

logger = logging.getLogger(__name__)

_rate_limit_counts: dict[str, int] = {}


def create_http_client(
    ticket_id: str | None = None,
    session_id: str | None = None,
):
    import httpx

    _pending_emits: list[dict] = []

    def on_response(response: httpx.Response) -> None:
        if response.status_code == 429:
            key = f"{ticket_id or 'unknown'}"
            _rate_limit_counts[key] = _rate_limit_counts.get(key, 0) + 1
            count = _rate_limit_counts[key]
            logger.warning(
                f"LLM rate limited (call #{count}): ticket={ticket_id}, session={session_id}"
            )
            _pending_emits.append(
                {
                    "session_id": session_id,
                    "ticket_id": ticket_id or "unknown",
                    "error": "LLM API rate limit exceeded (429 Too Many Requests)",
                    "agent_type": "orchestrator",
                    "retry_count": count,
                }
            )

    def get_pending_emits() -> list[dict]:
        return _pending_emits.pop() if _pending_emits else []

    async def flush_pending():
        while _pending_emits:
            emit_data = _pending_emits.pop(0)
            try:
                from app.events import emit_llm_rate_limited

                await emit_llm_rate_limited(**emit_data)
            except Exception as e:
                logger.debug(f"Could not emit rate limit event: {e}")

    client = httpx.AsyncClient(event_hooks={"response": [on_response]})

    original_aclose = client.aclose

    async def aclose_with_flush():
        await flush_pending()
        await original_aclose()

    client.aclose = aclose_with_flush

    return client
