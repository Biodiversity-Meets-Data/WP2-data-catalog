import requests
import json

host = "https://stac.dataspace.copernicus.eu/v1/"
end_point = "collections/"
parameters = "sentinel-1-grd"
url = host + end_point + parameters

response = requests.get(url)
result = response.json()

print(json.dumps(result, indent=4))