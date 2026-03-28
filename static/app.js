/* -------------------------------------------------------------------------
   Hanoi Crossing — Frontend
   ------------------------------------------------------------------------- */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let gameResult = null;   // full GameResultResponse from API
let stepIndex = -1;      // current position in history (-1 = initial)
let timer = null;        // playback interval id
let paused = false;

// Reconstructed state for stepping through moves
let boardState = null;   // { poles: {id: [disk,...]}, hands: {A: disk|null, B: disk|null} }

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

$$(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab").forEach((t) => t.classList.remove("active"));
    $$(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $(`#panel-${btn.dataset.tab}`).classList.add("active");
  });
});

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function fetchReplay() {
  const moves = $("#moves-input").value;
  const n_disks = parseInt($("#n-disks").value);
  const max_turns = parseInt($("#max-turns").value);

  const res = await fetch("/api/replay", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ moves, n_disks, max_turns }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Unknown error");
  }
  return res.json();
}

async function fetchRandom() {
  const n_disks = parseInt($("#n-disks").value);
  const max_turns = parseInt($("#max-turns").value);

  const res = await fetch("/api/random", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n_disks, max_turns }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Unknown error");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Board state management
// ---------------------------------------------------------------------------

function initBoardState(nDisks) {
  const poles = { "1a": [], "2": [], "3a": [], "1b": [], "3b": [] };

  // Player A: odd sizes (largest first), e.g. n=3 → [5, 3, 1]
  for (let i = 0; i < nDisks; i++) {
    poles["1a"].push({ size: 2 * nDisks - 1 - 2 * i, owner: "A" });
  }
  // Player B: even sizes (largest first), e.g. n=3 → [6, 4, 2]
  for (let i = 0; i < nDisks; i++) {
    poles["1b"].push({ size: 2 * nDisks - 2 * i, owner: "B" });
  }

  return {
    poles,
    hands: { A: null, B: null },
  };
}

function applyStep(record) {
  const { player, action, pole_id: pid } = record;

  // Illegal moves are no-ops — don't change board state
  if (!record.valid) return;

  if (action === "LIFT") {
    boardState.hands[player] = boardState.poles[pid].pop();
  } else if (action === "PLACE") {
    boardState.poles[pid].push(boardState.hands[player]);
    boardState.hands[player] = null;
  }
  // SKIP: nothing
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function createDiskEl(disk) {
  const el = document.createElement("div");
  el.className = `disk owner-${disk.owner} size-${disk.size}`;
  el.textContent = disk.size;
  return el;
}

function renderBoard() {
  // Render poles
  for (const pid of ["1a", "2", "3a", "1b", "3b"]) {
    const stack = $(`#stack-${pid}`);
    stack.innerHTML = "";
    for (const disk of boardState.poles[pid]) {
      stack.appendChild(createDiskEl(disk));
    }
  }

  // Render hands
  for (const p of ["A", "B"]) {
    const zone = $(`#hand-${p}`);
    const diskEl = $(`#hand-disk-${p}`);
    diskEl.innerHTML = "";

    if (boardState.hands[p]) {
      zone.style.display = "flex";
      diskEl.appendChild(createDiskEl(boardState.hands[p]));
    } else {
      zone.style.display = "none";
    }
  }
}

function renderHistory() {
  const log = $("#history-log");
  log.innerHTML = "";

  if (!gameResult) return;

  for (let i = 0; i < gameResult.history.length; i++) {
    const r = gameResult.history[i];
    const div = document.createElement("div");
    const pClass = r.player === "A" ? "player-a" : "player-b";
    div.className = `move-entry ${pClass}`;
    if (i === stepIndex) div.classList.add("active");

    const poleStr = r.pole_id ? ` ${r.pole_id}` : "";
    const label = `T${r.turn} ${r.player}: ${r.action}${poleStr}`;

    if (!r.valid) {
      div.classList.add("illegal");
      div.textContent = `${label} ✗ ${r.reason}`;
    } else {
      div.textContent = label;
    }
    log.appendChild(div);
  }

  // Scroll active entry into view
  const active = log.querySelector(".active");
  if (active) active.scrollIntoView({ block: "nearest" });
}

// ---------------------------------------------------------------------------
// Playback
// ---------------------------------------------------------------------------

function getSpeed() {
  // Slider: 50 (fast) to 1000 (slow)
  return parseInt($("#speed-slider").value);
}

function startPlayback() {
  if (timer) clearInterval(timer);
  paused = false;
  $("#btn-pause").textContent = "Pause";

  timer = setInterval(() => {
    if (paused) return;
    stepForward();
    if (stepIndex >= gameResult.history.length - 1) {
      clearInterval(timer);
      timer = null;
      showFinalStatus();
    }
  }, getSpeed());
}

function stepForward() {
  if (!gameResult) return;
  if (stepIndex >= gameResult.history.length - 1) return;

  stepIndex++;
  applyStep(gameResult.history[stepIndex]);
  renderBoard();
  renderHistory();
  updateTurnDisplay();
}

function updateTurnDisplay() {
  if (stepIndex < 0) {
    $("#turn-display").textContent = "Turn 0";
    return;
  }
  const r = gameResult.history[stepIndex];
  $("#turn-display").textContent = `Turn ${r.turn} — ${r.player}`;
}

function showFinalStatus() {
  const el = $("#status-display");
  if (gameResult.winner) {
    el.textContent = `Player ${gameResult.winner} wins!`;
    el.style.color = gameResult.winner === "A" ? "#ff6b6b" : "#4ecdc4";
  } else {
    el.textContent = "Draw";
    el.style.color = "#888";
  }
}

function resetPlayback() {
  if (timer) clearInterval(timer);
  timer = null;
  paused = false;
  stepIndex = -1;
  $("#btn-pause").textContent = "Pause";
  $("#status-display").textContent = "";

  if (gameResult) {
    boardState = initBoardState(gameResult.final_state.n_disks);
    renderBoard();
    renderHistory();
    updateTurnDisplay();
  }
}

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

function showError(msg) {
  const el = $("#error");
  el.textContent = msg;
  el.style.display = "block";
}

function clearError() {
  $("#error").style.display = "none";
}

// ---------------------------------------------------------------------------
// Run handlers
// ---------------------------------------------------------------------------

async function handleRun(fetchFn) {
  clearError();
  if (timer) clearInterval(timer);

  // Disable buttons during fetch
  $$("#btn-replay, #btn-random").forEach((b) => (b.disabled = true));

  try {
    gameResult = await fetchFn();
    stepIndex = -1;
    boardState = initBoardState(gameResult.final_state.n_disks);

    // Show playback controls and history
    $("#playback").style.display = "flex";
    $("#history-container").style.display = "flex";
    $("#status-display").textContent = "";

    renderBoard();
    renderHistory();
    updateTurnDisplay();

    // Auto-start playback
    startPlayback();
  } catch (e) {
    showError(e.message);
  } finally {
    $$("#btn-replay, #btn-random").forEach((b) => (b.disabled = false));
  }
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

$("#btn-replay").addEventListener("click", () => handleRun(fetchReplay));
$("#btn-random").addEventListener("click", () => handleRun(fetchRandom));

$("#btn-pause").addEventListener("click", () => {
  if (!timer && !paused) return;
  paused = !paused;
  $("#btn-pause").textContent = paused ? "Resume" : "Pause";
  if (!paused && !timer) startPlayback();
});

$("#btn-reset").addEventListener("click", resetPlayback);

$("#speed-slider").addEventListener("input", () => {
  if (timer && !paused) {
    clearInterval(timer);
    startPlayback();
  }
});

// ---------------------------------------------------------------------------
// Initial render — empty board
// ---------------------------------------------------------------------------

boardState = initBoardState(parseInt($("#n-disks").value));
renderBoard();