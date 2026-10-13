class Constants:
    """constants used throughout the code"""
    max_nbr_tokens = 4
    token_separator = "_"
    isric_base_url = "https://isric.org/"
    soilgrids_base_url = "https://files.isric.org/soilgrids/latest/data_aggregated"
    soilgrids_dataset_uuid = "8315df49-bde3-4138-8f71-9b722f3afd06"
    BDOD_VALUE = "bdod"
    CEC_VALUE = "cec"
    CFVO_VALUE = "cfvo"
    CLAY_VALUE = "clay"
    NITROGEN_VALUE = "nitrogen"
    OCD_VALUE = "ocd"
    OCS_VALUE = "ocs"
    PHH2O_VALUE = "phh2o"
    SAND_VALUE = "sand"
    SILT_VALUE = "silt"
    SOC_VALUE = "soc"
    WV0010_VALUE = "wv0010"
    WV0033_VALUE = "wv0033"
    WV1500_VALUE = "wv1500"
    VARIABLE_NAMES = [BDOD_VALUE, CEC_VALUE, CFVO_VALUE, CLAY_VALUE, NITROGEN_VALUE, OCD_VALUE, OCS_VALUE, PHH2O_VALUE,
                      SAND_VALUE, SILT_VALUE, SOC_VALUE, WV0010_VALUE, WV0033_VALUE, WV1500_VALUE]
    band_names = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm", "0-30cm"]
    RESOLUTION_1000 = "1000"
    RESOLUTION_5000 = "5000"
    RESOLUTIONS = [RESOLUTION_1000, RESOLUTION_5000]
