from bs4 import BeautifulSoup


def parse_bool(value: any) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in [
            "true",
            "yes",
            "y",
            "はい",
            "예",
            "ok",
            "1",
            "on",
            "enable",
            "enabled",
            "active",
            "activated",
            "open",
            "opened",
            "unlock",
            "unlocked",
        ]
    return bool(value)


def parse_float(value: any) -> float:
    if isinstance(value, float):
        return value

    try:
        return float(
            str(value)
            .replace(",", "")
            .replace(" ", "")
            .replace("円", "")
            .replace("¥", "")
            .replace("￦", "")
            .replace("₩", "")
            .replace("$", "")
            .replace("\t", "")
            .replace("원", "")
        )
    except (ValueError, TypeError):
        return 0.0


def parse_number(value: any) -> int:
    if value is None:
        return 0

    try:
        return int(
            str(value)
            .replace(",", "")
            .replace(" ", "")
            .replace("円", "")
            .replace("¥", "")
            .replace("￦", "")
            .replace("\t", "")
            .replace("원", "")
            .replace("free", "0")
        )
    except (ValueError, TypeError):
        return 0


def parse_html(text: str):
    return BeautifulSoup(text, "html.parser")


def parse_engine_id(item: any) -> str:
    if isinstance(item, dict):
        return "_".join(item.values())

    return str(item)
