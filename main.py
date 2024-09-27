from flask import Flask, Blueprint, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import API_TOKEN, JWT_SECRET_KEY
from football_api_model import FootballDataApi
from db.db_client import DynamoDBClient
from db.users_table_manager import UserManager
from db.predictions_table_manager import PredictionsManager
from datetime import timedelta
# Flask app initialization
from datetime import timedelta  # Add this import

# Flask app initialization
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY  # Secure value for production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Set token expiration to 7 days

CORS(app, supports_credentials=True)

# Initialize JWT
jwt = JWTManager(app)

# Move non-blueprint routes to their respective blueprints
auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')
football_blueprint = Blueprint('football', __name__, url_prefix='/football')

# API, DB, and Manager setup
api = FootballDataApi(API_TOKEN)
db_client = DynamoDBClient()
users_table = db_client.get_table_resource("users")
predictions_table = db_client.get_table_resource("premier-league-predictions")
user_manager = UserManager(users_table)
record_manager = PredictionsManager(predictions_table)

# Helper functions
def fetch_user(user_id):
    """Fetch the user by their ID."""
    return user_manager.get_user(user_id)

def create_token(user_record):
    """Create a JWT token for the user."""
    return create_access_token(identity=user_record['user_id'])

@auth_blueprint.route('/', methods=['POST'])
def auth():
    """Register or login user and return JWT token."""
    data = request.json
    username, pin = data.get('username'), data.get('pin')

    user_records = user_manager.check_if_user_exists(username)
    if not user_records:
        hashed_pin = generate_password_hash(pin)
        new_user = user_manager.create_user(username, hashed_pin)
        access_token = create_token(new_user)
        return jsonify({'message': 'User created and logged in', 'access_token': access_token, 'user': new_user}), 201
    
    user_record = user_records[0]
    if check_password_hash(user_record['pin'], pin):
        access_token = create_token(user_record)
        return jsonify({'message': 'Login successful', 'access_token': access_token, 'user': user_record}), 200
    return jsonify({'message': 'Invalid Pin'}), 401

@auth_blueprint.route('/logout', methods=['POST'])
def logout():
    """Logout user (placeholder for token invalidation)."""
    return jsonify({'message': 'Logged out'}), 200

@auth_blueprint.route('/auth-check', methods=['GET'])
@jwt_required()
def auth_check():
    """Check if user is authenticated."""
    user_record = fetch_user(get_jwt_identity())
    return jsonify({'authenticated': True, 'user': user_record}), 200

@football_blueprint.route('/matches', methods=['GET'])
@jwt_required()
def get_matches():
    """Get list of matches for the authenticated user."""
    records = record_manager.get_records_to_evaluate(get_jwt_identity())
    matches = api.get_matches_to_display(records)
    return jsonify(matches), 200

@football_blueprint.route('/matches', methods=['POST'])
@jwt_required()
def post_matches():
    """Submit a match prediction."""
    user_id = get_jwt_identity()
    data = request.json
    item = {
        'match_id': str(data['match_id']),
        'user_id': user_id,
        'home_team': data['home_team'],
        'away_team': data['away_team'],
        'home_team_flag': data['home_team_flag'],
        'away_team_flag': data['away_team_flag'],
        'match_date': data['match_date'],
        'isFinished': data.get('isFinished', False),
        'counted': False,
        'actual_outcome': None,
        'prediction': data['prediction'].upper(),
    }
    record_manager.create_record(item)
    user_record = user_manager.get_user(user_id)
    user_manager.update_user(user_id, {"prediction_counts": user_record.get("prediction_counts", 0) + 1 })
    return jsonify("Created a match prediction record"), 201

@football_blueprint.route('/matches/evaluate', methods=['GET'])
@jwt_required()
def evaluate_user_score():
    """Evaluate user score based on past match predictions."""
    user_id = get_jwt_identity()
    records = record_manager.get_records_to_evaluate(user_id)

    if not records:
        return jsonify({"message": "No uncounted predictions found."}), 200

    match_ids = [record['match_id'] for record in records]
    matches_with_result = api.get_matches_to_evaluate(match_ids)

    if not matches_with_result:
        return jsonify({"message": "No finished matches found for evaluation."}), 200

    score_increment = 0
    for match in matches_with_result:
        actual_outcome = "HOME" if match["score"]["winner"] == "HOME_TEAM" else "AWAY" if match["score"]["winner"] == "AWAY_TEAM" else "DRAW"

        for record in records:
            if str(record['match_id']) == str(match["id"]):
                if record['prediction'] == actual_outcome:
                    score_increment += 1
                response = record_manager.update_record(
                    match_id=match["id"], 
                    user_id=user_id, 
                    attributes={'counted': True, 'actual_outcome': actual_outcome, 'isFinished': True}
                )
                if not response:
                    return jsonify("Failed") 

    user_record = fetch_user(user_id)
    new_score = user_record.get('score', 0) + score_increment
    user_manager.update_user(user_id, {'score': new_score})

    return jsonify({"message": "User score updated", "new_score": new_score}), 200

@football_blueprint.route('/user-predictions', methods=['POST'])
@jwt_required()
def user_predictions():
    """Get all predictions for the authenticated user."""
    data = request.json
    user_predictions = record_manager.get_records_by_user(
        user_id=get_jwt_identity(), 
        last_evaluated_key=data.get("lastEvaluatedKey", None)
    )

    return jsonify(user_predictions), 200

@football_blueprint.route('/scoreboard', methods=['GET'])
@jwt_required()
def get_top_users():
    """Fetch top users based on their prediction scores."""
    users = user_manager.fetch_top_users()
    return jsonify(users), 200

# Register blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(football_blueprint)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
