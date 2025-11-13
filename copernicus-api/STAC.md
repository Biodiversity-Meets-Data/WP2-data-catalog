## API

### STAC

```http request
https://stac.dataspace.copernicus.eu/v1/api.html
```

Get collections

```http request
https://stac.dataspace.copernicus.eu/v1/collections
```

Get specific collection

```http request
https://stac.dataspace.copernicus.eu/v1/collections/sentinel-1-grd
```

Get items of a specific collection

```http request
https://stac.dataspace.copernicus.eu/v1/collections/sentinel-1-grd/items?limit=10
```

Get specific item of a specific collection

```http request
https://stac.dataspace.copernicus.eu/v1/collections/sentinel-1-grd/items/S1A_IW_GRDH_1SDH_20250730T090526_20250730T090543_060311_077ECF_8D8E_COG
```

Get filters

```http request
https://stac.dataspace.copernicus.eu/v1/queryables
```

Get filters for a specific collection

```http request
https://stac.dataspace.copernicus.eu/v1/collections/sentinel-1-grd/queryables
```

### Focus

Satellite:

- sentinel 2 
- sentinel 3 
- sentinel 5p

Level 2 data:
- wekeo has level 3
- stac has level 2 (and 1)


## Conversion

### Hard-coded stuff

EML attributes are referenced below

- \<metadataProvider\>: 
  - me as a metadata provider
- \<temporalCoverage\>: 
  - convert UTC datetime into date (YYYY-MM-DD)
- \<distribution\>:
  - redirect to landing page of the dataset on the Copernicus STAC browser
  - keep the other urls but redirect to documentation on how to access S3 bucket (which requires credentials)
- use 1 \<intellectualRights\> and 1 \<licensed\> instead of multiple \<licensed\>

### Query and conversion scripts

How to run, for all targeted collections (level 2 sentinel 2, 3, 5p)

```bash
python -m src.copernicus.stac.query_collections
```

For a specific collection

```bash
python -m src.copernicus.stac.query_collections <collection_id>
# where collection_id is the identifier being used in the copernicus stac browser
# ex: https://browser.stac.dataspace.copernicus.eu/collections/sentinel-2-l2a
```

Converted datasets will be saved in the folder hierarchy

```bash
./data/converted/stac/automatic/<collection_id>_converted_eml.xml
 ```
