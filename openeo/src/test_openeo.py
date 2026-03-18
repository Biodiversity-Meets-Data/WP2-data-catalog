import traceback
import argparse
from urllib import parse
from convert import Convert


def manage_arguments(arguments):
    """
    TODO
    maybe infer start_datetime from datetime
    """


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
parser.add_argument('-b', '--bands_path', required=True)
parser.add_argument('-d', '--datetime', required=True)
parser.add_argument('-e', '--end_datetime', required=True)
parser.add_argument('-i', '--input_path')
parser.add_argument('-o', '--output_path', required=True)
parser.add_argument('-p', '--projection', required=True)
parser.add_argument('-s', '--start_datetime', required=True)
parser.add_argument('-t', '--title', required=True)
# parse
args = parser.parse_args()
# check with some logic
manage_arguments(args)

try:
    convert = Convert(arguments=args)
    convert.convert(urls=bdod_urls)
except Exception as e:
    print(traceback.format_exc())
