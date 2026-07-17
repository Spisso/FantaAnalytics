import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from scraper.transfermarkt import TransfermarktScraper


class TransfermarktScraperTest(unittest.TestCase):
    def test_get_players_extracts_player_links_from_squad_page(self):
        scraper = TransfermarktScraper()

        roster_html = """
        <html>
            <body>
                <a href="/lautaro-martinez/profil/spieler/406625">Lautaro Martínez</a>
                <a href="/david-villa/profil/spieler/123">David Villa</a>
            </body>
        </html>
        """

        def fake_parse_page(url=None):
            if url is None:
                return BeautifulSoup(roster_html, "lxml")
            if "/profil/spieler/" in url:
                return BeautifulSoup(
                    "<html><body>Squadra attuale: Inter Nato il: 22/08/1997 (28) Nazionalità: Argentina Posizione: Punta centrale</body></html>",
                    "lxml",
                )
            return BeautifulSoup(roster_html, "lxml")

        with (
            patch.object(scraper, "get_club_roster_urls", return_value=["/club/roster"]),
            patch.object(scraper, "parse_page", side_effect=fake_parse_page),
        ):
            players = scraper.get_players()

        self.assertEqual(
            players,
            [
                {
                    "name": "Lautaro Martínez",
                    "team": "Inter",
                    "birth_date": "22/08/1997",
                    "position": "Punta centrale",
                    "nationality": "Argentina",
                },
                {
                    "name": "David Villa",
                    "team": "Inter",
                    "birth_date": "22/08/1997",
                    "position": "Punta centrale",
                    "nationality": "Argentina",
                },
            ],
        )

    def test_get_players_uses_roster_page_team_when_profile_is_missing_it(self):
        scraper = TransfermarktScraper()

        roster_html = """
        <html>
            <head><title>Inter - Kader</title></head>
            <body>
                <h1>Inter</h1>
                <a href="/lautaro-martinez/profil/spieler/406625">Lautaro Martínez</a>
            </body>
        </html>
        """

        def fake_parse_page(url=None):
            if url is None:
                return BeautifulSoup(roster_html, "lxml")
            if "/profil/spieler/" in url:
                return BeautifulSoup(
                    "<html><body>Nato il: 22/08/1997 (28) Nazionalità: Argentina Posizione: Punta centrale</body></html>",
                    "lxml",
                )
            return BeautifulSoup(roster_html, "lxml")

        with (
            patch.object(scraper, "get_club_roster_urls", return_value=["/club/roster"]),
            patch.object(scraper, "parse_page", side_effect=fake_parse_page),
        ):
            players = scraper.get_players()

        self.assertEqual(players[0]["team"], "Inter")

    def test_extract_profile_field_stops_before_stats_metadata(self):
        scraper = TransfermarktScraper()
        text = (
            "Posizione Portiere Era nazionale Spagna Gare/gol 1 / 0 "
            "10,00 mln € Aggiornato al 29/05/2026 Informazioni"
        )

        self.assertEqual(scraper._extract_profile_field(text, "Posizione"), "Portiere")
        self.assertEqual(scraper._extract_profile_field(text, "Nazionalità"), None)


if __name__ == "__main__":
    unittest.main()
