import websocket
import json
import logging
import os
import signal
import threading
import time
from confluent_kafka.admin import AdminClient
from quixstreams import Application
from quixstreams.models import TopicConfig

"""
This script demonstrates how to use a Kafka producer to stream real-time
events from Bluesky Jetstream to a Kafka topic.

NOTE that it does not parse/consume messages, it publishes/produces them to Kafka.
Each commit event is published to the `bluesky-events` topic, keyed by the user's DID.

If the connection drops, it reconnects with exponential backoff and resumes from the
last event it saw, using Jetstream's `cursor` parameter (a unix timestamp in microseconds).
The cursor of the last event Kafka confirmed is saved to `jetstream_cursor.txt` every few
seconds and on exit, so a crash or restart resumes where it left off.

Enable Kafka publishing:
- Start the Kafka brokers: `docker compose up -d` from `06_kafka/`, and confirm they are up
    in the Redpanda Console.
- Uncomment the Kafka setup block below (`KAFKA_BROKER`, `app`, `topic`, `producer`).
    The imports it needs are already at the top of the file.
- In `on_message`, replace `print(did)` with a produce step: serialize the event with
    `topic.serialize()` (DID as the key, the full event as the value), then pass the
    serialized key and value to `producer.produce()` along with the topic name.
- Uncomment `producer.flush()` in the `finally` block so buffered messages are sent on exit.
- Run the script, then confirm messages are arriving in the `bluesky-events` topic
      (Redpanda Console, or run `bluesky-consumer.py`).
- OPTIONAL: Implement a method to measure/count msgs/sec every 5 seconds and print to stdout
      as the script runs.


Ways to make this more robust once Kafka publishing is enabled:
- Save the cursor to a small local file (periodically and on exit) and load it on startup, so a
  restart resumes where it left off instead of skipping ahead. Ignore a saved cursor that is
  older than the topic's retention. TEST the cursor by running your script for a couple of minutes,
  then force it to stop using Ctrl+C, wait 5-10 seconds, then start it back up. You should see a
  large number of messages in the next count of msgs/sec.
- Add a delivery callback (`on_delivery`) so you know which messages Kafka accepted or rejected.
- Turn on `enable.idempotence` (implies `acks=all`) so the producer's internal retries can't
  create duplicates or reorder messages. Consider `compression.type` and larger batches too.
- Set the Kafka message timestamp to the event time (`time_us`) instead of the time it was received.
- Only advance the cursor after an event is safely handed to the producer, not when it arrives.
- Catch `BufferError` from `produce()`: it means Kafka is slow or down and the local buffer is full.
- When a message fails or the buffer fills, stop reading the stream, flush, and replay from the
  earliest failed event's cursor. Jetstream can act as your replay log.
- Before reconnecting, check that Kafka is reachable, and exit with an error after a few failed tries.
- Always `flush()` the producer before exiting, and handle SIGTERM (e.g. `docker stop`) as well as Ctrl-C.
- Reconnect if the stream goes silent for too long, not just when the connection drops.
- Rotate between Jetstream servers (jetstream1/2, us-east/us-west) on reconnect.
- Expect duplicates (at-least-once delivery): replays and the reconnect rewind can resend events.
  How would a consumer detect and drop them?
"""

