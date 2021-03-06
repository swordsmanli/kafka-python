from itertools import cycle
import logging

from kafka.common import ProduceRequest
from kafka.protocol import create_message
from kafka.partitioner import HashedPartitioner

log = logging.getLogger("kafka")


class SimpleProducer(object):
    """
    A simple, round-robbin producer. Each message goes to exactly one partition
    """
    def __init__(self, client, topic):
        self.client = client
        self.topic = topic
        self.client._load_metadata_for_topics(topic)
        self.next_partition = cycle(self.client.topic_partitions[topic])

    def send_messages(self, *msg):
        req = ProduceRequest(self.topic, self.next_partition.next(),
                             messages=[create_message(m) for m in msg])

        resp = self.client.send_produce_request([req])[0]
        assert resp.error == 0


class KeyedProducer(object):
    """
    A producer which distributes messages to partitions based on the key

    Args:
    client - The kafka client instance
    topic - The kafka topic to send messages to
    partitioner - A partitioner class that will be used to get the partition
        to send the message to. Must be derived from Partitioner
    """
    def __init__(self, client, topic, partitioner=None):
        self.client = client
        self.topic = topic
        self.client._load_metadata_for_topics(topic)

        if not partitioner:
            partitioner = HashedPartitioner

        self.partitioner = partitioner(self.client.topic_partitions[topic])

    def send(self, key, msg):
        partitions = self.client.topic_partitions[self.topic]
        partition = self.partitioner.partition(key, partitions)

        req = ProduceRequest(self.topic, partition,
                             messages=[create_message(msg)])

        resp = self.client.send_produce_request([req])[0]
        assert resp.error == 0
