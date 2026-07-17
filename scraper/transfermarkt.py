import re

import requests
from bs4 import BeautifulSoup


class TransfermarktScraper:
    def __init__(self):
        self.url = "https://www.transfermarkt.it/serie-a/startseite/wettbewerb/IT1"

        self.headers = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")}

    def get_page(self, url=None):

        target_url = url or self.url

        response = requests.get(
            target_url,
            headers=self.headers,
            timeout=20,
        )

        response.raise_for_status()

        return response.text

    def get_page_with_retry(self, url=None, retries=3):
        for attempt in range(retries):
            try:
                return self.get_page(url)
            except requests.RequestException:
                if attempt == retries - 1:
                    raise
        return None

    def parse_page(self, url=None):

        html = self.get_page_with_retry(url)

        return self._parse_html(html)

    def _parse_html(self, html):
        return BeautifulSoup(html, "lxml")

    def get_club_roster_urls(self):

        soup = self.parse_page()

        roster_urls = []

        for link in soup.select('a[href*="/kader/verein/"]'):
            href = link.get("href")
            if href and href not in roster_urls:
                roster_urls.append(href)

        return roster_urls

    def get_players(self):

        players = []
        roster_urls = self.get_club_roster_urls()

        for href in roster_urls:
            full_url = f"https://www.transfermarkt.it{href}"
            roster_soup = self.parse_page(full_url)
            team_name = self._extract_team_name(roster_soup)

            for link in roster_soup.select('a[href*="/profil/spieler/"]'):
                name = link.get_text(" ", strip=True)
                player_url = link.get("href")

                if name and player_url:
                    full_player_url = f"https://www.transfermarkt.it{player_url}"
                    try:
                        player_soup = self.parse_page(full_player_url)
                    except requests.RequestException:
                        continue

                    player_data = {
                        "name": name,
                        "team": self._extract_profile_field(player_soup, "Squadra attuale")
                        or team_name,
                        "birth_date": self._extract_birth_date(player_soup),
                        "position": self._extract_profile_field(player_soup, "Posizione"),
                        "nationality": self._extract_profile_field(player_soup, "Nazionalità"),
                    }

                    if player_data["name"] not in {player["name"] for player in players}:
                        players.append(player_data)

        return players

    def _extract_team_name(self, soup):
        for selector in ["h1", "h2", ".data-header__headline", ".spielername"]:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(" ", strip=True)
                if text:
                    return text

        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        if title:
            return title.split("-")[0].strip()

        return None

    def _extract_profile_field(self, soup, label):
        if not isinstance(soup, BeautifulSoup):
            text = str(soup)
            soup = BeautifulSoup(text, "lxml")

        for element in soup.select("li.data-header__label"):
            label_text = element.get_text(" ", strip=True)
            if label_text.startswith(label):
                value_element = element.select_one("span.data-header__content")
                if value_element:
                    value = value_element.get_text(" ", strip=True)
                    return re.sub(r"\s+", " ", value).strip()

        for element in soup.select(".info-table__content--regular"):
            if element.get_text(" ", strip=True) == label:
                sibling = element.find_next_sibling(class_="info-table__content--bold")
                if sibling:
                    value = sibling.get_text(" ", strip=True)
                    return re.sub(r"\s+", " ", value).strip()

        text = soup.get_text(" ", strip=True)
        if label not in text:
            return None

        normalized_text = re.sub(r"\s+", " ", text)
        stop_tokens = [
            r"Era nazionale",
            r"Gare/gol",
            r"Aggiornato al",
            r"Informazioni",
            r"Ruolo",
            r"Nome completo",
            r"Dati & fatti",
            r"Nato il",
            r"Nazionalità",
            r"Posizione",
            r"Altezza",
            r"Piede",
            r"Procuratore",
            r"In rosa da",
            r"Scadenza",
        ]
        boundary = "|".join(stop_tokens)
        pattern = re.compile(
            rf"{re.escape(label)}\s*[:\-]?\s*(.+?)(?=(?:{boundary})|$)",
            re.IGNORECASE,
        )
        match = pattern.search(normalized_text)
        if not match:
            return None

        value = match.group(1).strip()
        value = re.sub(r"\s+", " ", value)
        return value.replace(":", "").strip()

    def _extract_birth_date(self, soup):
        if not isinstance(soup, BeautifulSoup):
            text = str(soup)
            soup = BeautifulSoup(text, "lxml")

        for element in soup.select("li.data-header__label"):
            label_text = element.get_text(" ", strip=True)
            if label_text.startswith("Nato il"):
                value_element = element.select_one("span.data-header__content")
                if value_element:
                    value = value_element.get_text(" ", strip=True)
                    return re.sub(r"\s+", " ", value).split("(", 1)[0].strip()

        text = soup.get_text(" ", strip=True)
        if "Nato il" not in text:
            return None

        pattern = re.compile(r"Nato il\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return None

        return match.group(1).strip()