# Jetstream servers, rotated on each reconnect; all carry the same events and accept the same cursor
JETSTREAM_HOSTS = [
    "jetstream2.us-west.bsky.network",
    "jetstream1.us-west.bsky.network",
    "jetstream2.us-east.bsky.network",
    "jetstream1.us-east.bsky.network",
]
WANTED_COLLECTIONS = "app.bsky.*"          # Posts, likes, reposts, follows, blocks, profiles, etc.
CURSOR_REWIND_US = 2_000_000               # On reconnect, rewind 2s so no events are missed (may produce a few duplicates)
MAX_BACKOFF = 60                           # Max seconds to wait between reconnect attempts
TOPIC_RETENTION_MS = 3 * 60 * 60 * 1000    # 3 hours
REPORT_INTERVAL = 5                        # Seconds between msgs/sec reports and cursor saves
SILENCE_TIMEOUT = 30                       # Reconnect if no message arrives for this many seconds
MAX_KAFKA_FAILURES = 5                     # Exit after this many failed Kafka reachability checks in a row
FLUSH_TIMEOUT = 15                         # Max seconds to wait for Kafka when flushing
BUFFER_ERROR_TRIES = 3                     # produce() retries on a full local buffer before giving up

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CURSOR_FILE = os.path.join(SCRIPT_DIR, "jetstream_cursor.txt")   # gitignored

cursor = None              # time_us of the last event handed to the producer; resume point for reconnects
delivered_cursor = None    # time_us of the last event Kafka confirmed; this is what gets saved to disk
failed_cursor = None       # time_us of the earliest event Kafka rejected; replay starts here
replay_pending = False     # Set when a send fails: stop reading, flush, then replay from failed_cursor
backoff = 1                # Current reconnect delay in seconds
stop = False               # Set on Ctrl-C / SIGTERM to break out of the reconnect loop
host_index = 0             # Which Jetstream server to connect to next
current_ws = None          # The open WebSocket, so the silence watchdog can close it
last_message_at = time.monotonic()   # When the last message arrived, for the silence watchdog

total_count = 0                     # Messages produced since startup
window_count = 0                    # Messages produced in the current reporting window
window_start = time.monotonic()     # When the current reporting window began

