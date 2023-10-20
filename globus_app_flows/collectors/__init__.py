import logging

# from .search import SearchCollector
from django.utils.module_loading import import_string


log = logging.getLogger(__name__)


def get_collector(dotted_class_string: str) -> object:
    return import_string(dotted_class_string)
