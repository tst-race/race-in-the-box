# Copyright 2023 Two Six Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import datetime
import logging
from ast import Set
from typing import Any, Dict, List, Optional, Tuple
from typing_extensions import TypedDict, NotRequired
from enum import Enum, auto
from opensearchpy import (
    OpenSearch as Elasticsearch,
    OpenSearchException as ElasticsearchException,
)
from opensearchpy.client import logger as es_logger, logging as es_logging
from rib.utils import general_utils

# Defaults
DEFAULT_SCROLL_SIZE = "60s"
DEFAULT_TIMEOUT = 60

es_logger.setLevel(es_logging.ERROR)
logger = logging.getLogger(__name__)

###
# Types
###


class Span(TypedDict):
    """Result of a query of JagerTracing"""

    trace_id: str
    span_id: str
    start_time: int
    source_persona: str


class MessageSpan(Span):
    """
    Trace with information about a Message

    Uses lower camel case to match tags making parsing easier
    """

    messageSize: int
    messageHash: str
    messageTestId: str
    messageFrom: str
    messageTo: str


class MessagePathSpan(Span):
    """Message path information"""

    connectionIds: str
    pluginId: str
    parentSpanId: str


class MessageStatus(general_utils.PrettyEnum):
    """Status of Message Trace on the network"""

    ERROR = auto()
    SENT = auto()
    RECEIVED = auto()
    CORRUPTED = auto()


class MessageTraceUi(TypedDict):
    """Role up of Messages for Ui"""

    status: MessageStatus
    send_span: NotRequired[MessageSpan]
    receive_span: NotRequired[MessageSpan]


class MessageTrace(TypedDict):
    """Role up of Messages"""

    total_time: float
    status: MessageStatus
    send_span: MessageSpan
    receive_span: MessageSpan


class LinkSpanAction(general_utils.PrettyEnum):
    """Actions of a Link Span"""

    CONNECTION_OPEN = auto()
    CONNECTION_CLOSED = auto()
    CONNECTION_SEND = auto()
    CONNECTION_RECV = auto()
    LINK_CREATED = auto()
    LINK_DESTROYED = auto()
    LINK_LOADED = auto()


class LinkSpan(Span):
    """Trace with information about a Link"""

    link_id: str
    action: LinkSpanAction
    channel_gid: str
    link_address: str
    personas: Set
    link_type: str
    transmission_type: str
    connection_type: str
    send_type: str
    reliable: str
    link_direction: str
    connection_id: str


###
# Get Message Data
###


def parse_span_base_info(span: Span, raw_span_info: Dict):
    """
    Purpose:
        Get base span info from elasticsearch query result
    Args:
        span: span to populate
        raw_span_info: record to parse
    """

    span["trace_id"] = raw_span_info["_source"]["traceID"]
    span["span_id"] = raw_span_info["_source"]["spanID"]
    span["start_time"] = raw_span_info["_source"]["startTime"]
    span["source_persona"] = raw_span_info["_source"]["process"]["serviceName"]


def parse_span_base_info_ui(span: Span, raw_span_info: Dict):
    """
    Purpose:
        Get base span info from elasticsearch query result (load in different timestamp for ui)
    Args:
        span: span to populate
        raw_span_info: record to parse
    """

    span["trace_id"] = raw_span_info["_source"]["traceID"]
    span["span_id"] = raw_span_info["_source"]["spanID"]
    span["start_time"] = raw_span_info["_source"]["startTimeMillis"]
    span["source_persona"] = raw_span_info["_source"]["process"]["serviceName"]


