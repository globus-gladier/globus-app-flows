import logging
import copy
import urllib
from globus_app_flows.collectors.collector import Collector
from globus_portal_framework import gsearch
from globus_portal_framework.gclients import load_search_client
from globus_portal_framework.gsearch import get_search_filters, get_search_query


log = logging.getLogger(__name__)


class SearchCollector(Collector):
    """A Search Collector is an object intended to understand and process data
    for a given index. Since each Globus Search Index can store data a little
    bit differently, this can be overridden to account for differences one
    index has over another."""

    DEFAULT_SEARCH_KWARGS = {"limit": 10000, "filters": []}

    def __init__(
        self,
        index,
        name="",
        query=None,
        filters=None,
        search_data=None,
        user=None,
        metadata=None,
        page=None,
    ):
        self.index = index
        self.name = name
        self.query = query
        self.filters = filters or []
        self._search_data = search_data or {}
        self.search_kwargs = {}
        self._has_searched = False
        self.user = user

        self.items = None

    def get_metadata(self):
        return {
            "index": self.index,
            "query": self.query,
            "filters": self.filters,
        }

    @classmethod
    def from_get_request(cls, request, index, *args, **kwargs):
        filters = get_search_filters(request)
        return cls(
            index, query=get_search_query(request), filters=filters, user=request.user
        )

    def get_item(self):
        if self.items == None:
            self.items = iter(self.search_data["gmeta"])
        return next(self.items)

    @property
    def search_data(self):
        if self._search_data and self._search_data.get("gmeta"):
            return self._search_data
        required = [self.index, self.query]
        if not all(required):
            log.warning(
                "Not enough data to conduct search, populating "
                f"collection with empty values (user: {self.user}"
            )
            self._search_data = {"gmeta": [], "count": 0}
            return self._search_data
        if self._has_searched is False:
            self._search_data = self.post_search()
            # Ensure only one search is done
            self._has_searched = True
        log.debug(
            f'{self.__class__}: Fetching {len(self._search_data["gmeta"])} Results'
        )
        return self._search_data

    @search_data.setter
    def search_data(self, value):
        self._search_data = value

    def post_search(self):
        """Gather results from Globus Search. Wraps
        globus_portal_framework.gsearch.post_search with optional ability to
        specify a project. Default filters can easily be added.
        **parameters**
        ``user`` The user, typically from request.user. None for unauthorized
          search.
        ``index`` The index name defined in settings.SEARCH_INDEXES
        ``project`` Filter based on project, if this index supports it. None
          for no project filter.
        ``kwargs`` Extra post_search kwargs. By Default, q=* and limit=10000
          are used.
        **returns**
        The result from globus_portal_framework.gsearch.post_search()
        **Example**
        post_search(
          'my-foo-index',
          request.user,
          'my-project-name'
          search_kwargs={q='bananas'}
          q='*',
          filters=globus_portal_framework.gsearch.get_search_filters(request),
          limit=1000
        )
        """
        skwargs = copy.deepcopy(self.DEFAULT_SEARCH_KWARGS)
        if skwargs["filters"]:
            skwargs["filters"] += self.filters
        else:
            skwargs["filters"] = self.filters
        skwargs.update(self.search_kwargs or {})

        skwargs["q"] = skwargs.get("q", self.query or "*")

        sc = load_search_client(self.user)
        index_data = gsearch.get_index(self.index)
        sdata = sc.post_search(index_data["uuid"], skwargs).data
        log.debug(f"Did post search with {self.__class__}: {skwargs}")
        return sdata

    def process_search_data(self):
        fields = gsearch.get_index(self.index).get("fields", [])
        psd = gsearch.process_search_data(fields, self.search_data["gmeta"])
        return {
            "search_results": psd,
            "count": self.search_data.get("count", 0),
            "total": self.search_data.get("total", 0),
        }

    def get_record(self, gmeta):
        return gmeta["entries"][0]["content"]

    def get_subjects(self):
        return [e["subject"] for e in self.search_data["gmeta"]]
