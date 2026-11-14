"""FastAPI server: game routes and the static web page."""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from blind_waters.game import Game

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Blind Waters")
games = {}


class ShotIn(BaseModel):
    game_id: str
    row: int = Field(ge=0, le=9)
    col: int = Field(ge=0, le=9)


@app.post("/api/new-game")
def new_game(seed: Optional[int] = None):
    game_id = uuid.uuid4().hex
    games[game_id] = Game(seed=seed)
    return {"game_id": game_id, **games[game_id].to_dict()}


@app.get("/api/state/{game_id}")
def state(game_id: str):
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="unknown game")
    return game.to_dict()


@app.post("/api/shoot")
def shoot(shot: ShotIn):
    game = games.get(shot.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="unknown game")
    try:
        move = game.human_fire(shot.row, shot.col)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    return {"move": move, "state": game.to_dict()}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
