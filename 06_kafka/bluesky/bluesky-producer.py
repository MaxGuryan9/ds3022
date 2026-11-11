import websocket
import json
import logging
import os
from datetime import datetime
from quixstreams import Application
from quixstreams.models import TopicConfig

"""
This script demonstrates how to use a Kafka producer to stream real-time 
events from Bluesky Jetstream to a Kafka topic.

NOTE that it does not parse/consume messages, it publishes/produces them to Kafka.
"""

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:19092,127.0.0.1:29092,127.0.0.1:39092")

# Log to a file beside this script, regardless of where it is run from
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "bluesky-producer.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("bluesky-producer")

CURSOR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jet_stream_cursor.txt")
JETSTREAM_URL = "wss://jetstream2.us-west.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
last_time_us = None

def load_cursor():
    """Return the saved time_us, or None to start from live events."""
    try:
        with open(CURSOR_FILE) as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return None
    except ValueError:
        log.warning("Invalid cursor file; starting from live events")
        return None

def save_cursor():
    """Flush pending messages to Kafka, then save the position."""
    producer.flush()
    if last_time_us is None:
        return
    # Replace the file in one step so a crash cannot leave it half-written
    tmp_file = CURSOR_FILE + ".tmp"
    with open(tmp_file, "w") as f:
        f.write(str(last_time_us))
    os.replace(tmp_file, CURSOR_FILE)

app = Application(
    broker_address=KAFKA_BROKER,
    producer_extra_config={
        "broker.address.family": "v4",
        # Batch settings for better throughput
        "linger.ms": 5,  # Wait up to 5ms to batch messages
        "batch.size": 100000,  # Batch up to 100KB
    }
)
topic = app.topic(
    name="bluesky-events",
    value_serializer="json",
    config=TopicConfig(
        num_partitions=1, 
        replication_factor=3,
    )
)

# Create a kafka producer 
producer = app.get_producer()

message_count = 0
start_time = datetime.now()

def on_message(_ws, message):
    """Publish each post commit to Kafka and report the running rate."""
    global message_count, last_time_us

    try:
        data = json.loads(message)

        # Jetstream also sends identity/account events, which have no commit
        if data.get("kind") != "commit":
            return

        rev = data['commit']['rev']
        serialized = topic.serialize(key=rev, value=data)

        # Reuse the same producer - no context manager!
        producer.produce(
            topic=topic.name,
            key=serialized.key,
            value=serialized.value
        )
        last_time_us = data["time_us"]
    except Exception:
        # One bad message should not stop the stream
        log.exception("Failed to process message")
        return

    message_count += 1

    # Print rate every 100 messages
    if message_count % 100 == 0:
        save_cursor()
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > 0:
            print(f"Rate: {message_count/elapsed:.2f} msg/sec (total: {message_count})")

def on_error(_ws, error):
    """Record WebSocket errors, such as a dropped connection."""
    # Ctrl-C also arrives here, but it is a normal shutdown
    if not isinstance(error, KeyboardInterrupt):
        log.error("WebSocket error: %s", error)

def on_close(_ws, close_status_code, close_msg):
    log.info("WebSocket closed: %s %s", close_status_code, close_msg)
    print("WebSocket closed, flushing remaining messages...")

# Resume from the saved position when one exists
cursor = load_cursor()
url = f"{JETSTREAM_URL}&cursor={cursor}" if cursor else JETSTREAM_URL
log.info("Starting from cursor: %s", cursor)

ws = websocket.WebSocketApp(
    url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

try:
    ws.run_forever()
except Exception:
    log.exception("Producer stopped unexpectedly")
    raise
finally:
    # Ensure we flush and record our position on exit
    save_cursor()
    print(f"\nTotal messages produced: {message_count}")
