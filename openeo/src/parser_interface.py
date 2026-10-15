import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ParserInterface:
    """
    - behavior shared by subclasses: manage commandline arguments -> log -> convert
    - one child class per datasource
    """
    __metaclass__ = ABCMeta

    def __init__(self, args):
        # check with some logic ?
        self.manage_arguments(args)

    @abstractmethod
    def manage_arguments(self, arguments): raise NotImplementedError

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
