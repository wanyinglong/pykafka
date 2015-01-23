# TODO: Check all __repr__
# TODO: __slots__ where appropriate
# TODO: Use weak refs to avoid reference cycles?

import logging
from collections import defaultdict

from samsa import abstract
from samsa.pysamsa.partition import Partition
from samsa.pysamsa.protocol import (
    PartitionOffsetRequest, OFFSET_EARLIEST, OFFSET_LATEST
)


logger = logging.getLogger()


class Topic(abstract.Topic):

    def __init__(self, client, topic_metadata):
        """Create the Topic from metadata.

        :param client: Client connection to the cluster
        :type client: :class:`samsa.client.SamsaClient
        :param topic_metadata: Metadata for all topics
        :type topic_metadata: :class:`samsa.pysamsa.protocol.TopicMetadata`
        """
        self.client = client
        self._name = topic_metadata.name
        self._partitions = {}
        self.update(topic_metadata)

    @property
    def name(self):
        return self._name

    @property
    def partitions(self):
        return self._partitions

    def earliest_offsets(self):
        """Get the earliest offset for each partition of this topic."""
        return self.fetch_offsets(OFFSET_EARLIEST)

    def fetch_offsets(self, offsets_before, max_offsets=1):
        requests = defaultdict(list)  # one request for each broker
        for part in self.partitions.itervalues():
            requests[part.leader].append(PartitionOffsetRequest(
                self.name, part.id, offsets_before, max_offsets
            ))
        output = {}
        for broker, reqs in requests.iteritems():
            res = broker.request_offsets(reqs)
            output.update(res.topics[self.name])
        return output

    def latest_offsets(self):
        """Get the latest offset for each partition of this topic."""
        return self.fetch_offsets(OFFSET_LATEST)

    def update(self, brokers, metadata):
        """Update the Partitons with metadata about the cluster.

        :param brokers: Brokers partitions exist on
        :type brokers: List of :class:`samsa.pysamsa.Broker`
        :param metadata: Metadata for all topics
        :type metadata: :class:`samsa.pysamsa.protocol.TopicMetadata`
        """
        p_metas = metadata.partitions

        # Remove old partitions
        removed = set(self._partitions.keys()) - set(p_metas.keys())
        for id_ in removed:
            logger.info('Removing partiton %s', self._partitons[id_])
            self._partitons.pop(id_)

        # Add/update current partitions
        for id_, meta in p_metas.iteritems():
            if meta.id not in self._partitions:
                logger.info('Adding partition %s/%s', self.name, meta.id)
                self._partitions[meta.id] = Partition(
                    self, meta.id,
                    brokers[meta.leader],
                    [brokers[b] for b in meta.replicas],
                    [brokers[b] for b in meta.isr],
                )
            else:
                self._partitions[id_].update(meta)
