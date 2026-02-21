"""FastAPI endpoints for encounter creation, retrieval and websocket sync."""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .security import generate_token
from .store import EncounterStore, InMemoryEncounterStore


class CreateEncounterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class CreateEncounterResponse(BaseModel):
    encounter_id: str
    host_token: str
    player_token: str


class EncounterStateResponse(BaseModel):
    state: dict[str, Any]


class ActionEnvelope(BaseModel):
    token: str = Field(min_length=1)
    action: dict[str, Any]


class RollEnvelope(BaseModel):
    token: str = Field(min_length=1)
    roll: dict[str, Any]


class ChatEnvelope(BaseModel):
    token: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=1000)


class EncounterWebSocketHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, encounter_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[encounter_id].add(websocket)

    def disconnect(self, encounter_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(encounter_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(encounter_id, None)

    async def send_state(self, websocket: WebSocket, state: dict[str, Any]) -> None:
        await websocket.send_json({"type": "state.full", "state": state})

    async def broadcast_state(self, encounter_id: str, state: dict[str, Any]) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in self._connections.get(encounter_id, set()):
            try:
                await self.send_state(websocket, state)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(encounter_id=encounter_id, websocket=websocket)


def _default_store() -> EncounterStore:
    server_salt = os.getenv("DNDTRACKER_SERVER_SALT", "dev-salt")
    return InMemoryEncounterStore(server_salt=server_salt)


def create_app(store: EncounterStore | None = None) -> FastAPI:
    app = FastAPI(title="DND Tracker API", version="0.2.0")
    encounter_store = store if store is not None else _default_store()
    websocket_hub = EncounterWebSocketHub()
    app.state.websocket_hub = websocket_hub

    async def publish_state(encounter_id: str, state: dict[str, Any]) -> None:
        await websocket_hub.broadcast_state(encounter_id=encounter_id, state=state)

    app.state.publish_state = publish_state

    def get_store() -> EncounterStore:
        return encounter_store

    @app.post("/api/encounters", response_model=CreateEncounterResponse)
    def create_encounter(
        payload: CreateEncounterRequest,
        local_store: EncounterStore = Depends(get_store),
    ) -> CreateEncounterResponse:
        host_token = generate_token()
        player_token = generate_token()
        created = local_store.create_encounter(
            name=payload.name,
            host_token=host_token,
            player_token=player_token,
        )
        return CreateEncounterResponse(
            encounter_id=created.encounter_id,
            host_token=created.host_token,
            player_token=created.player_token,
        )

    @app.get("/api/encounters/{encounter_id}", response_model=EncounterStateResponse)
    def get_encounter(
        encounter_id: str,
        token: str = Query(min_length=1),
        local_store: EncounterStore = Depends(get_store),
    ) -> EncounterStateResponse:
        record = local_store.get_encounter_state(encounter_id=encounter_id, raw_token=token)
        if record is None:
            raise HTTPException(status_code=404, detail="Encounter not found or token invalid")
        return EncounterStateResponse(state=record.state)

    @app.post("/api/encounters/{encounter_id}/actions", response_model=EncounterStateResponse)
    async def post_action(
        encounter_id: str,
        payload: ActionEnvelope,
        local_store: EncounterStore = Depends(get_store),
    ) -> EncounterStateResponse:
        state = local_store.apply_action(encounter_id=encounter_id, raw_token=payload.token, action=payload.action)
        if state is None:
            raise HTTPException(status_code=403, detail="Action not allowed")
        await publish_state(encounter_id=encounter_id, state=state)
        return EncounterStateResponse(state=state)

    @app.post("/api/encounters/{encounter_id}/rolls", response_model=EncounterStateResponse)
    async def post_roll(
        encounter_id: str,
        payload: RollEnvelope,
        local_store: EncounterStore = Depends(get_store),
    ) -> EncounterStateResponse:
        state = local_store.append_roll(encounter_id=encounter_id, raw_token=payload.token, roll=payload.roll)
        if state is None:
            raise HTTPException(status_code=403, detail="Roll not allowed")
        await publish_state(encounter_id=encounter_id, state=state)
        return EncounterStateResponse(state=state)

    @app.post("/api/encounters/{encounter_id}/chat", response_model=EncounterStateResponse)
    async def post_chat(
        encounter_id: str,
        payload: ChatEnvelope,
        local_store: EncounterStore = Depends(get_store),
    ) -> EncounterStateResponse:
        state = local_store.append_chat(encounter_id=encounter_id, raw_token=payload.token, message=payload.message)
        if state is None:
            raise HTTPException(status_code=403, detail="Chat not allowed")
        await publish_state(encounter_id=encounter_id, state=state)
        return EncounterStateResponse(state=state)

    @app.websocket("/ws/encounters/{encounter_id}")
    async def encounter_ws(
        websocket: WebSocket,
        encounter_id: str,
        local_store: EncounterStore = Depends(get_store),
    ) -> None:
        token = websocket.query_params.get("token")
        if token is None or token == "":
            await websocket.close(code=1008)
            return
        access = local_store.get_encounter_access(encounter_id=encounter_id, raw_token=token)
        if access is None:
            await websocket.close(code=1008)
            return

        await websocket_hub.connect(encounter_id=encounter_id, websocket=websocket)
        await websocket_hub.send_state(websocket=websocket, state=access.state)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_hub.disconnect(encounter_id=encounter_id, websocket=websocket)

    return app


app = create_app()
