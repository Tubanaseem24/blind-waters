"""Agents share one interface: choose_shot, observe, reset."""

from abc import ABC, abstractmethod


class Agent(ABC):
    @abstractmethod
    def choose_shot(self, state):
        ...

    def observe(self, cell, result) -> None:
        pass

    def reset(self) -> None:
        pass


class RandomAgent(Agent):
    """Baseline: fires at uniformly random unknown cells."""

    def choose_shot(self, state):
        raise NotImplementedError


class HuntTargetAgent(Agent):
    """Hunts randomly, then targets neighbours of known hits."""

    def choose_shot(self, state):
        raise NotImplementedError


class ProbabilityAgent(Agent):
    """Core agent: fires at the cell covered by the most consistent layouts."""

    def choose_shot(self, state):
        raise NotImplementedError
