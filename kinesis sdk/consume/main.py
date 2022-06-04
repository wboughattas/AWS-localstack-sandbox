import json
import logging
import sys
import time

import boto3

logging.basicConfig(
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("consumer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


class ShardIteratorPair:
    def __init__(self, shard_id, iterator):
        self.shard_id = shard_id
        self.iterator = iterator


def main():
    logging.info('Starting GetRecords Consumer')

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

    # fetch all shards and associated initial iterators
    logging.info("Fetching Shards and Iterators")
    shard_iterators = []
    shards_response = kinesis.list_shards(StreamName=StreamName)
    has_more = bool(shards_response['Shards'])
    while has_more:
        for shard in shards_response['Shards']:
            shard_id = shard['ShardId']
            # start from last untrimmed record in the shard in the system
            # (the oldest data record in the shard)
            itr_response = kinesis.get_shard_iterator(StreamName=StreamName,
                                                      ShardId=shard_id,
                                                      ShardIteratorType='TRIM_HORIZON')

            shard_itr = ShardIteratorPair(shard_id, itr_response['ShardIterator'])
            shard_iterators.append(shard_itr)

        if 'NextToken' in shards_response:
            shards_response = kinesis.list_shards(StreamName=StreamName,
                                                  NextToken=shards_response['NextToken'])
            has_more = bool(shards_response['Shards'])
        else:
            has_more = False

    # continuously Poll shards, collecting records and updating to use latest shard iterators
    while True:
        for shard_itr in shard_iterators:
            try:
                records_response = kinesis.get_records(ShardIterator=shard_itr.iterator,
                                                       Limit=200)
                for record in records_response['Records']:
                    order = json.loads(record['Data'].decode('utf-8'))
                    logging.info(
                        f"Read Order {order} from Shard {shard_itr.shard_id} at position {record['SequenceNumber']}")

                if records_response['NextShardIterator']:
                    shard_itr.iterator = records_response['NextShardIterator']
            except Exception as e:
                logging.error({'message': 'Failed fetching records', 'error': str(e)})

        time.sleep(0.5)


if __name__ == '__main__':
    main()
