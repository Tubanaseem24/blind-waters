const API = "/api";
const letters = "ABCDEFGHIJ";
let gameState = null;
let busy = false;
let toastTimer = null;

const $ = (id) => document.getElementById(id);

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

async function request(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "The command could not be completed.");
  return data;
}

function createGrid(gridId, colsId, rowsId, isEnemy) {
  const grid = $(gridId);
  grid.innerHTML = "";
  $(colsId).innerHTML = "";
  $(rowsId).innerHTML = "";
  for (let col = 0; col < 10; col++) {
    const label = document.createElement("span");
    label.textContent = letters[col];
    $(colsId).appendChild(label);
  }
  for (let row = 0; row < 10; row++) {
    const label = document.createElement("span");
    label.textContent = String(row + 1);
    $(rowsId).appendChild(label);
    for (let col = 0; col < 10; col++) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell";
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-label", `${letters[col]}${row + 1}`);
      cell.dataset.row = row;
      cell.dataset.col = col;
      if (isEnemy) {
        cell.addEventListener("click", () => fireAt(row, col));
      } else {
        cell.disabled = true;
      }
      grid.appendChild(cell);
    }
  }
}

function renderBoard(gridId, values, enemy = false) {
  const cells = $(gridId).children;
  values.forEach((row, r) => row.forEach((value, c) => {
    const cell = cells[r * 10 + c];
    cell.className = "cell";
    if (value === "hit" || value === "sunk") {
      cell.classList.add("hit");
      if (value === "sunk") cell.classList.add("sunk");
      cell.setAttribute("aria-label", `${letters[c]}${r + 1}: hit`);
    } else if (value === "miss") {
      cell.classList.add("miss");
      cell.setAttribute("aria-label", `${letters[c]}${r + 1}: miss`);
    } else if (!enemy && value === "ship") {
      cell.classList.add("ship");
      cell.setAttribute("aria-label", `${letters[c]}${r + 1}: ship`);
    } else {
      cell.setAttribute("aria-label", `${letters[c]}${r + 1}: unknown`);
    }
    if (enemy) {
      cell.disabled = busy || !gameState || gameState.game_over || value !== "unknown";
    }
  }));
}

function renderLog(entries) {
  const log = $("battle-log");
  log.innerHTML = "";
  const recent = entries.slice(-12).reverse();
  $("log-count").textContent = `${String(entries.length).padStart(2, "0")} EVENTS`;
  if (!recent.length) {
    const empty = document.createElement("div");
    empty.className = "empty-log";
    empty.textContent = "No transmissions yet. Deploy to begin operations.";
    log.appendChild(empty);
    return;
  }
  recent.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "log-entry" + (entry.startsWith("Agent") ? " ai" : "");
    const time = document.createElement("span");
    time.className = "log-time";
    time.textContent = entry.startsWith("Agent") ? "AI" : "YOU";
    const message = document.createElement("span");
    message.textContent = entry.replace(/^You fired at /, "Fired at ").replace(/^Agent fired at /, "Fired at ");
    item.append(time, message);
    log.appendChild(item);
  });
}

