from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.common.time import Time
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.watermark_strategy import WatermarkStrategy
import json
import os

def run_kafka_stateful_aggregation():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    env.set_stream_time_characteristic(TimeCharacteristic.EventTime)

    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_LOG_TOPIC", "log2incident-logs")

    consumer = FlinkKafkaConsumer(
        topics=kafka_topic,
        deserialization_schema=SimpleStringSchema(),
        properties={"bootstrap.servers": kafka_bootstrap}
    )

    # Assume logs have a 'timestamp' field in ISO format
    def extract_timestamp(log_str):
        try:
            log = json.loads(log_str)
            # Convert ISO timestamp to epoch ms
            from datetime import datetime
            return int(datetime.fromisoformat(log["timestamp"]).timestamp() * 1000)
        except Exception:
            return 0

    ds = env.add_source(consumer)
    ds = ds.assign_timestamps_and_watermarks(
        WatermarkStrategy.for_monotonous_timestamps().with_timestamp_assigner(lambda e, _: extract_timestamp(e))
    )

    def parse_and_filter(log_str):
        log = json.loads(log_str)
        if "error" in log.get("message", "").lower():
            return (log["source"], 1)
        return None

    parsed = ds.map(parse_and_filter, output_type=Types.TUPLE([Types.STRING(), Types.INT()]))
    filtered = parsed.filter(lambda x: x is not None)

    # Windowed aggregation: count errors per source every 5 seconds
    result = (
        filtered
        .key_by(lambda x: x[0])
        .window(TumblingEventTimeWindows.of(Time.seconds(5)))
        .reduce(lambda a, b: (a[0], a[1] + b[1]))
    )

    result.print()
    env.execute("Kafka Flink Stateful Aggregation")
