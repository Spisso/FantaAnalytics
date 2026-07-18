from services.analytics.fantaanalytics.cli import main as analytics_cli


def main():
    database = "data/processed/fantaanalytics.db"
    upgraded = analytics_cli(["db-upgrade", "--database", database])
    if upgraded:
        return upgraded
    return analytics_cli(
        [
            "scrape-transfermarkt",
            "--season",
            "2026-27",
            "--database",
            database,
            "--output",
            "data/raw/transfermarkt_players.csv",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
