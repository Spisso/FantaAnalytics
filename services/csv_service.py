from pathlib import Path

import pandas as pd


class CsvService:
    def save(self, data, path):

        if not data:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)

        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(
            destination,
            index=False,
            encoding="utf-8",
        )
