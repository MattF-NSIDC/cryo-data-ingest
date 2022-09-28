from cryo_data_ingest.constants import NSIDC_PROVIDER_ID


def get_nsidc_collections() -> list:
    """Get a list of NSIDC's collection IDs for ingest."""
    ...


def get_collection_granules() -> list:
    """Get all granules in collection including the data file URL."""
    ...
