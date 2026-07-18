import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


class TransfermarktScraper:
    BASE_URL = "https://www.transfermarkt.it"
    PLAYER_ID_PATTERN = re.compile(r"/profil/spieler/(\d+)(?:[/?#]|$)")

    def __init__(self, season=None, http_client=None, pause_seconds=1.0, retries=2, sleeper=None):
        season_path = f"/saison_id/{str(season).split('-', 1)[0]}" if season else ""
        self.url = f"{self.BASE_URL}/serie-a/startseite/wettbewerb/IT1{season_path}"
        self.headers = {"User-Agent": "FantaAnalytics/0.1 (responsible data adapter)"}
        self.http_client = http_client or requests.Session()
        self.pause_seconds = max(0.0, pause_seconds)
        self.retries = max(1, retries)
        self.sleeper = sleeper or time.sleep
        self._request_count = 0

    @classmethod
    def extract_external_id(cls, profile_url):
        match = cls.PLAYER_ID_PATTERN.search(profile_url or "")
        return f"transfermarkt:{match.group(1)}" if match else None

    @classmethod
    def canonical_profile_url(cls, profile_url):
        absolute = urljoin(cls.BASE_URL, profile_url or "")
        parts = urlsplit(absolute)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    def get_page(self, url=None):
        if self._request_count and self.pause_seconds:
            self.sleeper(self.pause_seconds)
        self._request_count += 1
        response = self.http_client.get(url or self.url, headers=self.headers, timeout=20)
        response.raise_for_status()
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

    def get_players(self):
        candidates = {}
        for href in self.get_club_roster_urls():
            roster_soup = self.parse_page(urljoin(self.BASE_URL, href))
            team_name = self._extract_team_name(roster_soup)
            for link in roster_soup.select('a[href*="/profil/spieler/"]'):
                profile_url = self.canonical_profile_url(link.get("href"))
                external_id = self.extract_external_id(profile_url)
                full_name = link.get_text(" ", strip=True)
                if external_id and full_name and external_id not in candidates:
                    candidates[external_id] = (full_name, profile_url, team_name)

        players = []
        for external_id, (full_name, profile_url, roster_team) in candidates.items():
            try:
                player_soup = self.parse_page(profile_url)
            except requests.RequestException:
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
