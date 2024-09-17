import os
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    game_id = db.reference('games').push().key
    db.reference(f'games/{game_id}').set({
        'player1': request.json['player_name'],
        'player2': None,
        'player1_choice': None,
        'player2_choice': None,
        'status': 'waiting'
    })
    return jsonify({'game_id': game_id})

@app.route('/join_game', methods=['POST'])
def join_game():
    game_id = request.json['game_id']
    player_name = request.json['player_name']
    game_ref = db.reference(f'games/{game_id}')
    game = game_ref.get()
    
    if game and game['status'] == 'waiting':
        game_ref.update({
            'player2': player_name,
            'status': 'playing'
        })
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Game not found or already full'})

@app.route('/make_choice', methods=['POST'])
def make_choice():
    game_id = request.json['game_id']
    player = request.json['player']
    choice = request.json['choice']
    
    game_ref = db.reference(f'games/{game_id}')
    game_ref.child(f'{player}_choice').set(choice)
    
    game = game_ref.get()
    if game['player1_choice'] and game['player2_choice']:
        winner = determine_winner(game['player1_choice'], game['player2_choice'])
        game_ref.update({
            'status': 'finished',
            'winner': winner
        })
    
    return jsonify({'success': True})

def determine_winner(choice1, choice2):
    if choice1 == choice2:
        return 'tie'
    elif (choice1 == 'rock' and choice2 == 'scissors') or \
         (choice1 == 'scissors' and choice2 == 'paper') or \
         (choice1 == 'paper' and choice2 == 'rock'):
        return 'player1'
    else:
        return 'player2'

if __name__ == '__main__':
    app.run(debug=True)