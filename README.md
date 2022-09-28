# Cryo Data Ingest

The idea:

* Discover datasets using a metadata provider (CMR in particular; we can make it
  pluggable in the future if other suitable providers exist)
* Associate each dataset with a cryo-data datalad repository
* If a dataset is still "active", i.e. producing new data, update the associated
  cryo-data repository to reflect all current data files in the dataset.

*Dataset*: A collection of data files. CMR calls these "collections".

*Data file*: A file in a data set. CMR "granules" may contain multiple data files, e.g.
separate metadata files or browse images associated with the real data file. We are
probably only interested in a single file in each granule which contains measurements.
