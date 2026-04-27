import argparse
import logging
from datetime import datetime

from src.convert_multiple_assets import ConvertMultipleAssets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items')
# setup arguments
parser.add_argument('-d', '--datetime', required=True, help="datetime added to each item")
parser.add_argument('-e', '--end_datetime', required=True, help="end date of the collection")
parser.add_argument('-o', '--output_path', required=True, help="path of the directory that will contain the catalog")
parser.add_argument('-p', '--projection', required=True, help="name of the projection to use")
parser.add_argument('-s', '--start_datetime', required=True, help="start date of the collection")
# parse
args = parser.parse_args()


if __name__ == "__main__":
    try:
        convert = ConvertMultipleAssets(arguments=args)
        convert.run()

        # logger.info("start")
        # start = datetime.now()
        # convert = ConvertMultipleAssets(arguments=args)
        # convert.convert(urls=bdod_urls)
        # end = datetime.now()
        # elapsed = end - start
        # logger.info(f"end in {elapsed}")
    except Exception as e:
        logger.exception("global exception")
