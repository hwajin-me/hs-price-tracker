import logging


def logging_for_response(response, name: str):
    logging.getLogger(f"response.{name}").debug(f"API Response {response}")
