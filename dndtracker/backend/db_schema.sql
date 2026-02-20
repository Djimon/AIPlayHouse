CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    current_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS encounter_tokens (
    id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    role TEXT NOT NULL CHECK (role IN ('HOST', 'PLAYER')),
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS encounter_snapshots (
    id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    state_json JSONB NOT NULL,
    UNIQUE(encounter_id, version)
);

CREATE TABLE IF NOT EXISTS encounter_rolls (
    id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    created_at TIMESTAMPTZ NOT NULL,
    actor_id TEXT NULL,
    who_label TEXT NOT NULL,
    roll_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS encounter_chat (
    id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    created_at TIMESTAMPTZ NOT NULL,
    who_label TEXT NOT NULL,
    actor_id TEXT NULL,
    text TEXT NOT NULL
);
