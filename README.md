# Cryo Data Ingest

The idea:

* Discover data collections using a metadata provider (CMR in particular; we can make it
  pluggable in the future if other suitable providers exist)
* Associate each collection with a cryo-data datalad repository
* Add a data URL for each granule to the associated cryo-data repository
* Routine updates: If a collection is still "active", i.e. producing new data, update
  the associated cryo-data repository to reflect all current granules in the dataset

*Collection*: A data product; a  collection of datasets.

*Granule*: A dataset in a collection corresponding to a single measurement, e.g. a
swath of data, a day of data, or 8 hours of data, depending on the resolution of the
collection.


## Usage

_In early development. The following instructions are temporary._

0. Set up conda environment (`conda env create`)
1. Activate conda environment (`conda activate cryo-data-ingest`)
2. Run the "main script" from the root of this repo:

    ```
    PYTHONPATH=. python cryo_data_ingest/util/cmr.py
    ```
