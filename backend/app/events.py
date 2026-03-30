import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
)

NAMESPACE = "/pipeline"


class PipelineNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        pass

    async def on_disconnect(self, sid):
        pass


sio.register_namespace(PipelineNamespace(NAMESPACE))


async def emit_pipeline_started(session_id: str, ticket_id: str) -> None:
    await sio.emit(
        "pipeline_started",
        {"session_id": session_id, "ticket_id": ticket_id},
        namespace=NAMESPACE,
    )


async def emit_pipeline_completed(
    session_id: str, ticket_id: str, result: dict
) -> None:
    await sio.emit(
        "pipeline_completed",
        {"session_id": session_id, "ticket_id": ticket_id, "result": result},
        namespace=NAMESPACE,
    )


async def emit_pipeline_error(session_id: str, ticket_id: str, error: str) -> None:
    await sio.emit(
        "pipeline_error",
        {"session_id": session_id, "ticket_id": ticket_id, "error": error},
        namespace=NAMESPACE,
    )
