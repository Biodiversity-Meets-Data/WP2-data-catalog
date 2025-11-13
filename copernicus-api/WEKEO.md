### Setup

Main procedure is at https://help.wekeo.eu/en/articles/6751608-how-to-use-the-hda-api-in-python

- install conda
- create conda env
- either set default conda env. or activate conda env. 

```bash
conda activate wekeo_api
```

- install wekeo python library
- install pip
- install metapype https://github.com/PASTAplus/metapype-eml
- (optional) install mypy for type hinting
- (intellij) select conda env as python interpreter


### Steps

- get one or several or all datasets (json)
- for each dataset (json), 
  - parse content, create structure
  - validate
  - export as eml (xml)


### Conversion issues

- required eml nodes may be unknown (ex: end date for a running dataset)
- creator/contact/associated party (eml) do not necessarily match responsible party (json) 
- individual names (json) missing, not given name or surname
- terms (json) do not necessarily match license/distribution (eml)
- distribution (eml) vs distributor/distribution (json)


### WEkEO web interface vs API

Web interface exposes slightly different data versus the API. Most of the time metadata is mentioned, the following is the actual HTTP request that fetches data for the interface:

```http request
https://moi-be.wekeo.eu/api/dataset/EO:EUM:DAT:SENTINEL-3:SR_1_SRA___
```

There is a **rawMetadata** property in the JSON payload that contains the XML file content (iso19139).

