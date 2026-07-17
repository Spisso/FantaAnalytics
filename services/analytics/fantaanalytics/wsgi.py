"""Container entrypoint for the read-only API."""

from .api import create_app
from .settings import Settings

application = create_app(Settings.from_env().database_url)
