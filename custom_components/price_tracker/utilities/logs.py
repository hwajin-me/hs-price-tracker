import logging


def logging_for_response(response, name: str, domain: str = None):
    logging.getLogger(name).debug('API Response catch %s, silently', domain)

    if domain:
        logging.getLogger(f"{name.replace(".", "")}_response_{domain}").debug(f"API Response {response}")
    else:
        logging.getLogger(f"{name.replace(".", "")}_response").debug(f"API Response {response}")
