from models.player import Player
from datetime import date


player = Player(
    "Lautaro",
    "Martinez",
    "Inter",
    "A",
    date(1997, 8, 22)
)


print(player.name)
print(player.get_age())