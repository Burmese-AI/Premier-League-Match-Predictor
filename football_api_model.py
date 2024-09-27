import requests
from datetime import datetime, timedelta

class FootballDataApi:
    def __init__(self, api_token: str):
        self.base_url = "http://api.football-data.org/v4/"  # Moved base_url here
        self.headers = {'X-Auth-Token': api_token}
        self.COMPETITION_ID = 2021 #Premier League Competition ID

    # Convert match_date to a datetime object (remove 'Z' and parse the ISO format)
    def transform_match_date_into_datetime(self, match_date: str):
        target_date_obj = datetime.fromisoformat(match_date[:-1])  # Remove 'Z' for conversion
        return target_date_obj
    
    # Calculate the date range (today's date and 2 weeks from today)
    def calculate_date_range(self):
        # Current Date
        current_date = datetime.now()

        # Formatting the Current Date to "2024-09-11"
        date_from = current_date.strftime('%Y-%m-%d')

        # Getting the Fromattted Version of the Date after 14 days from the Current Date
        date_to = (current_date + timedelta(days=14)).strftime('%Y-%m-%d')

        # Return the Starting Date (Current Date) & the Ending Date (The Date after 14 Days)
        return date_from, date_to
    
    # Get the Matches with the Status of "TIMED"
    # To Note, In Football Data API, the Matches with the status of "TIMED" can't be directly filtered and fetched
    # Therefore, the Matches with the status of "SCHEDULED" must be direcly filtered first,
    def get_timed_matches(self):
        # Get the date_from and date_to
        date_from, date_to = self.calculate_date_range()
        # Fetch the scheduled matches using dateFrom and dateTo
        response = requests.get(
            f"{self.base_url}competitions/{self.COMPETITION_ID}/matches", 
            params={
                'status': 'SCHEDULED',
                'dateFrom': date_from,
                'dateTo': date_to
            }, 
            headers=self.headers
        )
        
        if response.status_code == 200:

            data = response.json()

            # From the response data, traverse the matches and store only the matches with the status of "TIMED"
            matches = [match for match in data.get("matches", []) if self.filter_matches_by_status(match, "TIMED")]

            # Return the List of Matches with the Status of "TIMED"
            return matches
        
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
        
    # Get Processed Matches to Display
    def get_matches_to_display(self, uncounted_prediction_records):
        # Check if uncounted_prediction_records is a list
        if not isinstance(uncounted_prediction_records, list):
            print("Error: uncounted_prediction_records should be a list of dictionaries.")
            return []

        # Fetch scheduled (timed) matches
        matches_to_display = self.get_timed_matches()        
        # Extract match IDs and predictions from the uncounted records
        predicted_matches = {}
        for record in uncounted_prediction_records:
            if isinstance(record, dict) and "match_id" in record and "prediction" in record:
                predicted_matches[str(record["match_id"])] = record['prediction']
            else:
                print("Warning: Invalid record format", record)
        
        # Update the scheduled matches with prediction information
        for match in matches_to_display:
            match_id = str(match["id"])
            match["prediction"] = {
                "status": match_id in predicted_matches,  # True if predicted, False otherwise
                "winner": predicted_matches.get(match_id, None)  # Predicted winner or None if not predicted
            }
                
        return matches_to_display
        
    # A helper method to match whether the match status is the same as the given status
    def filter_matches_by_status(self, match, status):
        return True if match["status"] == status else False
    
    # Get the Matches with the Status of "FINISHED" Filtered by the Match IDS the user predicted
    def get_matches_to_evaluate(self, match_ids):
        # Fetch the FINISHED matches using Match Ids
        response = requests.get(
            f"{self.base_url}/matches", 
            params={'status' : "FINISHED", 'ids' : ",".join(match_ids)}, 
            headers=self.headers
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []