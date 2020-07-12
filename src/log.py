# -*- coding: utf-8 -*-
__author__ = '@buzz'

import logging

FORMAT = '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s'
TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S %z'

logger = logging.getLogger("webhunt")
logger.propagate = False


def setup_logger(verbose: bool = False):
    # clear logging default handlers
    logging.getLogger().handlers.clear()
    logger.handlers.clear()
    # add logger format
    formatter = logging.Formatter(FORMAT, TIMESTAMP_FORMAT)
    output_handler = logging.StreamHandler()
    output_handler.setFormatter(formatter)
    logger.addHandler(output_handler)
    # set level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
