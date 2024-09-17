import os
import json
from flask import Flask, render_template, request, jsonify, session
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv
from .config import get_firebase_config  # Change this line

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Set secret key
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Add this line

# Initialize Firebase
firebase_service_account = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
cred = credentials.Certificate(firebase_service_account)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
})

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    game_id = request.json.get('game_id')

    print(f"Login attempt: username={username}, game_id={game_id}")  # Add this line

    if not username or not game_id:
        return jsonify({'success': False, 'message': 'Username and game ID are required'}), 400

    game_ref = db.reference(f'games/{game_id}')
    game = game_ref.get()

    print(f"Game data: {game}")  # Add this line

    if not game:
        return jsonify({'success': False, 'message': 'Invalid game ID'}), 404

    if game['player1'] == username:
        player = 'player1'
    elif game['player2'] == username:
        player = 'player2'
    else:
        print(f"Username {username} not found in game {game_id}")  # Add this line
        return jsonify({'success': False, 'message': 'Username not associated with this game'}), 403

    session['username'] = username
    session['game_id'] = game_id
    session['player'] = player

    # Set game status to 'playing' if both players have joined
    if game['player1'] and game['player2']:
        game_ref.update({'status': 'playing'})

    return jsonify({'success': True, 'player': player})

@app.route('/make_choice', methods=['POST'])
def make_choice():
    try:
        if 'username' not in session or 'game_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        choice = request.json.get('choice')
        game_id = session['game_id']
        player = session['player']

        if not choice:
            return jsonify({'success': False, 'message': 'No choice provided'}), 400

        game_ref = db.reference(f'games/{game_id}')
        game = game_ref.get()

        if not game:
            return jsonify({'success': False, 'message': 'Game not found'}), 404

        if game['status'] != 'playing':
            # If the game is not in playing state, check if both players are present
            if game['player1'] and game['player2']:
                game_ref.update({'status': 'playing'})
            else:
                return jsonify({'success': False, 'message': 'Waiting for other player to join'}), 400

        # Update the player's choice
        game_ref.child(f'{player}_choice').set(choice)

        # Check if both players have made their choices
        updated_game = game_ref.get()
        if updated_game.get('player1_choice') and updated_game.get('player2_choice'):
            # Determine the winner of this round
            round_winner = determine_winner(updated_game['player1_choice'], updated_game['player2_choice'])
            
            # Update scores
            if round_winner == 'player1':
                game_ref.child('player1_score').set(updated_game.get('player1_score', 0) + 1)
            elif round_winner == 'player2':
                game_ref.child('player2_score').set(updated_game.get('player2_score', 0) + 1)

            # Check if a player has reached 3 points
            final_game = game_ref.get()
            if final_game.get('player1_score', 0) >= 3:
                game_ref.update({'status': 'finished', 'winner': 'player1'})
            elif final_game.get('player2_score', 0) >= 3:
                game_ref.update({'status': 'finished', 'winner': 'player2'})
            else:
                # Reset choices for the next round
                game_ref.update({'player1_choice': None, 'player2_choice': None})

            return jsonify({'success': True, 'message': 'Round finished', 'round_winner': round_winner})
        else:
            return jsonify({'success': True, 'message': 'Choice recorded'})

    except Exception as e:
        app.logger.error(f"Error in make_choice: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

def determine_winner(choice1, choice2):
    if choice1 == choice2:
        return 'tie'
    elif (choice1 == 'rock' and choice2 == 'scissors') or \
         (choice1 == 'scissors' and choice2 == 'paper') or \
         (choice1 == 'paper' and choice2 == 'rock'):
        return 'player1'
    else:
        return 'player2'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config():
    try:
        return get_firebase_config()
    except Exception as e:
        app.logger.error(f"Error in config: {str(e)}")
        return jsonify({'error': 'Failed to get Firebase config'}), 500

if __name__ == '__main__':
    app.run(debug=True)