# Log errors and connection events to a file beside this script (*.log is gitignored)
logging.basicConfig(
    filename=os.path.join(SCRIPT_DIR, "bluesky-producer.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("bluesky-producer")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:19092,127.0.0.1:29092,127.0.0.1:39092")

# Used only to check that the brokers are reachable before (re)connecting
admin = AdminClient({"bootstrap.servers": KAFKA_BROKER, "broker.address.family": "v4"})

def wait_before_retry():
    """Sleep for the current backoff, then double it (up to MAX_BACKOFF)."""
    global backoff
    time.sleep(backoff)
    backoff = min(backoff * 2, MAX_BACKOFF)

def wait_for_kafka():
    """Block until the brokers answer a metadata request; exit after MAX_KAFKA_FAILURES tries in a row."""
    for attempt in range(1, MAX_KAFKA_FAILURES + 1):
        try:
            admin.list_topics(timeout=5)
            return
        except Exception as e:
            log.warning("Kafka unreachable (%s/%s): %s", attempt, MAX_KAFKA_FAILURES, e)
        if attempt < MAX_KAFKA_FAILURES:
            print(f"Kafka unreachable ({attempt}/{MAX_KAFKA_FAILURES}). Retrying in {backoff}s...")
            wait_before_retry()
    print(f"Kafka unreachable after {MAX_KAFKA_FAILURES} tries; exiting")
    log.error("Kafka unreachable after %s tries; exiting", MAX_KAFKA_FAILURES)
    raise SystemExit(1)

# app.topic() below blocks indefinitely if no broker answers, so check first
wait_for_kafka()

app = Application(
    broker_address=KAFKA_BROKER,
    producer_extra_config={
        "broker.address.family": "v4",
        # Idempotence (implies acks=all) stops internal retries from duplicating or reordering messages
        "enable.idempotence": True,
        "compression.type": "lz4",     # Cheap compression; JSON events shrink well
        "linger.ms": 20,               # Wait up to 20ms to fill larger batches
        "batch.size": 500000,          # Batch up to 500KB
        "message.timeout.ms": 30000,   # Report a failed delivery after 30s instead of the 5-minute default
    }
)
topic = app.topic(
    name="bluesky-events",
    value_serializer="json",
    config=TopicConfig(
        num_partitions=1,
        replication_factor=3,
        extra_config={"retention.ms": str(TOPIC_RETENTION_MS)}
    )
)

# Create a kafka producer, reused for every message
producer = app.get_producer()


def load_cursor():
    """Return the saved cursor, or None if missing, invalid, or older than the topic's retention."""
    try:
        with open(CURSOR_FILE) as f:
            saved = int(f.read().strip())
    except FileNotFoundError:
        return None
    except (ValueError, OSError) as e:
        log.warning("Ignoring unreadable cursor file: %s", e)
        return None
    # Events older than retention are already gone from Kafka, so replaying them adds nothing
    age_ms = (time.time_ns() // 1000 - saved) / 1000
    if age_ms > TOPIC_RETENTION_MS:
        log.info("Ignoring saved cursor %s: older than topic retention", saved)
        return None
    return saved

def save_cursor():
    """Write the safe resume point: the earliest failure if any, else the last confirmed delivery."""
    position = failed_cursor if failed_cursor is not None else delivered_cursor
    if position is None:
        return
    try:
        # Write then rename, so a crash mid-write cannot leave a half-written file
        tmp_file = CURSOR_FILE + ".tmp"
        with open(tmp_file, "w") as f:
            f.write(str(position))
        os.replace(tmp_file, CURSOR_FILE)
    except OSError:
        log.exception("Failed to save cursor")

def request_replay(time_us, reason):
    """Record the earliest failed event and close the stream so the main loop can flush and replay."""
    global failed_cursor, replay_pending
    if failed_cursor is None or time_us < failed_cursor:
        failed_cursor = time_us
    if not replay_pending:
        replay_pending = True
        print(f"{reason}; pausing stream to replay from {failed_cursor}")
        log.error("%s; replay from cursor %s", reason, failed_cursor)
        if current_ws:
            current_ws.close()

def on_delivery(err, msg, time_us):
    """Called by the producer once Kafka accepts or rejects a message."""
    global delivered_cursor
    if err is not None:
        request_replay(time_us, f"Delivery failed ({err})")
    elif delivered_cursor is None or time_us > delivered_cursor:
        delivered_cursor = time_us

def report_progress():
    """Every REPORT_INTERVAL seconds: print msgs/sec, save the cursor, and start a new window."""
    global window_count, window_start
    elapsed = time.monotonic() - window_start
    if elapsed >= REPORT_INTERVAL:
        print(f"Rate: {window_count / elapsed:.1f} msg/sec (total: {total_count})")
        save_cursor()
        window_count = 0
        window_start = time.monotonic()

def silence_watchdog():
    """Background thread: close the connection if the stream goes quiet, so the main loop reconnects."""
    while True:
        time.sleep(5)
        ws = current_ws
        if ws and time.monotonic() - last_message_at > SILENCE_TIMEOUT:
            print(f"No messages for {SILENCE_TIMEOUT}s; reconnecting")
            log.warning("Stream silent for %ss; closing connection", SILENCE_TIMEOUT)
            ws.close()

def handle_sigterm(signum, frame):
    """Treat SIGTERM (e.g. `docker stop`) like Ctrl-C so the same clean shutdown runs."""
    raise KeyboardInterrupt


def on_open(ws):
    """Connection established: reset the backoff delay and the silence timer."""
    global backoff, last_message_at
    backoff = 1
    last_message_at = time.monotonic()
    host = JETSTREAM_HOSTS[host_index % len(JETSTREAM_HOSTS)]
    print(f"Connected to {host}{f' (resuming from cursor {cursor})' if cursor else ''}")
    log.info("Connected to %s (cursor=%s)", host, cursor)

def on_message(ws, message):
    """Handle each Jetstream event: skip non-commit events, key by DID, produce to Kafka, then advance the cursor."""
    global cursor, total_count, window_count, last_message_at
    last_message_at = time.monotonic()

    # A send failed: ignore the rest of this connection; the replay will resend these events
    if replay_pending:
        return

    try:
        data = json.loads(message)
        time_us = data["time_us"]

        # Jetstream also sends 'identity' and 'account' events, which have no 'commit' field.
        # Nothing to send, so the cursor can move past them right away.
        if data.get("kind") != "commit":
            cursor = time_us
            return

        # The DID (decentralized identifier) uniquely identifies the acting user
        did = data["did"]

        # Serialize with the topic's JSON serializer (DID as key), then hand to the producer.
        # The Kafka timestamp is the event time (ms), not the time we received it.
        serialized = topic.serialize(key=did, value=data)
        producer.produce(
            topic=topic.name,
            key=serialized.key,
            value=serialized.value,
            timestamp=time_us // 1000,
            buffer_error_max_tries=BUFFER_ERROR_TRIES,
            poll_timeout=1.0,
            on_delivery=lambda err, msg, t=time_us: on_delivery(err, msg, t),
        )

        # Only now is the event safely with the producer, so advance the resume point
        cursor = time_us
        total_count += 1
        window_count += 1
        report_progress()

    except BufferError:
        # The local buffer stayed full after retries: Kafka is slow or down
        request_replay(time_us, "Producer buffer full")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Bad message ({type(e).__name__}: {e})")
        log.warning("Bad message (%s: %s)", type(e).__name__, e)
    except Exception as e:
        print(f"Unexpected error handling message: {e}")
        log.exception("Unexpected error handling message")

def on_error(ws, error):
    """Report WebSocket-level errors. Ctrl-C arrives here too (websocket-client swallows it), so flag a stop."""
    global stop
    if isinstance(error, KeyboardInterrupt):
        stop = True
    else:
        print(f"WebSocket error: {error}")
        log.error("WebSocket error: %s", error)

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed ({close_status_code}: {close_msg})")
    log.info("WebSocket closed (%s: %s)", close_status_code, close_msg)



signal.signal(signal.SIGTERM, handle_sigterm)
threading.Thread(target=silence_watchdog, daemon=True).start()

# Resume from the saved position when one exists
cursor = delivered_cursor = load_cursor()
log.info("Starting from cursor: %s", cursor)

# Reconnect loop: each pass checks Kafka, opens a connection (resuming from the cursor if we have one)
# and runs until it drops; then wait with exponential backoff and try again on the next server.
try:
    while not stop:
        # Don't read the stream if there is nowhere to send it
        wait_for_kafka()

        host =JETSTREAM_HOSTS[host_index % len(JETSTREAM_HOSTS)]
        url = f"wss://{host}/subscribe?wantedCollections={WANTED_COLLECTIONS}"
        if cursor:
            url += f"&cursor={cursor - CURSOR_REWIND_US}"
        current_ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        # Pings detect silently dead connections; reconnect=0 hands reconnection to this loop
        current_ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=0)
        current_ws = None
        if stop:
            break

        # A send failed: flush what is buffered (more failures may surface), then rewind to the earliest failure
        if replay_pending:
            producer.flush(FLUSH_TIMEOUT)
            cursor = delivered_cursor = failed_cursor
            failed_cursor = None
            replay_pending = False
            save_cursor()

        host_index += 1
        print(f"Disconnected. Reconnecting in {backoff}s...")
        wait_before_retry()
except KeyboardInterrupt:
    pass
finally:
    # Ensure buffered messages are sent to Kafka before exiting, then record how far we got
    remaining = producer.flush(FLUSH_TIMEOUT)
    if remaining:
        log.warning("%s messages not confirmed at exit; they will be replayed on restart", remaining)
    save_cursor()
    print(f"\nStopped. Total messages produced: {total_count} (cursor saved: {failed_cursor or delivered_cursor})")
    log.info("Stopped. Total produced: %s, cursor saved: %s", total_count, failed_cursor or delivered_cursor)
