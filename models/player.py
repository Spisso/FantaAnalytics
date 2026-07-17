from datetime import date

from services.analytics.fantaanalytics.normalization import calculate_age


class Player:
    def __init__(self, name, surname, team, role, birth_date, nationality=None, market_value=None):
        self.name = name
        self.surname = surname
        self.team = team
        self.role = role
        self.birth_date = birth_date
        self.nationality = nationality
        self.market_value = market_value

    def age_on(self, reference_date):
        return calculate_age(self.birth_date, reference_date)

    def get_age(self):
        return self.age_on(date.today())
