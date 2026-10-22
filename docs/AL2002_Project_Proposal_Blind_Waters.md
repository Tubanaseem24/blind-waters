# Project Proposal

**FAST — National University of Computer and Emerging Sciences**
FAST School of Computing · Karachi Campus · Department of Software Engineering
AL-2002 Artificial Intelligence (Laboratory) · Fall 2026
Semester Lab Project · Weightage 1 mark

---

## Group Information

| | Name | Roll Number | Section | Role in the project |
|---|---|---|---|---|
| Leader | Tuba Naseem | 24K-3063 | [to fill] | Game engine, interface, integration, and report coordination |
| Member 2 | Anzeela Shafi | 24K-3082 | [to fill] | CSP ship placement and hunt-and-target agent |
| Member 3 | Aiza Humayun | 24K-3116 | [to fill] | Probability agent, evaluation harness, and charts |

| Field | Entry |
|---|---|
| **Project Title** | Blind Waters |
| **Project Idea** | Own idea (needs approval). Battleship-style game with an AI opponent |
| **Category** | Part A — Game |
| **GitHub Repository URL** | [add repository link] |
| **Date of Submission** | [to fill on submission] |

---

## 1. Project Title and Summary

Blind Waters is a Battleship-style game in which a human player and an AI agent each secretly place a fleet on a 10x10 grid, then take turns firing at cells to locate the opponent's ships. The human plays against the AI through a simple interface that shows hits, misses, and sunk ships. Because the AI cannot see the human's fleet, it must maintain a belief about where ships are likely to be and update that belief after every shot. Using constraint reasoning to generate and check valid fleet layouts, and probability to choose the most promising cell, the AI finds ships in far fewer shots than a player guessing at random. A plain program that fires in a fixed order cannot adapt to the evidence it collects, and this adaptive reasoning is what the AI adds.

---

## 2. Problem Statement and Motivation

Battleship looks simple, but locating a hidden fleet is a reasoning problem with a large search space. On a 10x10 board with the standard fleet of five ships, there are billions of legal arrangements, so listing them all during a single turn is impossible. The information is also uncertain: each shot reveals only whether one cell is a hit or a miss, so after most turns the player knows very little. Many constraints interact at once. Ships cannot overlap, must stay on the board, and every miss removes a cell from every arrangement that covered it, while every hit narrows the possible positions of its ship. Human players cope with rules of thumb such as firing in a checkerboard pattern and searching around hits, which work but waste many shots. Solving this well is worthwhile because the same skill of tracking a belief under partial observation applies to radar tracking, robotic search and rescue, and any game with hidden information.

---

## 3. Problem Formulation

### 3.1 PEAS Description

| Component | Description for your project |
|---|---|
| Performance measure | Number of shots needed to sink all opponent ships (fewer is better); win rate against the human and against baseline agents |
| Environment | A 10x10 grid with a fleet of five ships (lengths 5, 4, 3, 3, 2). The opponent's fleet is hidden and placed at random from a fixed seed. Turns alternate between the human and the agent |
| Actuators | Fire at a chosen cell; display the belief heatmap and the chosen move in the interface |
| Sensors | Hit or miss responses for each fired cell; a sunk notification when a ship is fully hit; the public board state |

### 3.2 Environment and Agent Type

| Property | Classification — tick one |
|---|---|
| Observability | Fully observable ☐ **Partially observable ☒** |
| Determinism | **Deterministic ☒** ☐ Stochastic |
| Change over time | **Static ☒** ☐ Dynamic |
| State and actions | **Discrete ☒** ☐ Continuous |
| Agents | Single-agent ☐ **Multi-agent / adversarial ☒** |
| Agent type | Simple reflex ☐ **Model-based ☒** ☐ Goal-based ☐ Utility-based ☐ Learning ☐ |

The agent is model-based: it keeps an internal model of possible opponent fleets, updates it after every shot, and chooses the cell with the best chance of a hit.

### 3.3 Problem Representation

| Element | Your representation |
|---|---|
| State representation | A 10x10 grid where each cell is unknown, hit, or miss, plus the list of sunk ships. The agent also keeps a belief value for each unknown cell |
| Actions / moves | Fire at any unknown cell (up to 100 actions per game) |
| Initial state | Empty grid with no shots fired. The opponent's fleet is placed at random and valid under the placement rules |
| Goal or terminal test | All five ships of the opponent are sunk |
| Cost, utility, fitness or evaluation | Cost is the number of shots taken. Utility is the negative shot count, and the evaluation reports the average shots per game |

