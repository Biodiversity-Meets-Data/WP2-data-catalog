import logging

from src.parser_interface import ParserInterface

logger = logging.getLogger(__name__)


class Parser(ParserInterface):
    def __init__(self, arguments):
        super().__init__(arguments)

    def manage_arguments(self, arguments):
        pass

    def convert(self):
        pass
