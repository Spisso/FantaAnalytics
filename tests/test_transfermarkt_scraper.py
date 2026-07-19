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

    def test_extracts_unique_club_descriptors(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        league = BeautifulSoup(
            '<a href="/inter/kader/verein/46/saison_id/2026">Inter</a>'
            '<a href="/duplicate/kader/verein/46">Inter duplicate</a>'
            '<a href="/roma/kader/verein/ROMA">Invalid</a>',
            "lxml",
        )
        with patch.object(scraper, "parse_page", return_value=league):
            clubs = scraper.get_club_descriptors()
        self.assertEqual(len(clubs), 1)
        self.assertEqual(clubs[0]["external_id"], "transfermarkt-club:46")
        self.assertEqual(
            clubs[0]["roster_url"],
            "https://www.transfermarkt.it/inter/kader/verein/46/saison_id/2026",
        )

    def test_get_players_for_club_stops_profile_requests_at_limit(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        roster = BeautifulSoup(
            '<h1>Inter</h1>'
            '<a href="/one/profil/spieler/1">Uno</a>'
            '<a href="/two/profil/spieler/2">Due</a>'
            '<a href="/three/profil/spieler/3">Tre</a>',
            "lxml",
        )
        profile = BeautifulSoup(
            "Squadra attuale: Inter Nato il: 01/01/2000 Nazionalità: Italia Posizione: Portiere",
            "lxml",
        )
        with patch.object(scraper, "parse_page", side_effect=[roster, profile]) as parser:
            players, details = scraper.get_players_for_club("/inter/kader/verein/46", 1)
        self.assertEqual(len(players), 1)
        self.assertEqual(details["discovered"], 1)
        self.assertEqual(scraper.requested_profile_count, 1)
        self.assertEqual(parser.call_count, 2)
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

    def test_max_clubs_fetches_only_first_roster(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        roster = BeautifulSoup(
            '<h1>Inter</h1><a href="/one/profil/spieler/1">Uno</a>', "lxml"
        )
        profile = BeautifulSoup(
            "Squadra attuale: Inter Nato il: 01/01/2000 "
            "Nazionalità: Italia Posizione: Portiere",
            "lxml",
        )
        with (
            patch.object(
                scraper, "get_club_roster_urls", return_value=["/club/one", "/club/two"]
            ),
            patch.object(scraper, "parse_page", side_effect=[roster, profile]) as parser,
        ):
            players = scraper.get_players(max_clubs=1)
        self.assertEqual(len(players), 1)
        self.assertEqual(parser.call_count, 2)
        self.assertEqual(scraper.discovered_club_count, 2)
        self.assertEqual(scraper.processed_clubs, ["Inter"])

    def test_max_players_stops_profile_requests_at_limit(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        roster = BeautifulSoup(
            "".join(
                f'<a href="/player-{identifier}/profil/spieler/{identifier}">Player {identifier}</a>'
                for identifier in range(1, 5)
            ),
            "lxml",
        )
        profile = BeautifulSoup(
            "Squadra attuale: Inter Nato il: 01/01/2000 "
            "Nazionalità: Italia Posizione: Portiere",
            "lxml",
        )
        with (
            patch.object(scraper, "get_club_roster_urls", return_value=["/club/one"]),
            patch.object(
                scraper, "parse_page", side_effect=[roster, profile, profile]
            ) as parser,
        ):
            players = scraper.get_players(max_players=2)
        self.assertEqual([player["external_id"] for player in players], ["transfermarkt:1", "transfermarkt:2"])
        self.assertEqual(scraper.requested_profile_count, 2)
        self.assertEqual(parser.call_count, 3)

    def test_without_limits_processes_all_rosters_and_players(self):
        scraper = TransfermarktScraper(pause_seconds=0)
        first_roster = BeautifulSoup(
            '<h1>Inter</h1><a href="/one/profil/spieler/1">Uno</a>', "lxml"
        )
        second_roster = BeautifulSoup(
            '<h1>Roma</h1><a href="/two/profil/spieler/2">Due</a>', "lxml"
        )
        profile = BeautifulSoup(
            "Nato il: 01/01/2000 Nazionalità: Italia Posizione: Portiere", "lxml"
        )
        with (
            patch.object(
                scraper, "get_club_roster_urls", return_value=["/club/one", "/club/two"]
            ),
            patch.object(
                scraper,
                "parse_page",
                side_effect=[first_roster, second_roster, profile, profile],
            ) as parser,
        ):
            players = scraper.get_players()
        self.assertEqual(len(players), 2)
        self.assertEqual(scraper.processed_clubs, ["Inter", "Roma"])
        self.assertEqual(scraper.requested_profile_count, 2)
        self.assertEqual(parser.call_count, 4)

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
