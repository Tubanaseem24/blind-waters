"""FastAPI adapter for the Blind Waters browser interface.

Run from the repository root:
    uvicorn blind_waters.web_api:app --app-dir src --reload
"""
from __future__ import annotations

import random
import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from blind_waters.game import Game

app = FastAPI(title="Blind Waters API", version="1.0.0")
_sessions: Dict[str, Game] = {}
WEB_DIR = Path(__file__).resolve().parents[2] / "web"


class FireRequest(BaseModel):
    session_id: str = Field(min_length=1)
    row: int = Field(ge=0, le=9)
    col: int = Field(ge=0, le=9)


def get_game(session_id: str) -> Game:
    game = _sessions.get(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game session not found. Start a new battle.")
    return game


def make_state(session_id: str, game: Game) -> dict:
    state = game.to_dict()
    state.update({
        "session_id": session_id,
        "your_fleet_remaining": sum(not ship.is_sunk() for ship in game.human_board.ships),
        "enemy_fleet_remaining": sum(not ship.is_sunk() for ship in game.agent_board.ships),
        "agent_name": type(game.agent).__name__,
        "agent_description": "Random baseline opponent. Hunt-and-Target and Probability agents are not implemented yet.",
        "game_over": game.is_over(),
    })
    return state


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Blind Waters API"}


@app.post("/api/new")
def new_game():
    session_id = uuid.uuid4().hex
    seed = random.randrange(0, 2**31)
    game = Game(seed=seed)
    _sessions[session_id] = game
    return make_state(session_id, game)


@app.get("/api/state/{session_id}")
def game_state(session_id: str):
    return make_state(session_id, get_game(session_id))


@app.post("/api/fire")
def fire(request: FireRequest):
    game = get_game(request.session_id)
    try:
        moves = game.human_fire(request.row, request.col)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "state": make_state(request.session_id, game),
        "you": moves["you"],
        "agent": moves["agent"],
    }


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")
