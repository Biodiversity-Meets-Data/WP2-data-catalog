import argparse
import logging
from datetime import datetime
from urllib import parse
from convert import Convert

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def manage_arguments(arguments):
    """
    TODO
    maybe infer start_datetime from datetime
    """
    logger.debug("nothing to be done with arguments")


# base url
bdod_url = "https://files.isric.org/soilgrids/latest/data_aggregated/5000m/bdod/"
# url to the tiff files
bdod_tiffs = ["bdod_0-5cm_mean_5000.tif",
              "bdod_5-15cm_mean_5000.tif",
              "bdod_15-30cm_mean_5000.tif",
              "bdod_30-60cm_mean_5000.tif",
              "bdod_60-100cm_mean_5000.tif",
              "bdod_100-200cm_mean_5000.tif"]
bdod_urls = list()

for bdod_tiff in bdod_tiffs:
    url = parse.urljoin(bdod_url, bdod_tiff)
    bdod_urls.append(url)

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items')
# setup arguments
parser.add_argument('-b', '--bands_path', required=True, help="path of the json file where bands are defined")
parser.add_argument('-d', '--datetime', required=True, help="datetime added to each item")
parser.add_argument('-e', '--end_datetime', required=True, help="end date of the collection")
parser.add_argument('-i', '--input_path', help="path of the directory where local files are located. "
                                               "If undefined, hard-coded urls are used")
parser.add_argument('-m', '--multiprocess', action="store_true", help="enable multiprocess")
parser.add_argument('-o', '--output_path', required=True, help="path of the directory that will contain the catalog")
parser.add_argument('-p', '--projection', required=True, help="name of the projection to use")
parser.add_argument('-s', '--start_datetime', required=True, help="start date of the collection")
parser.add_argument('-t', '--title', required=True, help="title used in each asset")
# parse
args = parser.parse_args()
# check with some logic ?
manage_arguments(args)

if __name__ == "__main__":
    try:
        logger.info("start")
        start = datetime.now()
        convert = Convert(arguments=args)
        convert.convert(urls=bdod_urls)
        end = datetime.now()
        elapsed = end - start
        logger.info(f"end in {elapsed}")
    except Exception as e:
        logger.exception("global exception")
