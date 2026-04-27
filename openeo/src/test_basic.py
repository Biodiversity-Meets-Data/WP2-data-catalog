import argparse
from src.convert_single_asset import ConvertSingleAsset

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items, single asset per item')
# setup arguments
# parser.add_argument('-b', '--bands_path', required=True, help="path of the json file where bands are defined")
parser.add_argument('-c', '--collection_id', required=True, help="collection identifier")
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


if __name__ == "__main__":
    convert = ConvertSingleAsset(arguments=args)
    convert.run()
