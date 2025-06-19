// /GrammarGo_Pro/project/static/js/main.js (最終修正版)
document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    // --- DOM Elements ---
    const lobbyContainer = document.getElementById('lobby-container');
    const createRoomBtn = document.getElementById('create-room-btn');
    const joinRoomBtn = document.getElementById('join-room-btn');
    const roomIdInput = document.getElementById('room-id-input');
    
    const gameContainer = document.getElementById('game-container');
    const roomTitle = document.getElementById('room-title');
    const board = document.getElementById('game-board');
    const playerList = document.getElementById('player-list');
    const turnIndicator = document.getElementById('turn-indicator');
    const rollButton = document.getElementById('roll-button');
    const joinButton = document.getElementById('join-button');
    const playerNameInput = document.getElementById('player-name');
    const log = document.getElementById('log');
    const loginArea = document.getElementById('login-area');
    const gameControls = document.getElementById('game-controls');
    
    const questionModal = document.getElementById('question-modal');
    const submitAnswerButton = document.getElementById('submit-answer-button');
    const chanceDestinyModal = document.getElementById('chance-destiny-modal');
    const chanceButton = document.getElementById('chance-button');
    const destinyButton = document.getElementById('destiny-button');
    
    const diceContainer = document.getElementById('dice-container');
    const dice = document.getElementById('dice');

    // --- Game State Variables ---
    const boardSize = 30;
    let mySid = null;
    let myPlayerId = null;
    let currentQuestionRule = null;
    
    // *** 修改這裡：從 body 的 data-room-id 屬性讀取房間 ID ***
    const currentRoomId = document.body.dataset.roomId;

    // --- Initialization ---
    function init() {
        initBoard();
        if (currentRoomId) {
            showGame(currentRoomId);
        } else {
            showLobby();
        }
    }

    function initBoard() {
        board.innerHTML = '';
        for (let i = 0; i <= boardSize; i++) {
            const square = document.createElement('div');
            square.classList.add('square');
            square.id = `square-${i}`;
            square.textContent = i;
            if (i === 0) square.classList.add('start');
            if (i === boardSize) square.classList.add('finish');
            if (i > 0 && i < boardSize && i % 5 === 0) {
                square.classList.add('square-chance-destiny');
                square.textContent = '';
            }
            board.appendChild(square);
        }
    }

    // --- (其他所有 JavaScript 程式碼與上一版完全相同，此處為求簡潔省略) ---
    // --- 你可以繼續使用上一版我提供的完整 main.js，只需修改上面 const currentRoomId 的定義方式即可 ---
    
    // --- View Management ---
    function showLobby() {
        lobbyContainer.style.display = 'block';
        gameContainer.style.display = 'none';
    }

    function showGame(roomId) {
        lobbyContainer.style.display = 'none';
        gameContainer.style.display = 'block';
        roomTitle.textContent = `房間號碼: ${roomId}`;
    }

    // --- SocketIO Handlers ---
    socket.on('connect', () => {
        mySid = socket.id;
        console.log('Connected with SID:', mySid);
        if (currentRoomId) {
            console.log('In a game room, sending reconnect request...');
            socket.emit('reconnect_request');
        }
    });

    socket.on('update_game_state', (state) => {
        console.log("Received game state update:", state);
        if (state.player_sids && state.player_sids[mySid]) {
            myPlayerId = state.player_sids[mySid];
        }
        
        if (myPlayerId && state.players[myPlayerId]) {
            loginArea.style.display = 'none';
            gameControls.style.display = 'block';
        } else {
            loginArea.style.display = 'block';
            gameControls.style.display = 'none';
        }

        updatePlayerList(state.players);
        updateBoard(state.players);
        updateTurnIndicator(state);
        handleGameStatus(state);
    });

    socket.on('reconnect_failed', () => {
        console.log("Reconnect failed. Showing login area.");
        loginArea.style.display = 'block';
        gameControls.style.display = 'none';
    });
    
    socket.on('error', (data) => {
        alert("錯誤：" + data.message);
        window.location.href = '/';
    });

    socket.on('message', (data) => {
        const p = document.createElement('p'); p.textContent = data.text; log.appendChild(p); log.scrollTop = log.scrollHeight;
        const rollMatch = data.text.match(/擲出了 (\d) 點/);
        if (rollMatch) {
            const rollResult = parseInt(rollMatch[1]); dice.classList.remove('rolling'); dice.textContent = rollResult;
            setTimeout(() => { diceContainer.style.display = 'none'; }, 1500);
        }
    });

    socket.on('show_question', (data) => {
        currentQuestionRule = data.rule; document.getElementById('question-rule').textContent = data.rule;
        document.getElementById('question-prompt').textContent = data.prompt; document.getElementById('answer-input').value = '';
        questionModal.style.display = 'flex';
    });

    socket.on('show_result', (data) => { alert(data.explanation); questionModal.style.display = 'none'; });
    
    socket.on('show_chance_destiny', () => { chanceDestinyModal.style.display = 'flex'; });


    // --- UI Update Functions ---
    function updatePlayerList(players) {
        playerList.innerHTML = '';
        for (const playerId in players) {
            const p = players[playerId];
            const connectionStatus = p.is_connected ? '在線上' : '已離線';
            const statusClass = p.is_connected ? 'online' : 'offline';
            const li = document.createElement('li');
            li.innerHTML = `<span style="color: ${p.color}; font-weight: bold;">●</span> ${p.name} (在第 ${p.position} 格) - <span class="${statusClass}">${connectionStatus}</span>`;
            playerList.appendChild(li);
        }
    }

    function updateBoard(players) {
        document.querySelectorAll('.player-piece').forEach(p => p.remove());
        Object.keys(players).forEach((playerId, index) => {
            const p = players[playerId];
            if (p.is_connected) {
                const piece = document.createElement('div');
                piece.classList.add('player-piece');
                piece.style.backgroundColor = p.color;
                piece.style.transform = `translate(${index * 5}px, ${index * 5}px)`;
                const square = document.getElementById(`square-${p.position}`);
                if (square) square.appendChild(piece);
            }
        });
    }

    function updateTurnIndicator(state) {
        if (state.status === 'playing' && state.player_order.length > 0) {
            const currentTurnPlayerId = state.player_order[state.turn_index];
            const currentPlayer = state.players[currentTurnPlayerId];
            if(currentPlayer) {
                turnIndicator.textContent = `輪到: ${currentPlayer.name}`;
                rollButton.disabled = (currentTurnPlayerId !== myPlayerId);
            }
        }
    }

    function handleGameStatus(state) {
        if (state.status === 'finished') {
            rollButton.disabled = true;
            turnIndicator.textContent = `🎉 獲勝者: ${state.winner} 🎉`;
        } else if (state.status === 'waiting') {
            turnIndicator.textContent = '等待至少2位玩家...';
        }
    }

    // --- Event Listeners ---
    createRoomBtn.addEventListener('click', () => { window.location.href = '/create_room'; });
    joinRoomBtn.addEventListener('click', () => {
        const roomId = roomIdInput.value.trim();
        if (roomId) window.location.href = `/game/${roomId}`;
    });
    
    joinButton.addEventListener('click', () => {
        const name = playerNameInput.value.trim();
        if (name && currentRoomId) socket.emit('join_game', { name: name, room_id: currentRoomId });
    });

    rollButton.addEventListener('click', () => {
        rollButton.disabled = true;
        diceContainer.style.display = 'block';
        dice.classList.add('rolling');
        dice.textContent = '?';
        setTimeout(() => { socket.emit('roll_dice', { room_id: currentRoomId }); }, 1000);
    });

    submitAnswerButton.addEventListener('click', () => {
        const answer = document.getElementById('answer-input').value;
        if (!currentQuestionRule) { alert('錯誤：找不到目前的問題！'); return; }
        socket.emit('submit_answer', { answer, rule: currentQuestionRule, room_id: currentRoomId });
        currentQuestionRule = null;
    });

    chanceButton.addEventListener('click', () => {
        socket.emit('chose_chance_destiny', { choice: 'chance', room_id: currentRoomId });
        chanceDestinyModal.style.display = 'none';
    });

    destinyButton.addEventListener('click', () => {
        socket.emit('chose_chance_destiny', { choice: 'destiny', room_id: currentRoomId });
        chanceDestinyModal.style.display = 'none';
    });

    // --- Run Initialization ---
    init();
});