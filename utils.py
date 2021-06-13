from models import check_feed
import xmltodict

"""
Since we don't know where the actual feed (list of items) begins we should search for an entry point
from which the Feed object will be created. This function recursively searches for a list of items and
returns a list of keys which we need to get to the actual feed start
"""


def search_for_entry_point(feed: dict, keys: list) -> list:
    last_key: str = ""
    for key, value in feed.items():
        if type(value) == list:
            keys.append(key)
            return keys
        last_key = key
    keys.append(last_key)
    search_for_entry_point(feed[last_key], keys)
    return keys


"""
This function is similar to the previous one, it recursively searches for the namespace in the initial feed
dictionary, returns it if there is one, otherwise returns an empty string. "if type(value) == list" part is
used for breaking out from the recursion once we reach the feed start, because namespace can't be found there
and there will be an error raised because on the next run of the recursion we will try to iterate through list
with a method which is not suitable for it
"""


def search_for_namespace(feed: dict) -> str:
    last_key: str = ""
    namespace: str = ""
    for key, value in feed.items():
        if type(value) == list:
            return namespace
        if key == "@xmlns:g":
            namespace = value
            return namespace
        last_key = key
    namespace = search_for_namespace(feed[last_key])
    return namespace


"""
This function gets a list of items for building the Feed object using the list of keys found by 
search_for_entry_point() function and returns a list containing a list of items
"""


def get_items_list(feed: dict, keys: list) -> list:
    for key in keys:
        feed = feed[key]
    return feed


"""
Feed processing function which uses all of the above functions to create a valid feed dictionary
which is then passed to models.check_feed()
"""


def process_feed(feed: str) -> dict:
    feed_dict: dict = xmltodict.parse(feed)
    keys: list = search_for_entry_point(feed_dict, [])
    feed_dict = {"namespace": search_for_namespace(feed_dict),
                 "items": get_items_list(feed_dict, keys)}
    feed_information: dict = check_feed(feed_dict).dict()
    return feed_information
