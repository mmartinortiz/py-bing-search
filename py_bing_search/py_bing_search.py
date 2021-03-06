import urllib.request, urllib.error, urllib.parse
import requests
import time


class PyBingException(Exception):
    pass


class PyBingSearch(object):

    QUERY_URL = 'https://api.datamarket.azure.com/Bing/Search/Web' \
                 + '?Query={}&$top={}&$skip={}&$format={}'

    def __init__(self, api_key, safe=False):
        self.api_key = api_key
        self.safe = safe

    def search(self, query, limit=50, offset=0, format='json'):
        """ Returns the result list, and also the uri for next page (returned_list, next_uri)
        :param format: Output format. JSON by default
        :param offset:
        :param limit: Search results limit, 50 by default
        :param query: String to be searched
        """
        return self._search(query, limit, offset, format)

    def search_all(self, query, limit=50, format='json'):
        """ Returns a single list containing up to 'limit' Result objects
        :param query: String to be searched
        :param limit: Limit of the search, 50 by deafult
        :param format: Output format, JSON by default
        """
        results, next_link = self._search(query, limit, 0, format)
        while next_link and len(results) < limit:
            max = limit - len(results)
            more_results, next_link = self._search(query, max, len(results), format)
            if not more_results:
                break
            results += more_results
        return results

    def _search(self, query, limit, offset, format):
        """
        Returns a list of result objects, with the url for the next page bing search url.
        """
        url = self.QUERY_URL.format(urllib.parse.quote("'{}'".format(query)), limit, offset, format)
        r = requests.get(url, auth=("", self.api_key))
        try:
            json_results = r.json()
        except ValueError as vE:
            if not self.safe:
                raise PyBingException("Request returned with code {}, error msg: {}".format(r.status_code, r.text))
            else:
                print("[ERROR] Request returned with code {}, error msg: {}. \nContinuing in 5 seconds.".format(
                        r.status_code, r.text))
                time.sleep(5)
        try:
            next_link = json_results['d']['__next']
        except KeyError as kE:
            if not self.safe:
                raise PyBingException("Couldn't extract next_link: KeyError: {}".format(kE))
            else:
                print("Couldn't extract next_link: KeyError: {}".format(kE))
                time.sleep(3)
            next_link = ''
        return [Result(single_result_json) for single_result_json in json_results['d']['results']], next_link


class Result(object):
    """
    The class represents a SINGLE search result.
    Each result will come with the following:

    #For the actual results#
    title: title of the result
    url: the url of the result
    description: description for the result
    id: bing id for the page

    #Meta info#:
    meta.uri: the search uri for bing
    meta.type: for the most part WebResult
    """

    class _Meta(object):
        """
        Holds the meta info for the result.
        """
        def __init__(self, meta):
            self.type = meta['type']
            self.uri = meta['uri']

    def __init__(self, result):
        self.url = result['Url']
        self.title = result['Title']
        self.description = result['Description']
        self.id = result['ID']

        self.meta = self._Meta(result['__metadata'])