def get_message_spans(spans: List[Dict]):
    """
    Purpose:
        Get message spans from elasticsearch query result
    Args:
        spans: records to parse
    Return:
        source_persona_to_span: {source_persona: List[MessageSpans]}
        trace_id_to_span: {TraceId: List[MessageSpans]}
    """
    source_persona_to_span = {}
    trace_id_to_span = {}
    for span in spans:
        message = MessageSpan()

        # Get base span info
        parse_span_base_info(message, span)

        message_tags = [
            "messageSize",  # will be a string
            "messageHash",
            "messageTestId",
            "messageFrom",
            "messageTo",
        ]
        # Get Message specific info
        for tag in span["_source"]["tags"]:
            if tag["key"] in message_tags:
                message[tag["key"]] = tag["value"]

        # Add to return value
        trace_id_to_span.setdefault(message["trace_id"], [])
        source_persona_to_span.setdefault(message["source_persona"], [])

        trace_id_to_span[message["trace_id"]].append(message)
        source_persona_to_span[message["source_persona"]].append(message)

    return (source_persona_to_span, trace_id_to_span)


def get_message_spans_ui(spans: List[Dict]):
    """
    Purpose:
        Get message spans from elasticsearch query result (using ui specific timestamping)
    Args:
        spans: records to parse
    Return:
        source_persona_to_span: {source_persona: List[MessageSpans]}
        trace_id_to_span: {TraceId: List[MessageSpans]}
    """
    source_persona_to_span = {}
    trace_id_to_span = {}
    for span in spans:
        message = MessageSpan()

        # Get base span info for ui
        parse_span_base_info_ui(message, span)

        message_tags = [
            "messageSize",  # will be a string
            "messageHash",
            "messageTestId",
            "messageFrom",
            "messageTo",
        ]
        # Get Message specific info
        for tag in span["_source"]["tags"]:
            if tag["key"] in message_tags:
                message[tag["key"]] = tag["value"]

        # Add to return value
        trace_id_to_span.setdefault(message["trace_id"], [])
        source_persona_to_span.setdefault(message["source_persona"], [])

        trace_id_to_span[message["trace_id"]].append(message)
        source_persona_to_span[message["source_persona"]].append(message)

    return (source_persona_to_span, trace_id_to_span)


def get_message_span_tree(spans: List[Dict]):
    """
    Purpose:
        Get message spans from elasticsearch query result
    Args:
        spans: records to parse
    Return:
    """
    span_tree = {}
    for span in spans:
        message = MessagePathSpan()
        parse_span_base_info(message, span)
        message_path_tags = [
            "pluginId",
            "connectionIds",
        ]
        # Get Message specific info
        for tag in span["_source"]["tags"]:
            if tag["key"] in message_path_tags:
                message[tag["key"]] = tag["value"]

        if len(span["_source"]["references"]) > 0:
            parent_ref = span["_source"]["references"][0]
            message["parentSpanId"] = parent_ref["spanID"]

        span_tree.setdefault(message["trace_id"], [])
        span_tree[message["trace_id"]].append(message)
    return span_tree


def getMessageTraces(trace_id_to_span) -> List[MessageTrace]:
    """
    Purpose:
        Get Message Traces from spans. Each Trace ID should have 2 spans.
    Args:
        trace_id_to_span: Map of Trace IDs to 1-2 spans
    Return:
        messages: List of Messsage Traces
    """
    messages = []
    for trace_id, spans in trace_id_to_span.items():
        message = MessageTrace()
        for span in spans:
            if span["messageFrom"] == span["source_persona"]:
                message["send_span"] = span
            elif span["messageTo"] == span["source_persona"]:
                message["receive_span"] = span
        if message.get("send_span") and message.get("receive_span"):
            # Both send and receive spans were found, message was received
            # Determine Status
            if (
                message["send_span"]["messageHash"]
                == message["receive_span"]["messageHash"]
            ) and (
                message["send_span"]["messageSize"]
                == message["receive_span"]["messageSize"]
            ):
                message["status"] = MessageStatus.RECEIVED
            else:
                message["status"] = MessageStatus.CORRUPTED

            # Determine Time in seconds
            message["total_time"] = (
                message["receive_span"]["start_time"]
                - message["send_span"]["start_time"]
            ) / 1_000_000.0

        elif message.get("send_span"):
            # Send span found, receive is still missing
            message["status"] = MessageStatus.SENT
        else:
            # This case only happens if the send node fails to post to elasticsearch
            message["status"] = MessageStatus.ERROR
        messages.append(message)
    return messages


