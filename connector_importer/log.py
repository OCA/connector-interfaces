# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from logging.handlers import RotatingFileHandler

LOGGER_NAME = "[importer]"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

if os.getenv("IMPORTER_LOG_PATH"):
    # use separated log file when developing
    FNAME = "import.log"

    base_path = os.environ.get("IMPORTER_LOG_PATH")
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # add a rotating handler
    handler = RotatingFileHandler(
        base_path + "/" + FNAME, maxBytes=1024 * 5, backupCount=5
    )
    logger.addHandler(handler)
    logging.info("logging to {}".format(base_path + "/" + FNAME))