---

## 4. Proposed AI Approach

| # | Technique | Role in the project | Own code or library |
|---|---|---|---|
| 1 | Constraint satisfaction (CSP) with backtracking and MRV | Generates valid fleet layouts for the agent and checks legality of placements (no overlap, within bounds) | Own code |
| 2 | Probability-based search (heatmap of placement counts) | Core technique. Counts, for each unknown cell, how many valid fleet layouts consistent with all shots cover it, and fires at the highest-count cell | Own code |
| 3 | Hunt-and-target heuristic search | Baseline-plus agent that searches randomly until it hits, then searches neighbouring cells in a line. Compared against the core technique | Own code |

**Baseline:** A random agent that fires at uniformly chosen unknown cells.

**Explanation.** Blind Waters has partial observability and a huge number of hidden configurations, which makes exhaustive search impossible but leaves room for reasoning. The CSP formulation lets the agent enumerate and sample only legal fleet layouts, so its beliefs reflect real game rules. The probability-based agent treats each layout consistent with the shots so far as equally likely and counts the layouts that cover each cell. Its heuristic is the count itself: cells covered by more consistent layouts have a higher hit chance and are fired at first. The evaluation function is the expected information gain of a shot, reduced to a simple hit probability to keep the computation fast on a 10x10 board. The hunt-and-target agent uses a simpler heuristic, the adjacency of known hits, so it serves as a meaningful second technique to compare against. The random agent is the baseline that every technique must beat.

### 4.1 Planned Class Design

- **Cell**: attributes `row`, `col`, `state` (unknown, hit, miss). Methods `is_unknown()`, `mark(result)`.
- **Ship**: attributes `name`, `length`, `cells`, `hits`. Methods `place(cells)`, `register_hit(cell)`, `is_sunk()`.
- **Board**: attributes `size`, `grid`, `ships`. Methods `can_place(ship, start, orientation)`, `place_ship(...)`, `receive_shot(cell)`, `all_sunk()`.
- **Placer (CSP)**: attributes `board_size`, `fleet_spec`. Methods `solve(assignment)` (backtracking), `select_variable_mrv()`, `is_consistent()`, `random_layout(seed)`.
- **Agent** (abstract): methods `choose_shot(state)`, `observe(result)`, `reset()`.
  - **RandomAgent(Agent)**: baseline, fires at random unknown cells.
  - **HuntTargetAgent(Agent)**: heuristic search agent.
  - **ProbabilityAgent(Agent)**: samples layouts with `Placer` and fires at the highest-count cell.
- **Game**: attributes `human_board`, `agent_board`, `turn`, `history`. Methods `play_turn()`, `is_over()`, `winner()`.
- **Evaluator**: attributes `seeds`, `agents`, `board_sizes`. Methods `run_experiments()`, `summarise()`, `plot_results()`.

Relationships: `Game` owns two `Board` objects, each containing `Ship` objects built from `Cell`s. `Agent` is an abstract base class, and the three concrete agents plug into `Game` and `Evaluator` through the same interface. `ProbabilityAgent` uses `Placer` for its internal sampling.

---

## 5. Scope

**In scope**

| # | Feature | Why it is essential |
|---|---|---|
| 1 | Valid random fleet placement using a CSP backtracking solver | The game cannot start without legal boards, and the agent's belief depends on it |
| 2 | Human-versus-agent game loop with turn handling, hit and miss feedback, and a winner check | This is the playable core of the project |
| 3 | Probability-based agent that fires at the highest-count cell | This is the main AI technique and the one that must be evaluated |
| 4 | Random and hunt-and-target baseline agents behind the same interface | Without comparison, no claim about the AI's performance can be made |
| 5 | Evaluation harness with seeded experiments and at least three charts | Proves the AI works, using the same boards and seeds for every agent |

**Out of scope**

- Online multiplayer over a network.
- Minimax with alpha-beta pruning, because the game has hidden information and the standard minimax assumptions do not hold. This is discussed in the report as a comparison that does not fit.
- Neural networks or reinforcement learning for the agent.
- Custom fleet editors, non-standard fleets, and boards larger than 10x10 in the main experiments.
- Polished graphics, sound, animation, and mobile versions.
- Opponent modelling with Naive Bayes. This is an optional extension if time allows and is not required for completion.

