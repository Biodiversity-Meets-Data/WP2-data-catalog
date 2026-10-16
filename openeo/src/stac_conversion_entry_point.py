import argparse
import logging

from src.misc.soilgrids.parser import Parser as SoilgridsParser
from src.misc.bio_oracle.parser import Parser as BioOracleParser
from src.misc.datasource_types import DatasourceTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items, multiple assets per item')
# setup arguments
parser.add_argument('-d', '--datetime', required=True, help="datetime added to each item")
parser.add_argument('-e', '--end_datetime', required=True, help="end date of the collection")
parser.add_argument('-o', '--output_path', required=True, help="path of the directory that will contain the catalog")
parser.add_argument('-s', '--start_datetime', required=True, help="start date of the collection")
parser.add_argument('-t', '--type', required=True, help="datasource type")
# parse
args = parser.parse_args()

# entry point
if __name__ == "__main__":
    try:
        datasource_type = args.type

        if datasource_type == DatasourceTypes.SOILGRIDS:
            converter = SoilgridsParser(arguments=args)
        elif datasource_type == DatasourceTypes.BIO_ORACLE:
            converter = BioOracleParser(arguments=args)
        else:
            raise Exception(f"incorrect datasource type {datasource_type}, allowed values [{DatasourceTypes.list()}]")

        converter.run()
    except Exception as e:
        logger.exception(f"global exception {str(e)}")
