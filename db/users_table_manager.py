import uuid
import heapq
from boto3.dynamodb.conditions import Attr
from dynamo_error_handler import dynamo_error_handler  # Import the error handler

# Users Table Management
class UserManager:
    def __init__(self, table):
        self.table = table

    @dynamo_error_handler  # Apply the error handling decorator
    def fetch_top_users(self, limit=10):
        top_users = []
        query_params = {}

        # Initial scan to fetch users
        while True:
            response = self.table.scan(**query_params)

            # Process users in the current batch
            for user in response.get('Items', []):
                winning_rate = self.calculate_winning_rate(user)
                # Use a single push operation for both cases
                if len(top_users) < limit:
                    heapq.heappush(top_users, (winning_rate, user["username"]))
                else:
                    heapq.heappushpop(top_users, (winning_rate, user["username"]))

            # Check for more items
            if 'LastEvaluatedKey' not in response:
                break

            # Update the start key for the next scan
            query_params['ExclusiveStartKey'] = response['LastEvaluatedKey']

        # Sort and return the top users
        return sorted(top_users, key=lambda x: x[0], reverse=True)[:limit]

    def calculate_winning_rate(self, user):
        return round(user['score'] / user['prediction_counts'], 2) if user['prediction_counts'] > 0 else 0

    @dynamo_error_handler  # Apply the error handling decorator
    def create_user(self, username, pin):
        user_id = str(uuid.uuid4())
        self.table.put_item(
            Item={
                'user_id': user_id,
                'username': username.lower(),
                'pin': pin,
                'prediction_counts': 0,
                'score': 0
            }
        )
        return self.get_user(user_id)

    @dynamo_error_handler  # Apply the error handling decorator
    def get_user(self, user_id):
        response = self.table.get_item(Key={'user_id': user_id})
        return response.get('Item', None)

    @dynamo_error_handler  # Apply the error handling decorator
    def check_if_user_exists(self, username):
        response = self.table.scan(FilterExpression=Attr('username').eq(username.lower()))
        return response['Items']

    @dynamo_error_handler  # Apply the error handling decorator
    def update_user(self, user_id, attributes):
        update_expression = "SET " + ", ".join([f"{attr} = :{attr}" for attr in attributes.keys()])
        expression_attribute_values = {f":{attr}": value for attr, value in attributes.items()}
        response = self.table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return response
