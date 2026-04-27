from abc import ABCMeta, abstractmethod
import logging
from datetime import datetime
from src.misc.utils import Utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class STACInterface:
    __metaclass__ = ABCMeta

    def __init__(self, args):
        # check with some logic ?
        Utils.manage_arguments(args)

    @abstractmethod
    def convert(self): raise NotImplementedError

    def run(self):
        try:
            logger.info("start")
            start = datetime.now()
            self.convert()
            end = datetime.now()
            elapsed = end - start
            logger.info(f"end in {elapsed}")
        except Exception as e:
            logger.exception("global exception")
