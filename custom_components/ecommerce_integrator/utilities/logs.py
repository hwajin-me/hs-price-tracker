import logging


def logging_for_response(response, name: str, domain: str = None):
    logging.getLogger(name).debug("API Response catch %s, silently", domain)

    if domain:
        logging.getLogger(f"custom_components.price_tracker_response_{domain}").debug(
            f"API Response {response}"
        )
    else:
        logging.getLogger("custom_components.price_tracker_response").debug(
            f"API Response {response}"
        )
