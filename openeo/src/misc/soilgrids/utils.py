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

    @staticmethod
    def generate_file_name(variable_name: str, band_name: str, resolution: str):
        return Constants.token_separator.join([variable_name, band_name, "mean", resolution])

    @staticmethod
    def generate_file_names():
        file_names = list()

        for variables_name in Constants.variables_names:
            for band_name in Constants.band_names:
                for resolution in Constants.resolutions:
                    file_names.append(Utils.generate_file_name(variables_name, band_name, resolution))

        return file_names
