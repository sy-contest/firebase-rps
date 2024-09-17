let database;
let currentGameId = null;
let currentPlayer = null;

// Fetch Firebase config from server
fetch('/config')
    .then(response => response.json())
    .then(firebaseConfig => {
        firebase.initializeApp(firebaseConfig);
        database = firebase.database();
        initializeEventListeners();
    })
    .catch(error => console.error('Error loading Firebase config:', error));

function initializeEventListeners() {
    document.getElementById('login-button').addEventListener('click', login);

    document.querySelectorAll('.choice').forEach(button => {
        button.addEventListener('click', () => confirmChoice(button.dataset.choice));
    });
}

function login() {
    const username = document.getElementById('username').value;
    const gameId = document.getElementById('game-id').value;

    if (!username || !gameId) {
        alert('Please enter both username and game ID');
        return;
    }

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, game_id: gameId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentGameId = gameId;
            currentPlayer = data.player;
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('game-area').style.display = 'block';
            document.getElementById('current-game-id').textContent = currentGameId;
            listenForGameUpdates();
        } else {
            alert(data.message || 'Failed to login');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while logging in');
    });
}

function confirmChoice(choice) {
    if (confirm(`Are you sure you want to choose ${choice}?`)) {
        makeChoice(choice);
    }
}

function makeChoice(choice) {
    console.log(`Making choice: ${choice}`);
    fetch('/make_choice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ game_id: currentGameId, player: currentPlayer, choice: choice }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'An error occurred while making a choice');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Choice made successfully');
            disableChoiceButtons();
        } else {
            console.error('Error making choice:', data.message);
            alert('Error making choice: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while making a choice: ' + error.message);
    });
}

function disableChoiceButtons() {
    document.querySelectorAll('.choice').forEach(button => {
        button.disabled = true;
    });
}

function enableChoiceButtons() {
    document.querySelectorAll('.choice').forEach(button => {
        button.disabled = false;
    });
}

function listenForGameUpdates() {
    if (!database) {
        console.error('Firebase database not initialized');
        return;
    }
    const gameRef = database.ref(`games/${currentGameId}`);
    gameRef.on('value', (snapshot) => {
        const game = snapshot.val();
        document.getElementById('player1-name').textContent = `${game.player1} (${game.player1_score || 0})`;
        document.getElementById('player2-name').textContent = game.player2 ? `${game.player2} (${game.player2_score || 0})` : 'Waiting for player...';

        if (game.status === 'finished') {
            let result = '';
            if (game.winner === 'player1') {
                result = currentPlayer === 'player1' ? 'You win the game!' : 'You lose the game!';
            } else if (game.winner === 'player2') {
                result = currentPlayer === 'player2' ? 'You win the game!' : 'You lose the game!';
            } else {
                result = 'The game ended in a tie!';
            }
            document.getElementById('result').textContent = result;
            disableChoiceButtons();
            document.getElementById('choices').style.display = 'none'; // Optionally hide choices
        } else if (game.status === 'playing') {
            const playerChoice = game[`${currentPlayer}_choice`];
            if (!playerChoice) {
                enableChoiceButtons();
            } else {
                disableChoiceButtons();
            }
            document.getElementById('result').textContent = '';
        }
    });
}