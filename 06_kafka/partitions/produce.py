"""
Exercise: produce keyed messages into a 3-partition topic and watch
Kafka's default partitioner route each key to a consistent partition.
"""
import os
import json
import random
from collections import defaultdict

from confluent_kafka.admin import AdminClient, NewTopic
from quixstreams import Application

BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:19092,127.0.0.1:29092,127.0.0.1:39092")
TOPIC = "orders-by-customer"
NUM_PARTITIONS = 3
# quixstreams uses the murmur2 partitioner (Java-compatible); these keys split 2/2/2 across 3 partitions
KEYS = ["alice", "bob", "carol", "dave", "erin", "frank"]
NUM_MESSAGES = 900


def ensure_topic():
    """Create the topic with exactly 3 partitions if it doesn't exist."""
    admin = AdminClient({"bootstrap.servers": BROKER})
    existing = admin.list_topics(timeout=10).topics
    if TOPIC in existing:
        count = len(existing[TOPIC].partitions)
        print(f"Topic '{TOPIC}' already exists with {count} partitions")
        return
    futures = admin.create_topics(
        [NewTopic(TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=1)]
    )
    futures[TOPIC].result()  # raises if creation failed
    print(f"Created topic '{TOPIC}' with {NUM_PARTITIONS} partitions")


# Tracks which partitions each key landed in, filled by the delivery callback
placements = defaultdict(set)


def on_delivery(err, msg):
    """Called once per message when the broker confirms (or rejects) it."""
    if err is not None:
        print(f"  FAILED: {err}")
        return
    key = msg.key().decode()
    placements[key].add(msg.partition())
    print(f"  key={key:<6} -> partition {msg.partition()}  offset {msg.offset()}")


def main():
    ensure_topic()

    app = Application(
        broker_address=BROKER,
        producer_extra_config={"enable.idempotence": True, "acks": "all"},
    )

    print(f"\nProducing {NUM_MESSAGES} messages...\n")
    with app.get_producer() as producer:
        for i in range(NUM_MESSAGES):
            key = random.choice(KEYS)
            value = {"order_id": i, "customer": key, "amount": random.randint(5, 500)}
            producer.produce(
                topic=TOPIC,
                key=key,  # the key drives partition choice: hash(key) % 3
                value=json.dumps(value),
                on_delivery=on_delivery,
            )
        producer.flush()  # wait for all delivery callbacks before summarizing

    print("\nSummary: each key should map to exactly ONE partition")
    for key in sorted(placements):
        parts = sorted(placements[key])
        status = "OK" if len(parts) == 1 else "UNEXPECTED"
        print(f"  {key:<6} -> {parts}  {status}")


if __name__ == "__main__":
    main()