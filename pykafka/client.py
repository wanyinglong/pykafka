"""
Author: Keith Bourgoin, Emmett Butler
"""
__license__ = """
Copyright 2015 Parse.ly, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__all__ = ["KafkaClient"]

from .handlers import ThreadingHandler, GEventHandler
import logging

from .cluster import Cluster
from .handlers import ThreadingHandler


log = logging.getLogger(__name__)


class KafkaClient(object):
    """
    A high-level pythonic client for Kafka

    NOTE: `KafkaClient` holds weak references to `Topic` instances via
    :class:`pykafka.cluster.TopicDict`. To perform operations directly on these topics,
    such as examining their partition lists, client code must hold a strong reference to
    the topics it cares about. If client code doesn't need to examine `Topic` instances
    directly, no strong references are necessary.
    """
    def __init__(self,
                 hosts='127.0.0.1:9092',
                 zookeeper_hosts=None,
                 socket_timeout_ms=30 * 1000,
                 offsets_channel_socket_timeout_ms=10 * 1000,
                 use_greenlets=False,
                 exclude_internal_topics=True,
                 source_address='',
                 ssl_config=None):
        """Create a connection to a Kafka cluster.

        Documentation for source_address can be found at
        https://docs.python.org/2/library/socket.html#socket.create_connection

        :param hosts: Comma-separated list of kafka hosts to which to connect.
            If `ssl_config` is specified, the ports specified here are assumed
            to be SSL ports
        :type hosts: bytes
        :param zookeeper_hosts: KazooClient-formatted string of ZooKeeper hosts to which
            to connect. If not `None`, this argument takes precedence over `hosts`
        :type zookeeper_hosts: bytes
        :param socket_timeout_ms: The socket timeout (in milliseconds) for
            network requests
        :type socket_timeout_ms: int
        :param offsets_channel_socket_timeout_ms: The socket timeout (in
            milliseconds) when reading responses for offset commit and
            offset fetch requests.
        :type offsets_channel_socket_timeout_ms: int
        :param use_greenlets: Whether to perform parallel operations on greenlets
            instead of OS threads
        :type use_greenlets: bool
        :param exclude_internal_topics: Whether messages from internal topics
            (specifically, the offsets topic) should be exposed to the consumer.
        :type exclude_internal_topics: bool
        :param source_address: The source address for socket connections
        :type source_address: str `'host:port'`
        :param ssl_config: Config object for SSL connection
        :type ssl_config: :class:`pykafka.connection.SslConfig`
        """
        self._seed_hosts = zookeeper_hosts if zookeeper_hosts is not None else hosts
        self._source_address = source_address
        self._socket_timeout_ms = socket_timeout_ms
        self._offsets_channel_socket_timeout_ms = offsets_channel_socket_timeout_ms
        self._handler = GEventHandler() if use_greenlets else ThreadingHandler()
        self.cluster = Cluster(
            hosts,
            self._handler,
            socket_timeout_ms=self._socket_timeout_ms,
            offsets_channel_socket_timeout_ms=self._offsets_channel_socket_timeout_ms,
            exclude_internal_topics=exclude_internal_topics,
            source_address=self._source_address,
            zookeeper_hosts=zookeeper_hosts,
            ssl_config=ssl_config)
        self.brokers = self.cluster.brokers
        self.topics = self.cluster.topics

    def __repr__(self):
        return "<{module}.{name} at {id_} (hosts={hosts})>".format(
            module=self.__class__.__module__,
            name=self.__class__.__name__,
            id_=hex(id(self)),
            hosts=self._seed_hosts,
        )

    def update_cluster(self):
        """Update known brokers and topics.

        Updates each Topic and Broker, adding new ones as found,
        with current metadata from the cluster.
        """
        self.cluster.update()
