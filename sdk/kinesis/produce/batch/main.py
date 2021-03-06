import json
import logging
import sys
import time

import boto3

from order_generator import make_order

logging.basicConfig(
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("producer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    logging.info('Starting PutRecord Producer')

    service_name = 'kinesis'
    region_name = 'ca-central-1'
    # endpoint_url = 'http://localhost:4566/'
    # aws_access_key_id = 'test'
    # aws_secret_access_key = 'test'
    StreamName = 'test-bg'

    kinesis = boto3.client(service_name=service_name,
                           region_name=region_name,
                           # endpoint_url=endpoint_url,
                           # aws_access_key_id=aws_access_key_id,
                           # aws_secret_access_key=aws_secret_access_key
                           )

    # list for batching up order records to be sent to Kinesis via PutRecords API
    order_records = []
    while True:
        order = make_order()
        logging.info(f'Generated {order}')
        kinesis_entry = {
            'Data': json.dumps(order).encode('utf-8'),
            'PartitionKey': order['order_id']
        }
        order_records.append((order, kinesis_entry))

        if len(order_records) > 20:
            try:
                # break apart orders from records as separate lists
                orders, records = map(list, zip(*order_records))

                # write records to Kinesis via PutRecords API
                response = kinesis.put_records(Records=records,
                                               StreamName=StreamName)

                # inspect records to check for any that failed to be written to Kinesis
                for i, record_response in enumerate(response['Records']):
                    error_code = record_response.get('ErrorCode')
                    o = orders[i]
                    if error_code:
                        err_msg = record_response['ErrorMessage']
                        logging.error(f"Failed to produce {o} because {err_msg}")
                    else:
                        seq = record_response['SequenceNumber']
                        shard = record_response['ShardId']
                        logging.info(f"Produced {o} sequence {seq} to Shard {shard}")

                order_records.clear()

            except Exception as e:
                logging.error({
                    'message': 'Error producing records',
                    'error': str(e),
                    'records': order_records
                })

            # introduce artificial delay for demonstration and
            # visual tracking of logging
            time.sleep(10)


if __name__ == '__main__':
    main()
