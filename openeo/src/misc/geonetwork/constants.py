class Constants:
    geonetwork_base_url = "https://metadatacatalogue.lifewatch.eu"
    # this returns an elasticsearch payload, with encoding issues
    geonetwork_query_path_old = "/srv/api/records?uuid="
    # this is better for encoding
    geonetwork_query_path = "/srv/api/records/"
    # formatting
    geonetwork_query_path_format = "/formatters/json"
    geonetwork_name = "LifeWatch ERIC Metadata Catalogue"
