CREATE TABLE IF NOT EXISTS football_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    short_name TEXT,
    competition TEXT NOT NULL,
    season TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(normalized_name, competition, season)
);

CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    normalized_name TEXT NOT NULL,
    birth_date TEXT,
    nationality TEXT,
    secondary_nationality TEXT,
    preferred_foot TEXT,
    height_cm INTEGER,
    source_role TEXT,
    inferred_fantasy_role TEXT,
    official_fantasy_role TEXT,
    effective_fantasy_role TEXT NOT NULL,
    current_team_id INTEGER REFERENCES football_teams(id),
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_players_identity ON players(normalized_name, birth_date);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(current_team_id);

CREATE TABLE IF NOT EXISTS player_source_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    data_source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    external_source_id TEXT,
    source_url TEXT,
    source_display_name TEXT,
    matching_confidence REAL NOT NULL DEFAULT 1.0,
    manually_confirmed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(data_source_id, external_source_id)
);
CREATE INDEX IF NOT EXISTS idx_source_mapping_player ON player_source_mappings(player_id);

CREATE TABLE IF NOT EXISTS data_import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source_id INTEGER NOT NULL REFERENCES data_sources(id),
    schema_version TEXT NOT NULL,
    season TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    input_filename TEXT NOT NULL,
    input_checksum TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    updated_rows INTEGER NOT NULL DEFAULT 0,
    skipped_rows INTEGER NOT NULL DEFAULT 0,
    error_rows INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_import_runs_checksum ON data_import_runs(data_source_id, input_checksum, season);

CREATE TABLE IF NOT EXISTS data_import_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id INTEGER NOT NULL REFERENCES data_import_runs(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    error_code TEXT NOT NULL,
    field_name TEXT,
    raw_value TEXT,
    message TEXT NOT NULL,
    raw_record TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id INTEGER NOT NULL REFERENCES data_import_runs(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    source_external_id TEXT,
    payload TEXT NOT NULL,
    payload_checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(import_run_id, row_number)
);
CREATE INDEX IF NOT EXISTS idx_raw_records_checksum ON raw_records(payload_checksum);
