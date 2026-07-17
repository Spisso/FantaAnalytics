import pandas as pd


class CsvService:

    def save(self, data, path):

        if not data:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)

        df.to_csv(
            path,
            index=False,
            encoding="utf-8"
        )