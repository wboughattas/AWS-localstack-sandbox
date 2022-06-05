import base64
import json


def decode_record(record: bytes) -> str:
    string_data = base64.b64decode(record).decode('utf-8')
    return string_data


def lambda_handler(event, context):
    for record in event['Records']:
        try:
            order = decode_record(record['kinesis']['data'])
            return json.dumps({
                'message': 'Processed order record',
                'order': order
            })
        except Exception as e:
            return json.dumps({
                'error': 'failed-decoding-record',
                'exception': str(e),
                'record': record
            })