def get_message_traces_ui(trace_id_to_span) -> List[MessageTraceUi]:
    """
    Purpose:
        Get Message Traces from spans. Each Trace ID should have 2 spans.
    Args:
        trace_id_to_span: Map of Trace IDs to 1-2 spans
    Return:
        messages: List of Messsage Traces
    """
    messages = []
    for trace_id, spans in trace_id_to_span.items():
        message = MessageTraceUi()
        for span in spans:
            if span["messageFrom"] == span["source_persona"]:
                message["send_span"] = span
            elif span["messageTo"] == span["source_persona"]:
                message["receive_span"] = span
        if message.get("send_span") and message.get("receive_span"):
            # Both send and receive spans were found, message was received
            # Determine Status
            if (
                message["send_span"]["messageHash"]
                == message["receive_span"]["messageHash"]
            ) and (
                message["send_span"]["messageSize"]
                == message["receive_span"]["messageSize"]
            ):
                message["status"] = MessageStatus.RECEIVED
            else:
                message["status"] = MessageStatus.CORRUPTED

        elif message.get("send_span"):
            # Send span found, receive is still missing
            message["status"] = MessageStatus.SENT
        else:
            # This case only happens if the send node fails to post to elasticsearch
            message["status"] = MessageStatus.ERROR
        messages.append(message)
    return messages


def get_link_spans():
    """
    Get Link Spans from
    """
    # TODO Fill this out when moving inpect_links.py to a rib command
    pass


# ui users should use the get_message_list_spans() alternative version for handling pagination
def get_spans(es, results: list, scroll_size: str = DEFAULT_SCROLL_SIZE) -> list:
    """
    Purpose:
        Get list of spans from the query result object. Paginates through the results, invoking
        additional queries in the process.
    Args:
        results: raw records from query
        scroll_size: number of results to get on scroll
    Return:
    """

    if not results or "hits" not in results or "hits" not in results["hits"]:
        return []

    sid = results["_scroll_id"]
    hits = results["hits"]["hits"]
    records = []
    while len(hits) > 0:
        records.extend(hits)
        page = es.scroll(scroll_id=sid, scroll=scroll_size)
        sid = page["_scroll_id"]
        hits = page["hits"]["hits"]

    return records


def get_message_list_spans(results: Dict, page_size: int) -> Tuple[list, list, bool]:
    """
    Purpose:
        Get a list of spans from the query result object, a search_after value for pagination, and a more results flag
    Args:
        results: raw records from query
        page_size: number of results to get on the page
    Return:
        A tupled list of raw spans, a search_after list, and a boolean flag if there may be more pages of results
    """

    count = 0
    records = []
    search_after = []

    hits = results["hits"]["hits"]
    for trace in hits:
        spans = trace["inner_hits"]["spans"]["hits"]["hits"]
        records.extend(spans)
        search_after = trace["sort"]
        count += 1
        if count >= page_size:
            break

    has_more_pages = count >= page_size

    return records, search_after, has_more_pages


def create_query(
    persona: str = None,
    actions: List = None,
    trace_id: str = None,
    time_range: list = None,
    range_name: Optional[str] = None,
) -> Dict:
    """
    Purpose:
        Create query for Elasticsearch based on given criteria. Inputs are purposefully using
        terminology used elsewhere in RiB rather than elasticsearch terms. This function translates
        those RiB terms to elasticsearch terms to use in the query
    Args:
        persona: source node of span
        actions: List of actions to filter on
        trace_id: trace id to filter on
        time_range: time range to filter to
        range_name: Name of test range on which to filter
    Return:
        query
    """
    mustmatch = []
    if persona:
        mustmatch.append({"term": {"process.serviceName": persona}})
    if actions:
        mustmatch.append({"terms": {"operationName": actions}})
    if trace_id:
        mustmatch.append({"term": {"traceID": trace_id}})
    if range_name:
        mustmatch.append(
            {
                "nested": {
                    "path": "process.tags",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {"process.tags.key": "range-name"},
                                },
                                {"term": {"process.tags.value": range_name}},
                            ]
                        }
                    },
                }
            }
        )

    filters = [{"match_all": {}}]
    if time_range and len(time_range) > 0:
        filters.append({"range": {"startTimeMillis": dict(time_range)}})

    query = {
        "query": {
            "bool": {
                "must": mustmatch,
                "should": [],
                "filter": filters,
                "must_not": [],
            }
        }
    }

    return query


