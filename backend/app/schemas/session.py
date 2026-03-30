from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionAgent(BaseModel):
    id: str
    name: str
    role: str
    state: str


class SessionResponse(BaseModel):
    session_id: str
    ticket_id: str
    status: str
    created_at: datetime
    agents: list[SessionAgent]

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
