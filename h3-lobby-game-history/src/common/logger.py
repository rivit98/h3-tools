import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s [%(pathname)s:%(lineno)d] %(levelname)s - %(message)s'))
logger.addHandler(ch)
