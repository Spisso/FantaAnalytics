"""Minimal read-only WSGI API over the canonical repository."""

import json
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable, List, Tuple
from urllib.parse import parse_qs

from .persistence import CanonicalRepository

StartResponse = Callable[[str, List[Tuple[str, str]]], None]


class FantaAnalyticsApi:
    def __init__(self, database_path: Path):
        self.repository = CanonicalRepository(database_path)

    @staticmethod
    def _response(
        start_response: StartResponse, status: HTTPStatus, payload: dict
    ) -> Iterable[bytes]:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
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
            ready = self.repository.is_available()
            status = HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE
            return self._response(
                start_response, status, {"status": "ok" if ready else "degraded", "database": ready}
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


def create_app(database_path: Path) -> FantaAnalyticsApi:
    return FantaAnalyticsApi(database_path)
