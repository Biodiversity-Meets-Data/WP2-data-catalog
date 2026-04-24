### Intro

Let's try another API, this time to convert a resource to a STAC-compatible resource usable by OpenEO.
Bunch of links:

- use openeo for discoverable datasources
- Soil grid (https://rest.isric.org/soilgrids/v2.0/docs) -> stac json -> openeo
- https://data.isric.org/geonetwork/srv/eng/catalog.search#/home (geonetwork instance)
- https://github.com/gantian127/soilgrids
- https://rest.isric.org/soilgrids/v2.0/docs
- https://docs.openeo.cloud/getting-started/client-side-processing/#background
- https://docs.openeo.cloud/getting-started/client-side-processing/#stac-collections-and-items
- https://github.com/Open-EO/openeo-community-examples/blob/main/python/LoadStac/load-stac-item-example.ipynb

### Setup

Use miniforge instead of conda from rocky linux repositories: https://github.com/conda-forge/miniforge
Setup to automatically initialize after installation. Once base env is active:

- create new env (setup with the latest python 3)

```bash
conda create --name openeo_api python=3
```

- activate env.

```bash
conda activate openeo_api
```

- install openeo

```bash
conda install conda-forge::openeo
```

- install soilgrids (optional if using direct links to data repository)

```bash
conda install conda-forge::soilgrids
```

- install pystac, shapely, jsonschema, rasterio 

```bash
conda install conda-forge::pystac
conda install conda-forge::shapely
conda install conda-forge::jsonschema
conda install conda-forge::rasterio
# optional
conda install conda-forge::stac-validator
```

### geotiff -> stac

Use

- tutorial: https://stacspec.org/en/tutorials/2-create-stac-catalog-python/
- data: 
  - https://data.isric.org/geonetwork/srv/eng/catalog.search#/metadata/b5ca4bb7-7846-48d9-9af9-a0a4a0b94f23
  - https://files.isric.org/soilgrids/latest/data_aggregated/5000m/bdod/

```bash
python -m src.test_openeo \ 
  -b "data/input/soilgrids/bands.json" \ 
  -c "Soilgrids_collection" \ 
  -d "1905-04-01" \ 
  -s "1905-04-01" \ 
  -e "2016-07-05" \ 
  -p "EPSG:4326" \ 
  -t "SoilGrids250m 2.0 - Bulk density aggregated 5000m" \ 
  -i "data/input/soilgrids/highres/bdod" \ 
  -o "data/output/soilgrids/test_catalog/"
```

### Hierarchy

How to structure the catalog, see https://eo-college.org/topics/the-stac-catalog/

One collection per Soilgrids dataset:

```mermaid
flowchart TD
  TBD
```

One asset per file (depth), one item per variable:

```mermaid
flowchart TD
  C1(Main Catalog) --> C2
  C1(Main Catalog) --> C3
  C2(Soilgrids Collection) --> Cat1000
  C2(Soilgrids Collection) --> Cat5000
  C3(Other Collection)
  Cat1000(Catalog 1000) --> I1_bdod
  Cat1000(Catalog 1000) --> I1_other(Item ...)
  Cat1000(Catalog 1000) --> I1_cec
  I1_bdod(Item bdod) --> A1_bdod(Asset 0-5cm)
  I1_bdod(Item bdod) --> A2_bdod(Asset ...cm)
  I1_bdod(Item bdod) --> A3_bdod(Asset 100-200cm)
  I1_cec(Item cec) --> A1_cec(Asset 0-5cm)
  I1_cec(Item cec) --> A2_cec(Asset ...cm)
  I1_cec(Item cec) --> A3_cec(Asset 100-200cm)
  I1_other(Item ...) --> A1_other(Asset ...)
  Cat5000(Catalog 5000) --> I2_bdod 
  I2_bdod(Item ...)
```