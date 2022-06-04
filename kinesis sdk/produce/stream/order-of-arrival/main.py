"""
Producer app writing single Order records at a time to a Kinesis Data Stream using
the PutRecord API of the Python SDK.

The globally unique Order ID of each record is used as the partition key which ensures
order records will be equally distributed across the shard of the stream.
"""
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
    region_name = 'us-east-1'
    endpoint_url = 'http://localhost:4566/'
    aws_access_key_id = 'test'
    aws_secret_access_key = 'test'
    StreamName = 'test'

    kinesis = boto3.client(service_name=service_name,
                           region_name=region_name,
                           endpoint_url=endpoint_url,
                           aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key
                           )

    while True:
        # Generate fake order data
        order = make_order()
        logging.info(f'Generated {order}')

        try:
            # execute single PutRecord request
            response = kinesis.put_record(StreamName=StreamName,
                                          Data=json.dumps(order).encode('utf-8'),
                                          PartitionKey=order['order_id'])
            logging.info(f"Produced Record {response['SequenceNumber']} to Shard {response['ShardId']}")
        except Exception as e:
            logging.error({
                'message': 'Error producing record',
                'error': str(e),
                'record': order
            })

        # introduce artificial delay for demonstration and
        # visual tracking of logging
        time.sleep(0.3)


if __name__ == '__main__':
    main()
