import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME

# DynamoDB client for initialization and table access
class DynamoDBClient:
    def __init__(self):
        self.db = self.initialize_dynamodb()

    def initialize_dynamodb(self):
        return boto3.resource(
            'dynamodb',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME
        )

    def get_table_resource(self, table_name):
        return self.db.Table(table_name)
