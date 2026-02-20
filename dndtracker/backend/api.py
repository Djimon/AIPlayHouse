"""FastAPI endpoints for ISSUE-01 encounter creation and retrieval."""

from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from dndtracker.backend.security import generate_token
from dndtracker.backend.store import EncounterStore, InMemoryEncounterStore


class CreateEncounterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class CreateEncounterResponse(BaseModel):
    encounter_id: str
    host_token: str
    player_token: str


class EncounterStateResponse(BaseModel):
    state: dict[str, Any]


def _default_store() -> EncounterStore:
    server_salt = os.getenv("DNDTRACKER_SERVER_SALT", "dev-salt")
    return InMemoryEncounterStore(server_salt=server_salt)


def create_app(store: EncounterStore | None = None) -> FastAPI:
    app = FastAPI(title="DND Tracker API", version="0.1.0")
    encounter_store = store if store is not None else _default_store()

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

    return app


app = create_app()
