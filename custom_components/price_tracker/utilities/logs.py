import logging


def logging_for_response(response, name: str):
    logging.getLogger(f"{name}.response").debug(f"API Response {response}")
