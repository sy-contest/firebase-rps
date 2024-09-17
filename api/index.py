import os
import json
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv
from .config import get_firebase_config  # Change this line

load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Initialize Firebase
firebase_service_account = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
cred = credentials.Certificate(firebase_service_account)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    try:
        game_id = db.reference('games').push().key
        db.reference(f'games/{game_id}').set({
            'player1': request.json['player_name'],
            'player2': None,
            'player1_choice': None,
            'player2_choice': None,
            'player1_score': 0,
            'player2_score': 0,
            'status': 'waiting'
        })
        app.logger.info(f"Created game: {game_id}")
        return jsonify({'success': True, 'game_id': game_id})
    except Exception as e:
        app.logger.error(f"Error in create_game: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'An error occurred while creating the game'}), 500

@app.route('/join_game', methods=['POST'])
def join_game():
    try:
        game_id = request.json['game_id']
        player_name = request.json['player_name']
        
        game_ref = db.reference(f'games/{game_id}')
        game = game_ref.get()
        
        if not game:
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        if game['status'] != 'waiting':
            return jsonify({'success': False, 'message': 'Game is already full'}), 400
        
        game_ref.update({
            'player2': player_name,
            'status': 'playing'
        })
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error in join_game: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'An error occurred while joining the game'}), 500

@app.route('/make_choice', methods=['POST'])
def make_choice():
    try:
        app.logger.info(f"Received make_choice request: {request.json}")
        game_id = request.json.get('game_id')
        player = request.json.get('player')
        choice = request.json.get('choice')
        
        if not all([game_id, player, choice]):
            missing = [k for k, v in {'game_id': game_id, 'player': player, 'choice': choice}.items() if not v]
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        app.logger.info(f"Updating game {game_id} for {player} with choice {choice}")
        game_ref = db.reference(f'games/{game_id}')
        game = game_ref.get()
        
        if not game:
            raise ValueError(f"Game with ID {game_id} not found")
        
        app.logger.info(f"Current game state: {game}")
        
        # Check if it's the player's turn
        if player == 'player1' and game.get('player1_choice') is not None:
            raise ValueError("Player 1 has already made a choice")
        if player == 'player2' and game.get('player2_choice') is not None:
            raise ValueError("Player 2 has already made a choice")
        
        game_ref.child(f'{player}_choice').set(choice)
        
        app.logger.info(f"Fetching updated game data")
        game = game_ref.get()
        app.logger.info(f"Updated game data: {game}")
        
        if game.get('player1_choice') and game.get('player2_choice'):
            app.logger.info("Both players have made their choices")
            round_winner = determine_winner(game['player1_choice'], game['player2_choice'])
            app.logger.info(f"Round winner: {round_winner}")
            
            if round_winner != 'tie':
                new_score = game.get(f'{round_winner}_score', 0) + 1
                app.logger.info(f"Updating {round_winner} score to {new_score}")
                game_ref.child(f'{round_winner}_score').set(new_score)
            
            if game.get(f'{round_winner}_score', 0) >= 3:
                app.logger.info(f"Game finished, winner: {round_winner}")
                game_ref.update({
                    'status': 'finished',
                    'winner': round_winner
                })
            else:
                app.logger.info("Resetting choices for next round")
                game_ref.update({
                    'player1_choice': None,
                    'player2_choice': None
                })
        
        return jsonify({'success': True})
    except ValueError as ve:
        app.logger.error(f"ValueError in make_choice: {str(ve)}", exc_info=True)
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Error in make_choice: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

def determine_winner(choice1, choice2):
    if choice1 == choice2:
        return 'tie'
    elif (choice1 == 'rock' and choice2 == 'scissors') or \
         (choice1 == 'scissors' and choice2 == 'paper') or \
         (choice1 == 'paper' and choice2 == 'rock'):
        return 'player1'
    else:
        return 'player2'

@app.route('/config')
def config():
    return get_firebase_config()

if __name__ == '__main__':
    app.run(debug=True)