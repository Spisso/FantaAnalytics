"""Minimal read-only WSGI API over the canonical repository."""

import json
import logging
from http import HTTPStatus
from typing import Callable, Iterable, List, Tuple
from urllib.parse import parse_qs

from .persistence import CanonicalRepository

logger = logging.getLogger(__name__)

StartResponse = Callable[[str, List[Tuple[str, str]]], None]


class FantaAnalyticsApi:
    def __init__(self, database):
        self.repository = CanonicalRepository(database)

    @staticmethod
    def _response(
        start_response: StartResponse, status: HTTPStatus, payload: dict
    ) -> Iterable[bytes]:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(encoded))),
            ],
        )
        return [encoded]

    def __call__(self, environ: dict, start_response: StartResponse) -> Iterable[bytes]:
        if environ.get("REQUEST_METHOD") != "GET":
            return self._response(
                start_response, HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Metodo non supportato"}
            )
        path = environ.get("PATH_INFO", "")
        query = parse_qs(environ.get("QUERY_STRING", ""))
        if path == "/health":
            return self._response(
                start_response, HTTPStatus.OK, {"status": "ok", "service": "analytics"}
            )
        if path == "/ready":
            ready = self.repository.is_ready()
            status = HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE
            if not ready:
                logger.warning("Database readiness check failed")
            return self._response(
                start_response,
                status,
                {"status": "ready" if ready else "unavailable", "database": ready},
            )
        if path == "/api/v1/players":
            players = self.repository.list_players(
                role=query.get("role", [None])[0],
                team=query.get("team", [None])[0],
                season=query.get("season", [None])[0],
                limit=int(query.get("limit", ["50"])[0]),
            )
            return self._response(
                start_response, HTTPStatus.OK, {"data": players, "count": len(players)}
            )
        if path == "/api/v1/teams":
            season = query.get("season", [None])[0]
            teams = self.repository.list_teams(season=season)
            return self._response(
                start_response,
                HTTPStatus.OK,
                {"data": teams, "count": len(teams), "season": season},
            )
        if path.startswith("/api/v1/players/"):
            try:
                player_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                return self._response(
                    start_response, HTTPStatus.NOT_FOUND, {"error": "Giocatore non trovato"}
                )
            player = self.repository.get_player(player_id)
            if player is None:
                return self._response(
                    start_response, HTTPStatus.NOT_FOUND, {"error": "Giocatore non trovato"}
                )
            return self._response(start_response, HTTPStatus.OK, {"data": player})
        if path == "/api/v1/import-runs":
            runs = self.repository.list_import_runs(limit=int(query.get("limit", ["50"])[0]))
            return self._response(start_response, HTTPStatus.OK, {"data": runs, "count": len(runs)})
        return self._response(
            start_response, HTTPStatus.NOT_FOUND, {"error": "Risorsa non trovata"}
        )


def create_app(database) -> FantaAnalyticsApi:
    return FantaAnalyticsApi(database)