# this is a new query func to support ui pagination
def create_message_list_query(
    persona: str = None,
    actions: List = None,
    trace_id: str = None,
    time_range: list = None,
    search_after_vals: list = [],
    range_name: Optional[str] = None,
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    test_id: Optional[str] = None,
) -> Dict:
    """
    Purpose:
        Create a special message query for Elasticsearch based on given criteria. Inputs are purposefully using
        terminology used elsewhere in RiB rather than elasticsearch terms. This function translates
        those RiB terms to elasticsearch terms to use in the query
    Args:
        persona: source node of span
        actions: List of actions to filter on
        trace_id: trace id to filter on
        time_range: time range to filter to
        search_after_vals: List of vals to use as search_after
        range_name: Name of test range on which to filter
        sender: sender node to filter on
        recipient: reciever node to filter on
        test_id: test ID on which to filter
    Return:
        query
    """
    mustmatch = []

    if persona:
        mustmatch.append({"term": {"process.serviceName": persona}})
    if actions:
        mustmatch.append({"terms": {"operationName": actions}})
    if trace_id:
        mustmatch.append({"term": {"traceID": trace_id}})
    if range_name:
        mustmatch.append(
            {
                "nested": {
                    "path": "process.tags",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {"process.tags.key": "range-name"},
                                },
                                {"term": {"process.tags.value": range_name}},
                            ]
                        }
                    },
                }
            }
        )
    if sender:
        mustmatch.append(
            {
                "nested": {
                    "path": "tags",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {"tags.key": "messageFrom"},
                                },
                                {"term": {"tags.value": sender}},
                            ]
                        }
                    },
                }
            }
        )
    if recipient:
        mustmatch.append(
            {
                "nested": {
                    "path": "tags",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {"tags.key": "messageTo"},
                                },
                                {"term": {"tags.value": recipient}},
                            ]
                        }
                    },
                }
            }
        )
    if test_id:
        mustmatch.append(
            {
                "nested": {
                    "path": "tags",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {"tags.key": "messageTestId"},
                                },
                                {"term": {"tags.value": test_id}},
                            ]
                        }
                    },
                }
            }
        )

    filters = [{"match_all": {}}]
    if time_range and len(time_range) > 0:
        filters.append({"range": {"startTimeMillis": dict(time_range)}})

    query = {
        "collapse": {
            "field": "traceID",
            "inner_hits": {"name": "spans", "size": 2},
        },
        "query": {
            "bool": {
                "must": mustmatch,
                "should": [],
                "filter": filters,
                "must_not": [],
            }
        },
    }

    if search_after_vals:
        query["search_after"] = search_after_vals

    return query


def do_message_list_query(
    es: Elasticsearch,
    query: Dict,
    page_size: int,
    reverse_sort: bool = False,
) -> Dict:
    """
    Purpose:
        Perform an initial Elasticsearch query if search_vals is blank, otherwise perform a search_after
    Args:
        es: the elasticsearch instance
        query: the query to be run
        page_size: number of results to get on a page
        reverse_sort: determine if the returned data should be reverse sorted
    Return:
        results: returns the link artifacts
    """

    sort = "traceID:"
    if not reverse_sort:
        sort += "asc"
    else:
        sort += "desc"

    try:
        results = es.search(
            body=query,
            sort=sort,
            docvalue_fields="startTimeMillis",
            size=page_size,
            request_timeout=DEFAULT_TIMEOUT,
        )
    except ElasticsearchException as err:
        print(f"Search error: {err}")
        results = None

    return results


