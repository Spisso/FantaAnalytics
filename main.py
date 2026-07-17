import os

import pandas as pd
import requests

from scraper.transfermarkt import TransfermarktScraper
from services.csv_service import CsvService
from services.database_service import DatabaseService

CSV_PATH = "data/raw/transfermarkt_players.csv"
DB_PATH = "database/transfermarkt.db"


def load_players():
    scraper = TransfermarktScraper()

    try:
        return scraper.get_players()
    except requests.RequestException as exc:
        print(f"Scraping fallito, uso il backup CSV: {exc}")
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH).to_dict(orient="records")
        return []


def normalize_players(players):
    normalized_players = []
    for player in players:
        normalized_players.append(
            {
                "name": player.get("name"),
                "team": player.get("team"),
                "birth_date": player.get("birth_date"),
                "position": player.get("position"),
                "nationality": player.get("nationality"),
            }
        )
    return normalized_players


def main():
    players = load_players()
    normalized_players = normalize_players(players)

    csv = CsvService()
    csv.save(normalized_players, CSV_PATH)

    db = DatabaseService(db_path=DB_PATH)
    db.save(normalized_players, table_name="players")

    print(f"Salvati {len(normalized_players)} giocatori")


if __name__ == "__main__":
    main()