---

## 6. Data or Environment Source

| Field | Entry |
|---|---|
| Source name and URL | Generated by the project's own seeded board generator (no external URL) |
| Type | Generated / simulated ☒ |
| Access requirements | No key needed ☒ |
| Approximate size | Each game uses one 10x10 board. Experiments use 1,000 seeded boards per agent, which is a few megabytes at most |
| Licence / terms of use | Original code by the project team, released for academic use under the course rules |
| Offline fallback | The game generates boards locally and needs no network access. Generated seeds for all experiment boards are saved to `data/seeds.csv` so that every run can reproduce the same boards without regeneration |

Boards are generated using the CSP placer with a fixed random seed. The same seeds are used for every agent so that the comparisons are fair.

---

## 7. Evaluation Plan

| Item | Plan |
|---|---|
| What will be compared | Probability-based agent (core) against hunt-and-target agent and random agent |
| Metric(s) | Average number of shots to win, median shots, and win rate in the human-versus-agent mode |
| Baseline | Random agent |
| Test instances / test set | 1,000 seeded boards on a 10x10 grid with the standard fleet. Additional runs on 6x6 and 8x8 boards to show how performance scales |
| Number of runs and seed | 1,000 games per agent per board size, using seeds 0 to 999 for all agents |
| Planned charts (at least three) | (1) Histogram of shots to win for each agent. (2) Bar or box plot of average shots per agent across board sizes. (3) Cumulative fraction of ships sunk against number of shots, one curve per agent. (4) Optional: a belief heatmap snapshot mid-game for the report |

---

## 8. Division of Work

| Member | Modules / components owned | Approximate share |
|---|---|---|
| Tuba Naseem (Leader) | Board, Cell, Ship classes; Game loop and turn handling; terminal or Pygame interface; integration and final report coordination | 34% |
| Anzeela Shafi | CSP Placer with backtracking and MRV; Random and Hunt-and-target agents; placement tests | 33% |
| Aiza Humayun | ProbabilityAgent and its heatmap; Evaluator, seeded experiments, and charts; statistical summary | 33% |

All members write tests for their own modules and contribute to the final report. Commits are tracked in the GitHub repository.

---

## 9. Milestones and Timeline

| # | Milestone — what will be demonstrably working | Target date | Owner |
|---|---|---|---|
| 1 | Board, Cell, and Ship classes pass unit tests; a valid 10x10 fleet is printed on screen | Week 4 | Tuba Naseem |
| 2 | CSP Placer generates 100 valid fleets from seeds and rejects overlapping or out-of-bounds placements | Week 5 | Anzeela Shafi |
| 3 | Human-versus-random-agent game plays a full game in the terminal with correct hit, miss, and sunk messages | Week 7 | Tuba Naseem |
| 4 | Hunt-and-target agent and ProbabilityAgent both play complete games and print shots-to-win for 100 seeded boards | Week 9 | Anzeela Shafi and Aiza Humayun |
| 5 | Evaluator runs 1,000 seeded games per agent and produces the planned charts | Week 11 | Aiza Humayun |
| 6 | Experiments complete, final integration, documentation and repository cleanup | Week 15 | All members |

---

## 10. Expected Outcome and Risks

A working submission lets a user run the program, place their fleet automatically, and play against the agent in the terminal or a simple window. The interface shows hits, misses, and sunk ships, and optionally displays the agent's heatmap so the user can see its reasoning. We expect the probability-based agent to finish games in noticeably fewer shots than the hunt-and-target agent, and both to beat the random agent by a wide margin. The report will show the averages, distributions, and scaling across board sizes.

The first risk is that the probability calculation becomes too slow when the agent counts many layouts. If this happens, we will sample a fixed number of consistent layouts per turn instead of enumerating them all, and report the sample size used. The second risk is that the team falls behind schedule because of the full board logic and the evaluation work. If this occurs, we will cut the interface to terminal only and limit the main experiments to the 10x10 board, keeping the 6x6 and 8x8 runs as optional.

---

**For office use — Lab Instructor**

Proposal status: Approved ☐ Approved with changes ☐ Revision required ☐
Comments: ______________________________________
Signature and date: ______________________________

*End of Project Proposal*
