from pyflink.datastream import StreamExecutionEnvironment, KeyedProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import StreamingFileSink
from pyflink.common.watermark_strategy import WatermarkStrategy
import json

# Example input: list of dicts with 'source' and 'message' fields
def run_stateful_aggregation(logs):
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Convert logs to JSON strings for the DataStream, handling datetime serialization
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    log_jsons = [json.dumps(log, default=default_serializer) for log in logs]
    ds = env.from_collection(log_jsons, type_info=Types.STRING())

    # Parse JSON and extract source
    def parse_log(log_str):
        log = json.loads(log_str)
        return (log['source'], log['message'])

    parsed = ds.map(parse_log, output_type=Types.TUPLE([Types.STRING(), Types.STRING()]))

    # Key by source
    keyed = parsed.key_by(lambda x: x[0])

    class ErrorCount(KeyedProcessFunction):
        def open(self, runtime_context):
            desc = ValueStateDescriptor('error_count', Types.INT())
            self.count_state = runtime_context.get_state(desc)

        def process_element(self, value, ctx):
            count = self.count_state.value()
            if count is None:
                count = 0
            if 'error' in value[1].lower():
                count += 1
                self.count_state.update(count)
            yield (value[0], count)

    aggregated = keyed.process(ErrorCount(), output_type=Types.TUPLE([Types.STRING(), Types.INT()]))

    # Print results to console (PyFlink only supports Java sinks)
    aggregated.print()
    env.execute('Stateful Aggregation Demo')
    # Results cannot be collected in Python directly; return None
    return None
