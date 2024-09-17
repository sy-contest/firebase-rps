// Initialize Firebase (replace with your own config)
const firebaseConfig = {
    apiKey: "AIzaSyBXnt1GwSFE1MCZIguzDCJt8pJ2aqW4JQY",
    authDomain: "rps-con.firebaseapp.com",
    projectId: "rps-con",
    storageBucket: "rps-con.appspot.com",
    messagingSenderId: "213355497362",
    appId: "1:213355497362:web:2c0bd14ff9b4141577e34b"
  };

firebase.initializeApp(firebaseConfig);
const database = firebase.database();

let currentGameId = null;
let currentPlayer = null;

document.getElementById('create-game').addEventListener('click', createGame);
document.getElementById('join-game').addEventListener('click', joinGame);

document.querySelectorAll('.choice').forEach(button => {
    button.addEventListener('click', () => makeChoice(button.dataset.choice));
});

function createGame() {
    const playerName = document.getElementById('player-name').value;
    if (!playerName) {
        alert('Please enter your name');
        return;
    }

    fetch('/create_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName }),
    })
    .then(response => response.json())
    .then(data => {
        currentGameId = data.game_id;
        currentPlayer = 'player1';
        document.getElementById('current-game-id').textContent = currentGameId;
        document.getElementById('player1-name').textContent = playerName;
        document.getElementById('game-setup').style.display = 'none';
        document.getElementById('game-area').style.display = 'block';
        listenForGameUpdates();
    });
}

function joinGame() {
    const playerName = document.getElementById('player-name').value;
    const gameId = document.getElementById('game-id').value;
    if (!playerName || !gameId) {
        alert('Please enter your name and game ID');
        return;
    }

    fetch('/join_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName, game_id: gameId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentGameId = gameId;
            currentPlayer = 'player2';
            document.getElementById('current-game-id').textContent = currentGameId;
            document.getElementById('player2-name').textContent = playerName;
            document.getElementById('game-setup').style.display = 'none';
            document.getElementById('game-area').style.display = 'block';
            listenForGameUpdates();
        } else {
            alert(data.message);
        }
    });
}

function makeChoice(choice) {
    fetch('/make_choice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ game_id: currentGameId, player: currentPlayer, choice: choice }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelectorAll('.choice').forEach(button => {
                button.disabled = true;
            });
        }
    });
}

function listenForGameUpdates() {
    const gameRef = database.ref(`games/${currentGameId}`);
    gameRef.on('value', (snapshot) => {
        const game = snapshot.val();
        document.getElementById('player1-name').textContent = game.player1;
        document.getElementById('player2-name').textContent = game.player2 || 'Waiting for player...';

        if (game.status === 'finished') {
            let result = '';
            if (game.winner === 'tie') {
                result = "It's a tie!";
            } else if (game.winner === currentPlayer) {
                result = 'You win!';
            } else {
                result = 'You lose!';
            }
            document.getElementById('result').textContent = result;
            document.querySelectorAll('.choice').forEach(button => {
                button.disabled = true;
            });
        }
    });
}