def do_query(es: Elasticsearch, query: Dict) -> Dict:
    """Performs an elasticsearch query to retrieve link artifacts"""

    try:
        results = es.search(
            body=query,
            sort="startTimeMillis:asc",
            docvalue_fields="startTimeMillis",
            scroll=DEFAULT_SCROLL_SIZE,
            request_timeout=DEFAULT_TIMEOUT,
        )
    except ElasticsearchException as err:
        print(f"Search error: {err}")
        results = None
    return results


def log_deployment_metadata(
    es: Elasticsearch, name: str, metadata: Dict[str, Any], indexName: str
) -> bool:
    """Logs deployment meta-data to given Elasticsearch index"""

    # Check if index exists
    indexExists = es.indices.exists(index=indexName)
    if not indexExists:
        es.indices.create(indexName)

    ts = datetime.datetime.utcnow()
    milliseconds = str(round(ts.timestamp() * 1000))

    doc = {
        "name": name,
        "metadata": metadata,
        "timestamp": ts,
        "timestamp_ms": milliseconds,
    }

    resp = es.index(index=indexName, body=doc)
    logger.debug(f"rib command log operation returned: {resp}")


class LinkQueryMethod(Enum):
    CONNECTION_EVER = auto()
    CONNECTION_CURRENT = auto()
    LINK_EVER = auto()
    LINK_CURRENT = auto()
    # TODO
    # PACKAGE_EVER = auto()
    # TODO
    # PACKAGE_CURRENT = auto()


###
# Link Extractor
###


