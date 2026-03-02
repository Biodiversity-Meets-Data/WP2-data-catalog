### Misc

let's try another API

- use openeo for discoverable datasources
- Soil grid (https://rest.isric.org/soilgrids/v2.0/docs) -> stac json -> openeo
- https://github.com/gantian127/soilgrids
- https://rest.isric.org/soilgrids/v2.0/docs
- https://docs.openeo.cloud/getting-started/client-side-processing/#background
- https://docs.openeo.cloud/getting-started/client-side-processing/#stac-collections-and-items
- https://github.com/Open-EO/openeo-community-examples/blob/main/python/LoadStac/load-stac-item-example.ipynb

### Setup

Same setup as the copernicus api:

- use conda
- create new env

```bash
conda create --name openeo_api python=3.10
```

- activate env.

```bash
conda activate openeo_api
```

- install openeo

```bash
conda install conda-forge::openeo
```

- ~~install soilgrids~~

```bash
# bad idea, will use all memory while solving dependencies
conda install conda-forge::soilgrids
```

- install pystac

```bash
conda install conda-forge::pystac
```

- install rasterio

```bash
conda install conda-forge::rasterio
```

### geotiff -> stac

// TODO