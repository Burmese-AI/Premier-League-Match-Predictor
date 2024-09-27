from boto3.dynamodb.conditions import Attr, Key
from dynamo_error_handler import dynamo_error_handler  # Import the error handler

# Predictions Records Table Management
class PredictionsManager:
    def __init__(self, table):
        self.table = table

    def _scan_with_filter(self, user_id, filter_expression, last_evaluated_key=None):

        # To store records
        records = []

        params = {
            'FilterExpression': filter_expression,
        }

        while True:
            if last_evaluated_key:
                params['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.scan(**params)

            # Extract records that match the user_id filter
            records.extend(response.get("Items", []))

            # Check LastEvaluatedKey
            last_evaluated_key = response.get('LastEvaluatedKey', None)
            if last_evaluated_key:
                # Check if the LastEvaluatedKey matches the filter criteria
                if last_evaluated_key.get('user_id') != user_id:
                    print("LastEvaluatedKey does not match user_id, continuing to scan...")
                    continue  # Continue scanning to find a valid LastEvaluatedKey
            break  # Exit the loop if no more items or a valid LastEvaluatedKey is found

        return response["Items"], response.get('LastEvaluatedKey', None)  # Return items and last evaluated key

    @dynamo_error_handler  # Apply the error handling decorator
    def create_record(self, item):
        response = self.table.put_item(Item=item)
        return response

    @dynamo_error_handler  # Apply the error handling decorator
    def update_record(self, match_id, user_id, attributes):
        # Convert match_id to string
        match_id_str = str(match_id)

        update_expression = "SET " + ", ".join([f"{attr} = :{attr}" for attr in attributes.keys()])
        expression_attribute_values = {f":{attr}": value for attr, value in attributes.items()}

        response = self.table.update_item(
            Key={
                'match_id': match_id_str,  # Ensure match_id is a string
                'user_id': user_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return response
    
    @dynamo_error_handler  # Apply the error handling decorator
    def get_records_by_user(self, user_id, last_evaluated_key=None):
        records, last_evaluated_key = self._scan_with_filter(
            user_id=user_id, 
            filter_expression= Attr('user_id').eq(user_id), 
            last_evaluated_key=last_evaluated_key
        )

        return {
            "records": records,
            "last_evaluated_key": last_evaluated_key  # Return the last evaluated key for further requests
        }
    
    @dynamo_error_handler  # Apply the error handling decorator
    def get_records_to_evaluate(self, user_id):
        records = []
        last_evaluated_key = None
        
        # Loop to fetch all uncounted records
        while True:
            fetched_records, last_evaluated_key = self._scan_with_filter(
                    user_id=user_id,
                    filter_expression=Attr('counted').eq(False) & Attr('user_id').eq(user_id), 
                    last_evaluated_key=last_evaluated_key
                )
            records.extend(fetched_records)

            if not last_evaluated_key:  # Break if there's no more data to fetch
                break

        return records