class ESLinkExtractor:
    """
    A class that encapsulates elastic search query functionality

    Example Usage:

    from rib.utils.elasticsearch_utils import ESLinkExtractor

    qObj = ESLinkExtractor("elasticsearch")
    df = qObj.do_query(timeout=200, date_range=[["gte", "now-1h/h"]])
    """

    # Defaults
    DEFAULT_SCROLL_SIZE = "60s"
    DEFAULT_TIMEOUT = 60
    DEFAULT_SIZE = -1

    # Keywords of interest
    _action_terms_connection = [
        "CONNECTION_OPEN",
        "CONNECTION_CLOSED",
        "CONNECTION_SEND",
        "CONNECTION_RECV",
    ]
    _action_terms_link = [
        "LINK_CREATED",
        "LINK_DESTROYED",
        "LINK_LOADED",
    ]

    _wanted_tags = [
        "size",
        "linkId",
        "channelGid",
        "linkAddress",
        "personas",
        "linkType",
        "transmissionType",
        "connectionType",
        "sendType",
        "reliable",
        "linkDirection",
        "connectionId",
    ]
    _source_fields = [
        "traceID",
        "spanID",
        "operationName",
        "startTimeMillis",
    ]
    _search_fields = list(_source_fields)
    _search_fields.extend("tags.*")

    def __init__(
        self,
        es_host: str,
        res_size: int = DEFAULT_SIZE,
        scroll_size: str = DEFAULT_SCROLL_SIZE,
        timeout=120,
        max_retries=5,
        retry_on_timeout=True,
    ):
        """
        Parameters
        ----------
        es_host: str
            <hostname>[:<port>] of the elasticsearch instance

        res_size: int
            Number of records requested

        scroll_size: str
            A scroll size value (e.g. "60s")

        """

        self.es = Elasticsearch(
            [es_host],
            timeout=timeout,
            max_retries=max_retries,
            retry_on_timeout=retry_on_timeout,
        )
        self.res_size = res_size
        self.scroll_size = scroll_size

    def create_query(
        self,
        persona: str = None,
        actions: List = None,
        trace_ids: List = None,
        time_range: list = None,
        range_name: Optional[str] = None,
    ) -> Dict:
        """
        Purpose:
            Create query for Elasticsearch based on given criteria. Inputs are purposefully using
            terminology used elsewhere in RiB rather than elasticsearch terms. This function translates
            those RiB terms to elasticsearch terms to use in the query
        Args:
            persona: source node of span
            actions: List of actions to filter on
            trace_ids: trace ids to filter on
            time_range: time range to filter to
            range_name: Name of test range on which to filter
        Return:
            query
        """
        mustmatch = []
        if persona:
            mustmatch.append({"term": {"process.serviceName": persona}})
        if actions:
            mustmatch.append({"terms": {"operationName": actions}})
        if trace_ids:
            mustmatch.append({"terms": {"traceID": trace_ids}})
        if range_name:
            mustmatch.append(
                {
                    "nested": {
                        "path": "process.tags",
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "term": {"process.tags.key": "range-name"},
                                    },
                                    {"term": {"process.tags.value": range_name}},
                                ]
                            }
                        },
                    }
                }
            )

        filters = [{"match_all": {}}]
        if time_range and len(time_range) > 0:
            filters.append({"range": {"startTimeMillis": dict(time_range)}})

        query = {
            "query": {
                "bool": {
                    "must": mustmatch,
                    "should": [],
                    "filter": filters,
                    "must_not": [],
                }
            }
        }

        return query

    def extract_link_records(self, results: list) -> list:
        """Convenience routine to extract individual records from the result object.

        Extracts required fields from the search results and returns a list of dicts.
        Paginates through the results, invoking additional queries in the process.

        Parameters
        ----------

        results: list
            Results returned from a query

        Returns
        -------
        list
            A list of dicts
        """

        if not results or "hits" not in results or "hits" not in results["hits"]:
            return []

        sid = results["_scroll_id"]
        hits = results["hits"]["hits"]
        records = []
        while len(hits) > 0:
            for res in hits:
                # Get the basic set of fields
                rec = {
                    k: res["_source"][k]
                    for k in ESLinkExtractor._source_fields
                    if k in res["_source"]
                }

                # Get the required tags
                for d in res["_source"]["tags"]:
                    if d["key"] in ESLinkExtractor._wanted_tags:
                        rec[d["key"]] = d["value"]

                # Add the service (node) name
                if (
                    "process" in res["_source"]
                    and "serviceName" in res["_source"]["process"]
                ):
                    rec["serviceName"] = res["_source"]["process"]["serviceName"]
                else:
                    rec["serviceName"] = ""

                records.append(rec)

                # Return if we've gathered required number of records
                if self.res_size > 0 and len(records) >= self.res_size:
                    return records

            # pylint: disable-next=unexpected-keyword-arg
            page = self.es.scroll(scroll_id=sid, scroll=self.scroll_size)
            sid = page["_scroll_id"]
            hits = page["hits"]["hits"]

        return records

    def do_query(
        self,
        query: Dict = None,
        timeout: int = DEFAULT_TIMEOUT,
        date_range: list = None,
        services: list = None,
        method: LinkQueryMethod = LinkQueryMethod.LINK_CURRENT,
        range_name: Optional[str] = None,
    ) -> Dict:
        """Performs an elasticsearch query to retrieve link artifacts

        Parameters
        ----------

        query: Dict
            A prepared query structure

        timeout: int
            The number of seconds to wait prior to giving up

        date_range: list
            A list of [name,value] pairs that specify the date interval for the search

        services: List
            The service (node) names to match in the search

        method: LinkQueryMethod
            Type of edges to process

        range_name: str
            Name of test range on which to filter

        Returns
        -------
        Dict
            results of the query

        """

        if not query:
            # Construct the query if it is not given directly
            mustmatch = []
            if services:
                mustmatch.extend([{"terms": {"process.serviceName": services}}])

            if range_name:
                mustmatch.extend(
                    [
                        {
                            "nested": {
                                "path": "process.tags",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "term": {
                                                    "process.tags.key": "range-name"
                                                },
                                            },
                                            {
                                                "term": {
                                                    "process.tags.value": range_name
                                                }
                                            },
                                        ]
                                    }
                                },
                            }
                        }
                    ]
                )

            if method in [LinkQueryMethod.LINK_EVER, LinkQueryMethod.LINK_CURRENT]:
                action_terms = ESLinkExtractor._action_terms_link
            else:
                # For connections, we need to take both links and connections
                # into account
                action_terms = (
                    ESLinkExtractor._action_terms_connection
                    + ESLinkExtractor._action_terms_link
                )
            mustmatch.extend([{"terms": {"operationName": action_terms}}])

            filters = [{"match_all": {}}]
            if date_range and len(date_range) > 0:
                filters.append({"range": {"startTimeMillis": dict(date_range)}})

            query = {
                "query": {
                    "bool": {
                        "must": mustmatch,
                        "should": [],
                        "filter": filters,
                        "must_not": [],
                    }
                }
            }

        try:
            # pylint: disable=unexpected-keyword-arg
            results = self.es.search(
                body=query,
                #    _source=ESLinkExtractor.search_fields,
                sort="startTimeMillis:asc",
                size=self.res_size,
                docvalue_fields="startTimeMillis",
                scroll=self.scroll_size,
                request_timeout=timeout,
            )
            # pylint: enable=unexpected-keyword-arg
        except ElasticsearchException as err:
            print(f"Search error: {err}")
            results = None
        return results

    def get_spans(self, results: list, scroll_size: str = DEFAULT_SCROLL_SIZE) -> list:
        """
        Purpose:
            Get list of spans from the query result object. Paginates through the results, invoking
            additional queries in the process.
        Args:
            results: raw records from query
            scoll_size: number of results to get on scroll
        Return:
            records: list of records
        """

        if not results or "hits" not in results or "hits" not in results["hits"]:
            return []

        sid = results["_scroll_id"]
        hits = results["hits"]["hits"]
        records = []
        while len(hits) > 0:
            records.extend(hits)
            # pylint: disable-next=unexpected-keyword-arg
            page = self.es.scroll(scroll_id=sid, scroll=self.scroll_size)
            sid = page["_scroll_id"]
            hits = page["hits"]["hits"]

        return records

    def get_path_graph(self, traceids, range_name):
        """
        Purpose:
            Get a graph from traceId to each node traversed
        Args:
            traceids: list of trace Ids
            range_name: name of test range on which to filter
        Return:
            persona_tree: list of edges in a graph that have
                   the form (source, dest, pluginID, connectionId)
        """

        query = self.create_query(trace_ids=traceids, range_name=range_name)
        results = self.do_query(query)
        spans = self.get_spans(results)
        message_path_spans = get_message_span_tree(spans)

        span_tree = {}
        persona_map = {}
        persona_tree = {}

        # First build a tree from trace Id to each span id
        # while also creating a mapping between the span id and the persona
        for trace_id in message_path_spans:
            for message in message_path_spans[trace_id]:
                span_tree.setdefault(message["trace_id"], [])
                child_node = message["span_id"]
                persona_map[child_node] = message["source_persona"]
                if "parentSpanId" in message:
                    parent_node = message["parentSpanId"]
                    span_tree[message["trace_id"]].append(
                        (parent_node, child_node, message)
                    )

        # Translate span information to persona information
        for t in span_tree:
            persona_tree[t] = set()
            for p, c, m in span_tree[t]:
                if p in persona_map and c in persona_map:
                    parent_node = persona_map[p]
                    child_node = persona_map[c]
                    # Only save edges that have complete information
                    if parent_node != child_node and all(
                        name in m for name in ["pluginId", "connectionIds"]
                    ):
                        persona_tree[t].add(
                            (parent_node, child_node, m["pluginId"], m["connectionIds"])
                        )

        return persona_tree
