import os
import json
from flask import Flask, render_template, request, jsonify, session
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

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    game_id = request.json.get('game_id')

    if not username or not game_id:
        return jsonify({'success': False, 'message': 'Username and game ID are required'}), 400

    game_ref = db.reference(f'games/{game_id}')
    game = game_ref.get()

    if not game:
        return jsonify({'success': False, 'message': 'Invalid game ID'}), 404

    if game['player1'] == username:
        player = 'player1'
    elif game['player2'] == username:
        player = 'player2'
    else:
        return jsonify({'success': False, 'message': 'Username not associated with this game'}), 403

    session['username'] = username
    session['game_id'] = game_id
    session['player'] = player

    return jsonify({'success': True, 'player': player})

@app.route('/make_choice', methods=['POST'])
def make_choice():
    if 'username' not in session or 'game_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    choice = request.json.get('choice')
    game_id = session['game_id']
    player = session['player']

    # ... (rest of the make_choice logic)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config():
    return get_firebase_config()

if __name__ == '__main__':
    app.run(debug=True)