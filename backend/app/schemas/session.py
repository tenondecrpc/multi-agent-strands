from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionAgent(BaseModel):
    id: str
    name: str
    role: str
    state: str


class SessionMetrics(BaseModel):
    tokens_used: int = 0
    duration_seconds: int = 0
    files_created: int = 0
    tests_passed: bool | None = None


class AgentLog(BaseModel):
    id: str
    agent_id: str
    message: str
    level: str
    timestamp: datetime


class SessionResponse(BaseModel):
    session_id: str
    ticket_id: str
    status: str
    started_at: datetime
    agents: list[SessionAgent]
    logs: list[AgentLog] = []
    metrics: SessionMetrics = SessionMetrics()
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
