import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


class TransfermarktScraper:
    BASE_URL = "https://www.transfermarkt.it"
    PLAYER_ID_PATTERN = re.compile(r"/profil/spieler/(\d+)(?:[/?#]|$)")
    CLUB_ID_PATTERN = re.compile(r"/kader/verein/(\d+)(?:[/?#]|$)")

    def __init__(self, season=None, http_client=None, pause_seconds=1.0, retries=2, sleeper=None):
        season_path = f"/saison_id/{str(season).split('-', 1)[0]}" if season else ""
        self.url = f"{self.BASE_URL}/serie-a/startseite/wettbewerb/IT1{season_path}"
        self.headers = {"User-Agent": "FantaAnalytics/0.1 (responsible data adapter)"}
        self.http_client = http_client or requests.Session()
        self.pause_seconds = max(0.0, pause_seconds)
        self.retries = max(1, retries)
        self.sleeper = sleeper or time.sleep
        self._request_count = 0
        self.discovered_club_count = 0
        self.processed_clubs = []
        self.requested_profile_count = 0
        self.profile_errors = []
        self.last_response = None

    @classmethod
    def extract_external_id(cls, profile_url):
        match = cls.PLAYER_ID_PATTERN.search(profile_url or "")
        return f"transfermarkt:{match.group(1)}" if match else None

    @classmethod
    def canonical_profile_url(cls, profile_url):
        absolute = urljoin(cls.BASE_URL, profile_url or "")
        parts = urlsplit(absolute)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    @classmethod
    def extract_club_id(cls, roster_url):
        match = cls.CLUB_ID_PATTERN.search(roster_url or "")
        return f"transfermarkt-club:{match.group(1)}" if match else None

    def get_page(self, url=None):
        if self._request_count and self.pause_seconds:
            self.sleeper(self.pause_seconds)
        self._request_count += 1
        response = self.http_client.get(url or self.url, headers=self.headers, timeout=20)
        response.raise_for_status()
        self.last_response = response
        return response.text

    def get_page_with_retry(self, url=None, retries=None):
        attempts = self.retries if retries is None else max(1, retries)
        for attempt in range(attempts):
            try:
                return self.get_page(url)
            except requests.RequestException:
                if attempt == attempts - 1:
                    raise
        return None

    def parse_page(self, url=None):
        return self._parse_html(self.get_page_with_retry(url))

    def _parse_html(self, html):
        return BeautifulSoup(html, "lxml")

    def get_club_roster_urls(self):
        soup = self.parse_page()
        urls = []
        for link in soup.select('a[href*="/kader/verein/"]'):
            href = link.get("href")
            if href and href not in urls:
                urls.append(href)
        return urls

    def get_club_descriptors(self):
        soup = self.parse_page()
        descriptors = []
        seen = set()
        for link in soup.select('a[href*="/kader/verein/"]'):
            href = link.get("href")
            club_id = self.extract_club_id(href)
            if not href or not club_id or club_id in seen:
                continue
            seen.add(club_id)
            name = link.get_text(" ", strip=True) or href.rsplit("/", 1)[-1]
            descriptors.append(
                {
                    "external_id": club_id,
                    "name": name,
                    "roster_url": self.canonical_roster_url(href),
                }
            )
        return descriptors

    @classmethod
    def canonical_roster_url(cls, roster_url):
        absolute = urljoin(cls.BASE_URL, roster_url or "")
        parts = urlsplit(absolute)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    def get_players_for_club(self, roster_url, max_players=None):
        requested_roster_url = self.canonical_roster_url(roster_url)
        roster_soup = self.parse_page(requested_roster_url)
        response = self.last_response
        team_name = self._extract_team_name(roster_soup)
        profile_anchors = roster_soup.select('a[href*="/profil/spieler/"]')
        discarded = []
        candidates = {}
        all_external_ids = set()
        for link in profile_anchors:
            profile_url = self.canonical_profile_url(link.get("href"))
            external_id = self.extract_external_id(profile_url)
            full_name = link.get_text(" ", strip=True)
            if external_id:
                all_external_ids.add(external_id)
            if max_players is not None and len(candidates) >= max_players:
                discarded.append({"reason": "limit_reached", "href": link.get("href")})
            elif not external_id:
                discarded.append({"reason": "external_id_absent", "href": link.get("href"), "name": full_name})
            elif not full_name:
                discarded.append({"reason": "empty_name", "href": link.get("href"), "external_id": external_id})
            elif external_id in candidates:
                discarded.append({"reason": "duplicate", "href": link.get("href"), "external_id": external_id, "name": full_name})
            else:
                candidates[external_id] = (full_name, profile_url, team_name)
        players = []
        errors = []
        for external_id, (full_name, profile_url, roster_team) in candidates.items():
            self.requested_profile_count += 1
            try:
                player_soup = self.parse_page(profile_url)
            except requests.RequestException as exc:
                error = {"profile_url": profile_url, "error": str(exc)}
                self.profile_errors.append(error)
                errors.append(error)
                continue
            players.append(
                {
                    "external_id": external_id,
                    "profile_url": profile_url,
                    "full_name": full_name,
                    "team": self._extract_profile_field(player_soup, "Squadra attuale")
                    or roster_team,
                    "birth_date": self._extract_birth_date(player_soup),
                    "source_role": self._extract_profile_field(player_soup, "Posizione"),
                    "nationality": self._extract_profile_field(player_soup, "Nazionalità"),
                    "market_value": self._extract_market_value(player_soup),
                }
            )
        return players, {
            "requested_url": requested_roster_url,
            "final_url": response.url if response is not None else requested_roster_url,
            "http_status": response.status_code if response is not None else None,
            "response_length": len(response.text) if response is not None else None,
            "title": roster_soup.title.get_text(" ", strip=True) if roster_soup.title else None,
            "team": team_name,
            "total_anchors": len(roster_soup.find_all("a")),
            "profile_anchors": len(profile_anchors),
            "unique_external_ids": len(all_external_ids),
            "links_discarded": discarded,
            "discovered": len(candidates),
            "profiles_requested": len(candidates),
            "profiles_succeeded": len(players),
            "profiles_failed": len(errors),
            "records_valid": len(players),
            "errors": errors,
        }

    def get_players(self, max_clubs=None, max_players=None):
        self.discovered_club_count = 0
        self.processed_clubs = []
        self.requested_profile_count = 0
        self.profile_errors = []
        candidates = {}
        roster_urls = self.get_club_roster_urls()
        self.discovered_club_count = len(roster_urls)
        if max_clubs is not None:
            roster_urls = roster_urls[:max_clubs]
        for href in roster_urls:
            roster_soup = self.parse_page(urljoin(self.BASE_URL, href))
            team_name = self._extract_team_name(roster_soup)
            self.processed_clubs.append(team_name or href)
            for link in roster_soup.select('a[href*="/profil/spieler/"]'):
                profile_url = self.canonical_profile_url(link.get("href"))
                external_id = self.extract_external_id(profile_url)
                full_name = link.get_text(" ", strip=True)
                if external_id and full_name and external_id not in candidates:
                    candidates[external_id] = (full_name, profile_url, team_name)
                    if max_players is not None and len(candidates) >= max_players:
                        break
            if max_players is not None and len(candidates) >= max_players:
                break

        players = []
        for external_id, (full_name, profile_url, roster_team) in candidates.items():
            self.requested_profile_count += 1
            try:
                player_soup = self.parse_page(profile_url)
            except requests.RequestException as exc:
                self.profile_errors.append({"profile_url": profile_url, "error": str(exc)})
                continue
            players.append(
                {
                    "external_id": external_id,
                    "profile_url": profile_url,
                    "full_name": full_name,
                    "team": self._extract_profile_field(player_soup, "Squadra attuale")
                    or roster_team,
                    "birth_date": self._extract_birth_date(player_soup),
                    "source_role": self._extract_profile_field(player_soup, "Posizione"),
                    "nationality": self._extract_profile_field(player_soup, "Nazionalità"),
                    "market_value": self._extract_market_value(player_soup),
                }
            )
        return players

    def _extract_team_name(self, soup):
        for selector in ["h1", "h2", ".data-header__headline", ".spielername"]:
            element = soup.select_one(selector)
            if element and element.get_text(" ", strip=True):
                return element.get_text(" ", strip=True)
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        return title.split("-")[0].strip() if title else None

    def _extract_profile_field(self, soup, label):
        if not isinstance(soup, BeautifulSoup):
            soup = BeautifulSoup(str(soup), "lxml")
        for element in soup.select("li.data-header__label"):
            if element.get_text(" ", strip=True).startswith(label):
                value_element = element.select_one("span.data-header__content")
                if value_element:
                    return re.sub(r"\s+", " ", value_element.get_text(" ", strip=True)).strip()
        for element in soup.select(".info-table__content--regular"):
            if element.get_text(" ", strip=True) == label:
                sibling = element.find_next_sibling(class_="info-table__content--bold")
                if sibling:
                    return re.sub(r"\s+", " ", sibling.get_text(" ", strip=True)).strip()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        if label not in text:
            return None
        boundary = "|".join(
            ["Era nazionale", "Gare/gol", "Aggiornato al", "Informazioni", "Ruolo", "Nome completo", "Dati & fatti", "Nato il", "Nazionalità", "Posizione", "Altezza", "Piede", "Procuratore", "In rosa da", "Scadenza", r"[\d.,]+\s*(?:mln|mila|k)?\s*€"]
        )
        match = re.search(
            rf"{re.escape(label)}\s*[:\-]?\s*(.+?)(?=(?:{boundary})|$)", text, re.IGNORECASE
        )
        return re.sub(r"\s+", " ", match.group(1)).replace(":", "").strip() if match else None

    def _extract_birth_date(self, soup):
        text = soup.get_text(" ", strip=True) if isinstance(soup, BeautifulSoup) else str(soup)
        match = re.search(r"Nato il\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_market_value(self, soup):
        for selector in [".data-header__market-value-wrapper", ".tm-player-market-value-development__current-value"]:
            element = soup.select_one(selector)
            if element:
                match = re.search(r"[\d.,]+\s*(?:mln|mila|k)?\s*€", element.get_text(" ", strip=True), re.I)
                if match:
                    return match.group(0)
        match = re.search(r"[\d.,]+\s*(?:mln|mila|k)?\s*€", soup.get_text(" ", strip=True), re.I)
        return match.group(0) if match else None
