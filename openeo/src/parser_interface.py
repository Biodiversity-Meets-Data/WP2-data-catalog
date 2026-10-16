import logging

from abc import ABCMeta, abstractmethod, ABC
from datetime import datetime

logger = logging.getLogger(__name__)


class ParserInterface(ABC):
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
        logger.info("start")
        start = datetime.now()
        self.convert()
        end = datetime.now()
        elapsed = end - start
        logger.info(f"end in {elapsed}")
