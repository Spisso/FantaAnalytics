import unittest
from unittest.mock import Mock, patch

import requests
from bs4 import BeautifulSoup

from scraper.transfermarkt import TransfermarktScraper


class TransfermarktScraperTest(unittest.TestCase):
    def test_extracts_stable_external_id_and_canonical_url(self):
        url = "/lautaro/profil/spieler/406625?foo=bar"
        self.assertEqual(
            TransfermarktScraper.extract_external_id(url), "transfermarkt:406625"
        )
        self.assertEqual(
            TransfermarktScraper.canonical_profile_url(url),
            "https://www.transfermarkt.it/lautaro/profil/spieler/406625",
        )

    def test_get_players_deduplicates_profile_before_fetch(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        roster = BeautifulSoup(
            '<h1>Inter</h1><a href="/lautaro/profil/spieler/406625">Lautaro Martínez</a>'
            '<a href="/altro/profil/spieler/406625">Lautaro Duplicate</a>',
            "lxml",
        )
        profile = BeautifulSoup(
            "Squadra attuale: Inter Nato il: 22/08/1997 (28) "
            "Nazionalità: Argentina Posizione: Punta centrale 95,00 mln €",
            "lxml",
        )
        with (
            patch.object(scraper, "get_club_roster_urls", return_value=["/club/roster"]),
            patch.object(scraper, "parse_page", side_effect=[roster, profile]) as parser,
        ):
            players = scraper.get_players()
        self.assertEqual(len(players), 1)
        self.assertEqual(parser.call_count, 2)
        self.assertEqual(players[0]["external_id"], "transfermarkt:406625")
        self.assertEqual(players[0]["full_name"], "Lautaro Martínez")
        self.assertEqual(players[0]["source_role"], "Punta centrale")
        self.assertEqual(players[0]["market_value"], "95,00 mln €")

    def test_http_client_is_injectable_and_errors_are_raised(self):
        client = Mock()
        client.get.side_effect = requests.ConnectionError("offline")
        scraper = TransfermarktScraper(http_client=client, pause_seconds=0, retries=2)
        with self.assertRaises(requests.ConnectionError):
            scraper.get_page_with_retry()
        self.assertEqual(client.get.call_count, 2)

    def test_extract_profile_field_stops_before_stats_metadata(self):
        scraper = TransfermarktScraper()
        text = "Posizione Portiere Era nazionale Spagna Gare/gol 1 / 0"
        self.assertEqual(scraper._extract_profile_field(text, "Posizione"), "Portiere")


if __name__ == "__main__":
    unittest.main()
