import logging

from pystac import CatalogType

from src.parser_interface import ParserInterface
from src.misc.bio_oracle.constants import Constants as BioOracleConstants
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class Parser(ParserInterface):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.output_path = arguments.output_path

    def manage_arguments(self, arguments):
        pass

    def convert(self):
        extractor = super().get_extractor()
        dataset = super().query_dataset(uuid=BioOracleConstants.dataset_id)
        catalog = Utils.create_catalog("soilgrids_catalog", "main catalog")

        attributes = extractor.extract_attributes(dataset)

        catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)
