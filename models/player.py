from datetime import date


class Player:

    def __init__(
        self,
        name,
        surname,
        team,
        role,
        birth_date,
        nationality=None,
        market_value=None
    ):
        self.name = name
        self.surname = surname
        self.team = team
        self.role = role
        self.birth_date = birth_date
        self.nationality = nationality
        self.market_value = market_value


    def get_age(self):
        today = date.today()

        age = today.year - self.birth_date.year

        if (today.month, today.day) < (
            self.birth_date.month,
            self.birth_date.day
        ):
            age -= 1

        return age