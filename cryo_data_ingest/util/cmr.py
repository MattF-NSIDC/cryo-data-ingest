import csv
import json
import logging
import requests
from typing import Iterator, TypedDict

from cryo_data_ingest.constants.cmr import (
    CMR_COLLECTIONS_SEARCH_URL,
    CMR_GRANULES_SEARCH_URL,
    CMR_NSIDC_PROVIDER_ID,
    CMR_PAGE_SIZE,
)
from cryo_data_ingest.constants.paths import JSON_STORAGE_DIR
from cryo_data_ingest.constants.requests import REQUESTS_TIMEOUT

# TODO: Move logging setup to another file
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Collection(TypedDict):
    id: str
    short_name: str
    version_id: str


class Granule(TypedDict):
    id: str
    url: str


class OutputGranule(TypedDict):
    """Just the information needed to create a datalad URL file."""
    who: str
    link: str


def _page_cmr_results(
    cmr_query_url: str,
    /,
    *,
    query_params: dict = {},
    query_headers: dict = {},
) -> Iterator[str]:
    """Generate results until there are no more pages.
    
    Results are returned as raw strings, not parsed as any specific format. Consumer is
    expected to do e.g. `json.loads` on the results.
    """
    CMR_SEARCH_HEADER = 'CMR-Search-After'
    first_pass = True
    while True:
        response = requests.get(
            cmr_query_url,
            params=query_params,
            headers=query_headers,
            timeout=REQUESTS_TIMEOUT,
        )

        if not response.ok:
            raise SearchError(
                f'CMR search failed with error: {response.content}',
            )

        if first_pass == True:
            logger.debug(f"Got {response.headers['CMR-Hits']} for query {cmr_query_url}")
            first_pass = False

        results_page = response.content

        # If no search-after header is returned, we've got everything already and can
        # stop iterating.
        if CMR_SEARCH_HEADER not in response.headers:
            logger.debug('End of CMR results')
            return

        yield results_page

        # Update the headers to get the next set of results on the next query:
        try:
            query_headers[CMR_SEARCH_HEADER] = response.headers.get(CMR_SEARCH_HEADER)
        except Exception as e:
            breakpoint()
            ...


def _collection_readable_id(collection: Collection) -> str:
    return f"{collection['short_name']}.{collection['version_id']}"


def get_nsidc_collections() -> Iterator[Collection]:
    """Get a list of NSIDC's collection IDs for ingest.

    WARNING: NSIDC has 485 at time of writing, but we should still page through the
    results in case the number balloons in the future.

    TODO: Pass JSON params instead of putting them in URL
    """
    cmr_query_url = (
        f'{CMR_COLLECTIONS_SEARCH_URL}?page_size={CMR_PAGE_SIZE}'
        f'&provider_short_name={CMR_NSIDC_PROVIDER_ID}'
    )
    # TODO: Use the paging algorithm
    response = requests.get(cmr_query_url, timeout=REQUESTS_TIMEOUT)
    if not response.ok:
        raise RuntimeError(f'CMR request failed with error: {response.content}')
    
    response_json = json.loads(response.content)
    collections_json = response_json['feed']['entry']
    logger.info(
        f'Found {len(collections_json)} collections with provider'
        f' {CMR_NSIDC_PROVIDER_ID}'
    )

    for collection_json in collections_json:
        yield {
            'id': collection_json['id'],
            'short_name': collection_json['short_name'],
            'version_id': collection_json['version_id'],
        }


def get_collection_granules(collection: Collection) -> Iterator[Granule]:
    """Get all granules in collection including the data file URL."""
    cmr_query_url = (
        f'{CMR_GRANULES_SEARCH_URL}?page_size={CMR_PAGE_SIZE}'
        f"&collection_concept_id={collection['id']}"
    )
    for page in _page_cmr_results(cmr_query_url):
        page_decoded = page.decode('utf-8')
        page_dicts = csv.DictReader(page_decoded.splitlines(), delimiter=',')
        for granule in page_dicts:
            # NOTE: Online Access URLs sounds like it could contain multiple URLs, but
            # what is the delimiter? I can't find it documented _anywhere_. This doc
            # seems to indicate the possibility of multiple URL entries, but doesn't
            # describe their response format.
            url = granule['Online Access URLs']
            if not url:
                logger.debug(f'Encountered empty URL: {granule}')
                continue

            yield {
                "id": granule['Granule UR'],
                "url": url,
            }


def write_collection_granules(collection: Collection) -> None:
    collection_readable_id = _collection_readable_id(collection)

    granules = list(get_collection_granules(collection))
    if len(granules) == 0:
        logger.info(f'{collection_readable_id} has 0 granules. Skipping!')
        return

    logger.info(
        f'Creating file for {collection_readable_id} ({len(granules)}'
        ' granules)...'
    )

    output_granules: list[OutputGranule] = [
        {'who': collection_readable_id, 'link': g['url']}
        for g in granules
    ]

    collection_fp = JSON_STORAGE_DIR / f'{collection_readable_id}.json'

    JSON_STORAGE_DIR.mkdir(exist_ok=True)
    with open(collection_fp, 'w') as f:
        json.dump(output_granules, f, indent=2)
    logger.info(f'Wrote {collection_fp}')


def write_collections_granules() -> None:
    for collection in get_nsidc_collections():
        write_collection_granules(collection)


if __name__ == '__main__':
    write_collections_granules()
