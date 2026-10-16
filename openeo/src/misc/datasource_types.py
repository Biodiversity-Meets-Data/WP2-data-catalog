from enum import StrEnum


class DatasourceTypes(StrEnum):
    SOILGRIDS = "soilgrids"
    BIO_ORACLE = "bio_oracle"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
