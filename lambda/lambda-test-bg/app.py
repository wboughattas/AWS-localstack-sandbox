import base64
import json


def decode_record(record: bytes) -> str:
    string_data = base64.b64decode(record).decode('utf-8')
    return string_data


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        payload = decode_record(record['data'])

        # Do custom processing on the payload here
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': json.dumps(payload, ensure_ascii=False).encode('utf8')
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))
    return {'records': output}
