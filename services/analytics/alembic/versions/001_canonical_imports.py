"""canonical import baseline

Revision ID: 001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "football_teams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("canonical_name", sa.String, nullable=False),
        sa.Column("normalized_name", sa.String, nullable=False),
        sa.Column("short_name", sa.String),
        sa.Column("competition", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("normalized_name", "competition", "season"),
    )
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("source_type", sa.String, nullable=False),
        sa.Column("base_url", sa.String),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("canonical_full_name", sa.String, nullable=False),
        sa.Column("first_name", sa.String),
        sa.Column("last_name", sa.String),
        sa.Column("normalized_name", sa.String, nullable=False),
        sa.Column("birth_date", sa.Date),
        sa.Column("nationality", sa.String),
        sa.Column("secondary_nationality", sa.String),
        sa.Column("preferred_foot", sa.String),
        sa.Column("height_cm", sa.Integer),
        sa.Column("source_role", sa.String),
        sa.Column("inferred_fantasy_role", sa.String),
        sa.Column("official_fantasy_role", sa.String),
        sa.Column("effective_fantasy_role", sa.String, nullable=False),
        sa.Column("current_team_id", sa.Integer, sa.ForeignKey("football_teams.id")),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_players_identity", "players", ["normalized_name", "birth_date"])
    op.create_table(
        "player_source_mappings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "player_id", sa.Integer, sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "data_source_id",
            sa.Integer,
            sa.ForeignKey("data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_source_id", sa.String),
        sa.Column("source_url", sa.String),
        sa.Column("source_display_name", sa.String),
        sa.Column("matching_confidence", sa.Float, nullable=False),
        sa.Column("manually_confirmed", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("data_source_id", "external_source_id"),
    )
    op.create_table(
        "data_import_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("data_source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("schema_version", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("input_filename", sa.String, nullable=False),
        sa.Column("input_checksum", sa.String, nullable=False),
        sa.Column("parser_version", sa.String, nullable=False),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("inserted_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "data_import_errors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "import_run_id",
            sa.Integer,
            sa.ForeignKey("data_import_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("error_code", sa.String, nullable=False),
        sa.Column("field_name", sa.String),
        sa.Column("raw_value", sa.Text),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("raw_record", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "raw_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "import_run_id",
            sa.Integer,
            sa.ForeignKey("data_import_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("source_external_id", sa.String),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("payload_checksum", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("import_run_id", "row_number"),
    )


def downgrade():
    for table in (
        "raw_records",
        "data_import_errors",
        "data_import_runs",
        "player_source_mappings",
        "players",
        "data_sources",
        "football_teams",
    ):
        op.drop_table(table)
