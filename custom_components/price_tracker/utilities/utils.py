import random


def random_bool() -> bool:
    return random.choice([True, False])


def random_choice(choices: list) -> any:
    return random.choice(choices)
