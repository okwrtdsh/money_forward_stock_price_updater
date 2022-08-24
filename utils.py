import logging


def setup_logger(logger, level=logging.DEBUG):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] (%(filename)s'
        '#%(lineno)d, %(funcName)s): %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
