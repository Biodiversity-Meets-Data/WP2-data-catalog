import argparse
from src.convert_multiple_assets import ConvertMultipleAssets

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items, multiple assets per item')
# setup arguments
parser.add_argument('-d', '--datetime', required=True, help="datetime added to each item")
parser.add_argument('-e', '--end_datetime', required=True, help="end date of the collection")
parser.add_argument('-o', '--output_path', required=True, help="path of the directory that will contain the catalog")
parser.add_argument('-s', '--start_datetime', required=True, help="start date of the collection")
# parse
args = parser.parse_args()


if __name__ == "__main__":
    convert = ConvertMultipleAssets(arguments=args)
    convert.run()
