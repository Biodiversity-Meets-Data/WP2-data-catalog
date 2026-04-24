import logging
from src.misc.soilgrids.constants import Constants

logger = logging.getLogger(__name__)


class Utils:
    @staticmethod
    def extract_band_from_name(file_name: str, known_bands: list):
        tokens = file_name.split(Constants.token_separator)
        nbr_tokens = len(tokens)

        if nbr_tokens != Constants.max_nbr_tokens:
            raise Exception(f"incorrect number of tokens: {nbr_tokens}")

        band = tokens[1]

        if band not in known_bands:
            raise Exception(f"band {band}: is unknown")

        return band