function render() {
  if (!gameState) return;
  renderBoard("enemy-grid", gameState.enemy_waters, true);
  renderBoard("own-grid", gameState.your_fleet, false);

  $("your-shots").textContent = String(gameState.you_shots).padStart(2, "0");
  $("ai-shots").textContent = String(gameState.agent_shots).padStart(2, "0");
  const enemyHits = gameState.enemy_waters.flat().filter(v => v === "hit" || v === "sunk").length;
  $("enemy-hits").textContent = String(enemyHits).padStart(2, "0");
  $("fleet-left").textContent = String(gameState.your_fleet_remaining).padStart(2, "0");
  const accuracy = gameState.you_shots ? Math.round(enemyHits / gameState.you_shots * 100) : 0;
  $("accuracy").textContent = gameState.you_shots ? accuracy + "%" : "—";
  $("accuracy-bar").style.width = accuracy + "%";

  $("agent-engine").textContent = gameState.agent_name;
  $("agent-mode").textContent = gameState.agent_name.toUpperCase() + " / BASELINE";
  const last = gameState.log.length ? gameState.log[gameState.log.length - 1] : "No shots recorded";
  $("last-action").textContent = last.length > 35 ? last.slice(0, 32) + "…" : last;
  renderLog(gameState.log);

  if (gameState.game_over) {
    $("mission-status").textContent = "COMPLETE";
    $("mission-title").textContent = gameState.winner === "you" ? "Enemy fleet neutralized" : "Your fleet was lost";
    $("mission-sub").textContent = "Engagement complete. Review the battle log.";
    $("turn-indicator").innerHTML = '<span class="turn-dot"></span> MISSION COMPLETE';
    $("instruction-text").textContent = "Battle concluded. Start a new operation to play again.";
    $("start-button").textContent = "↻ NEW OPERATION";
    $("result-title").textContent = gameState.winner === "you" ? "VICTORY" : "DEFEAT";
    $("result-copy").textContent = gameState.winner === "you"
      ? `You neutralized the opposing fleet in ${gameState.you_shots} shots.`
      : `The AI neutralized your fleet in ${gameState.agent_shots} shots.`;
    $("result-emblem").textContent = gameState.winner === "you" ? "✦" : "⚑";
    $("result-modal").classList.remove("hidden");
  } else if (gameState.you_shots || gameState.agent_shots) {
    $("mission-status").textContent = "ENGAGED";
    $("mission-title").textContent = "Battle in progress";
    $("mission-sub").textContent = "Select an unknown hostile coordinate to fire.";
    $("turn-indicator").innerHTML = '<span class="turn-dot"></span> YOUR TURN / SELECT TARGET';
    $("instruction-text").textContent = busy ? "AI is calculating its response…" : "Select an unknown square in Hostile Waters to fire. The opponent responds automatically.";
    $("start-button").textContent = "↻ RESTART BATTLE";
  } else {
    $("mission-status").textContent = "DEPLOYED";
    $("mission-title").textContent = "Fleet deployment complete";
    $("mission-sub").textContent = "Your fleet is positioned. Choose your first target.";
    $("turn-indicator").innerHTML = '<span class="turn-dot"></span> YOUR TURN / SELECT TARGET';
    $("instruction-text").textContent = "Select any unknown square in Hostile Waters to fire. The AI responds after your shot.";
    $("start-button").textContent = "↻ RESTART BATTLE";
  }
}

async function startGame() {
  if (busy) return;
  busy = true;
  $("start-button").disabled = true;
  try {
    gameState = await request("/new", { method: "POST" });
    $("result-modal").classList.add("hidden");
    render();
    showToast("Fleet deployed. Choose your first target.");
  } catch (error) {
    showToast(error.message);
  } finally {
    busy = false;
    $("start-button").disabled = false;
    render();
  }
}

async function fireAt(row, col) {
  if (!gameState || busy || gameState.game_over) return;
  const current = gameState.enemy_waters[row][col];
  if (current !== "unknown") {
    showToast("That coordinate has already been targeted.");
    return;
  }
  busy = true;
  render();
  $("turn-indicator").innerHTML = '<span class="turn-dot"></span> TRANSMITTING SHOT…';
  try {
    const result = await request("/fire", {
      method: "POST",
      body: JSON.stringify({ session_id: gameState.session_id, row, col })
    });
    gameState = result.state;
    const outcome = result.you.result === "hit" ? "DIRECT HIT" : "SHOT MISSED";
    showToast(`${letters[col]}${row + 1} — ${outcome}`);
    render();
  } catch (error) {
    showToast(error.message);
  } finally {
    busy = false;
    render();
  }
}

async function checkConnection() {
  try {
    await request("/health");
    $("connection-label").textContent = "API CONNECTED";
    $("connection-label").style.color = "#70dca9";
  } catch {
    $("connection-label").textContent = "API OFFLINE";
    $("connection-label").style.color = "#ff6e67";
    showToast("Start the Blind Waters API server to play.");
  }
}

createGrid("enemy-grid", "enemy-cols", "enemy-rows", true);
createGrid("own-grid", "own-cols", "own-rows", false);
$("start-button").addEventListener("click", startGame);
$("new-game-top").addEventListener("click", startGame);
$("play-again").addEventListener("click", startGame);
checkConnection();
