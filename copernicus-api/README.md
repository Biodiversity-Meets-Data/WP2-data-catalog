## Conversion to eml

### Wekeo API vs Copernicus STAC API

These scripts were originally intended for querying wekeo API, but were later targeted towards Copernicus STAC API.
Some code is shared between the two, the procedure being the same:

- query API
- pick relevant attributes from json payload
- build an eml file using third-party libraries (with some validation og the eml/xml)

There are dedicated readme files for each API. Wekeo scripts use conda environment, and by extension STAC does as well.
