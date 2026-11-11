"""
Consumer-group demo: run ONE instance to read all 3 partitions, or run THREE
instances with the same group name to split the partitions between them.

    python consume.py <group-name>

Within a partition, messages for a key stay in order; across partitions they interleave.
Ctrl+C to stop and print a summary.
"""
import os
import sys
import json
from collections import defaultdict

from quixstreams import Application

BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:19092,127.0.0.1:29092,127.0.0.1:39092")
TOPIC = "orders-by-customer"
GROUP = sys.argv[1] if len(sys.argv) > 1 else "orders-group"
ME = f"pid {os.getpid()}"  # label so you can tell parallel instances apart

app = Application(
    broker_address=BROKER,
    consumer_group=GROUP,
    auto_offset_reset="earliest",  # a NEW group starts from the beginning of the topic
)

by_partition = defaultdict(list)


def on_assign(consumer, partitions):
    """Fires on every rebalance: shows which partitions this instance now owns."""
    print(f"[{ME}] ASSIGNED partitions {sorted(p.partition for p in partitions)} (group '{GROUP}')")


def on_revoke(consumer, partitions):
    """Fires when partitions are taken away, e.g. another instance joined the group."""
    print(f"[{ME}] REVOKED partitions {sorted(p.partition for p in partitions)}")


with app.get_consumer() as consumer:
    consumer.subscribe([TOPIC], on_assign=on_assign, on_revoke=on_revoke)
    try:
        while True:  # run until Ctrl+C so instances can be started before the producer
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}")
                continue
            key = msg.key().decode()
            order = json.loads(msg.value())["order_id"]
            by_partition[msg.partition()].append((key, order))
            print(f"[{ME}] partition {msg.partition()}  offset {msg.offset():<4} key={key:<6} order={order}")
    except KeyboardInterrupt:
        pass

print(f"\n[{ME}] Keys found per partition:")
for p in sorted(by_partition):
    keys = sorted({k for k, _ in by_partition[p]})
    print(f"  partition {p}: {len(by_partition[p])} msgs, keys {keys}")
