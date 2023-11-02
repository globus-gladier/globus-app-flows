import logging
import copy
import urllib
from collections import deque
from django.contrib.auth.models import User
from globus_app_flows.collectors.collector import Collector
from globus_portal_framework.gclients import load_transfer_client


log = logging.getLogger(__name__)


class TransferCollector(Collector):
    """A Transfer collector can iterate over a given Globus Collection and
    collect datasets."""

    # MAX_DEPTH = 3
    SKIP_FOLDERS = []
    SKIP_FILES = True

    def __init__(
        self,
        collection: str,
        path: str,
        max_depth: int = 0,
        name="",
        user: User = None,
    ):
        self.collection = collection
        self.path = path
        self.max_depth = 0
        self.name = name
        self.user = user

        self.items = None

    def get_metadata(self):
        return {
            "collection": self.collection,
            "path": self.path,
            "depth": self.max_depth,
        }

    @classmethod
    def from_get_request(cls, request, *args, **kwargs):
        return cls(user=request.user)

    def get_transfer_client(self):
        return load_transfer_client(self.user)

    def get_item(self):
        if self.items == None:
            self.items = deque()
            self.items.append((self.path, "", 0))
            self.items = self._recursive_ls_helper(
                self.get_transfer_client(),
                self.collection,
                self.items,
                2,
                self.SKIP_FOLDERS,
            )
        next_item = next(self.items)
        if next_item["type"] == "dir" and next_item["name"] in self.SKIP_FOLDERS:
            log.debug(f"SKIPPING {next_item['name']} because it sucks!")
            return self.get_item()
        elif self.SKIP_FILES is True and next_item["type"] == "file":
            return self.get_item()
        return next_item

    def _recursive_ls_helper(self, tc, ep, queue, max_depth, skip=None):
        while queue:
            abs_path, rel_path, depth = queue.pop()
            path_prefix = rel_path + "/" if rel_path else ""

            res = tc.operation_ls(ep, path=abs_path)

            if depth < max_depth:
                queue.extend(
                    (
                        res["path"] + item["name"],
                        path_prefix + item["name"],
                        depth + 1,
                    )
                    for item in res["DATA"]
                    if item["type"] == "dir" and item["name"] not in skip
                )
            for item in res["DATA"]:
                item["name"] = path_prefix + item["name"]
                yield item
