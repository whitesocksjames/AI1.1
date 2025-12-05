
# Assignment 1.1 – Find Train Connections

This repository contains my solution for **Assignment 1.1 – Find the best train connection** in the AI‑1 Systems Project.

The goal is to compute optimal train connections between two stations using Indian Railways schedule data, under four cost functions: `stops`, `timeintrain`, `price`, and `arrivaltime HH:MM:SS`.

---

## 1. Dependencies

- **Language**: Python 3.10+
- **Solver**: standard library only
    - `csv`, `datetime`, `heapq`, `collections`, `typing`, `argparse`, `pathlib`
- **For `verify.py` only** (provided by the assignment repository):
    - `requests`

Install `requests` (optional, for example checking):

```bash
python -m pip install requests
```

---

## 2. How to Run

All commands assume the current working directory is this assignment folder (containing `schedule.csv`, `mini-schedule.csv`, `problems.csv`, etc.).

### 2.1 Generate solutions for grading

```powershell
python main.py --mode assignment
```

- Reads `problems.csv`
- Writes `solutions.csv`

### 2.2 Generate and verify example solutions

```powershell
python main.py --mode examples
python verify.py example-solutions.csv
```

- Reads `example-problems.csv`
- Writes `example-solutions.csv`
- `verify.py` sends the example solutions to the server and prints a score and feedback.

---

## 3. Repository Structure (relevant files)

- `main.py`
    - CLI entrypoint (`--mode examples` / `--mode assignment`).

- `solver.py`
    - Loads problems and schedules.
    - Dispatches to the appropriate cost-function implementation.
    - Reconstructs connections and writes CSV output.

- `schedule_utils.py`
    - Parses `schedule.csv` / `mini-schedule.csv` into per-train lists.
    - Applies cross-day rules (arrival < previous departure → +1 day, departure < arrival → +1 day).
    - Builds a station index for fast lookup.

- `graph_builder.py`
    - Builds graphs for `stops`, `timeintrain`, and `price`.

- `search.py`
    - Generic `dijkstra(graph, start, is_goal)`.
    - `reconstruct_path(prev, goal)`.
    - Specialised `dijkstra_arrivaltime(...)` for the arrival-time cost function.

- Data / I/O files
    - `schedule.csv`, `mini-schedule.csv`
    - `example-problems.csv`, `example-solutions.csv`
    - `problems.csv`, `solutions.csv`
    - `verify.py`

---

## 4. Design Overview

High-level workflow:

1. Parse the selected schedule with `schedule_utils.py` (cached per file).
2. Build a graph tailored to the chosen cost function.
3. Run Dijkstra’s algorithm (generic or specialised) to find a best path.
4. Reconstruct the path into the required `Train : from_islno -> to_islno ; ...` format.
5. Compute the cost and write a CSV row for each problem.

Notes:

- For `stops`, `timeintrain`, and `price`, my results match the official example solutions and are accepted as optimal by `verify.py`.
- For `arrivaltime HH:MM:SS`, I follow the textual description (earliest departure at `HH:MM:SS`, explicit waiting and change times, cross-day roll-over). The resulting connections are consistent with the official examples; costs differ from the server’s internal convention for arrival days, which appears to be slightly different from the PDF but is undocumented.

---

## 5. Quick Reference

```powershell
cd E:\fau\AI\AI1\task1\assignment

# Example problems (for checking against server)
python main.py --mode examples
python verify.py example-solutions.csv

# Official problems (for grading)
python main.py --mode assignment
```

---

# Solution Summary (for grading)

This short summary follows the course “Solution Summary” guidelines and explains the main ideas behind the implementation.

---

## 1. Problem Understanding

The task is to find best train connections on a large Indian Railways timetable. Each problem specifies:

- `FromStation`, `ToStation`
- A schedule file (`schedule.csv` or `mini-schedule.csv`)
- A minimal change time (minutes)
- A cost function: `stops`, `timeintrain`, `price`, or `arrivaltime HH:MM:SS`

Output per problem:

- `ProblemNo`
- `Connection`: sequence of `TrainNo : from_islno -> to_islno` segments
- `Cost`: numeric or `DD:HH:MM:SS`, depending on the cost function

The problem is naturally modelled as a shortest-path search on a weighted graph. I use Dijkstra’s algorithm throughout.

---

## 2. Data and Time Handling

- Schedules are parsed into per-train ordered stop lists.
- For each train, times are normalised so that arrival and departure along the train are monotonic in real time:
    - If arrival at stop *n* < departure at stop *n−1* → add 1 day to arrival.
    - If departure at stop *n* < arrival at stop *n* → add 1 day to departure.
- A station index (`station_code → list of (train, index)`) enables fast lookup of all trains stopping at a station.
- Internally, I use `datetime` and convert to seconds since an arbitrary base date; the concrete date is irrelevant as long as roll-over is consistent.

---

## 3. Search Strategy and Graph Models

### 3.1 Algorithm choice

- All edge weights are non-negative → Dijkstra’s algorithm is appropriate.
- I use a generic `dijkstra(graph, start, is_goal)` for static graphs and a specialised variant for `arrivaltime` that incorporates current absolute time into the state.

### 3.2 Cost-function-specific graphs

**`stops`**

- Nodes: stations.
- Edges: between consecutive stops of the same train.
- Edge weight: 1 (entering a new station).

**`timeintrain`**

- Nodes: `(train, idx)`.
- Edges: along the same train with weight = travel time in seconds.
- Transfers: zero-cost edges between nodes at the same station.
- Super source connects to all nodes at `FromStation`.

**`price`**

- State: `(train, idx, used_segments)` with `used_segments` capped at 10.
- Same-train edges:
    - If `used_segments < 10`: cost `+1`, `used_segments + 1`.
    - Else: cost `+0`.
- Transfers: zero-cost, new train starts with `used_segments = 0`.

**`arrivaltime HH:MM:SS`**

- Interpret `HH:MM:SS` as earliest departure time `start_time`.
- State: `(train, idx)` with two tracked values:
    - `dist[state]`: total duration in seconds since `start_time`.
    - `cur_abs_time[state]`: absolute timestamp of arrival at this stop.
- Initialisation:
    - From `start_time` at `FromStation`, roll each candidate train’s departure forward to ≥ `start_time`, then compute arrival at the next stop.
- Transitions:
    - Continue on the same train: roll departure to ≥ current time, then compute arrival.
    - Change trains: wait `ChangeTime` seconds, then roll new train’s departure forward and compute arrival.
- Goal: first popped state whose station is `ToStation`; `dist[state]` is formatted as `DD:HH:MM:SS`.

For `stops`, `timeintrain`, and `price`, this design reproduces the official example solutions exactly. For `arrivaltime`, the connections are consistent with the examples, but the server uses a slightly different, undocumented convention for arrival days, leading to differing costs for problems 60–79.

---

## 4. Implementation Structure

- `schedule_utils.py`: parsing and time normalisation only.
- `graph_builder.py`: builds graphs for `stops`, `timeintrain`, `price`.
- `search.py`: generic and specialised Dijkstra + path reconstruction.
- `solver.py`: reads problem CSVs, calls the appropriate search, formats `Connection` and `Cost`.
- `main.py`: small CLI wrapper around `solver.py`.

This separation keeps the implementation modular and easier to reason about.

---

## 5. Correctness and Limitations

- For `stops`, `timeintrain`, and `price`, running
    - `python main.py --mode examples`
    - `python verify.py example-solutions.csv`
    shows that all example problems 0–59 are accepted as correct and optimal.
- For `arrivaltime`, my implementation strictly follows the textual rules (waiting, `ChangeTime`, cross-day roll-over), but the server expects slightly different arrival-day costs for problems 60–79. I document this mismatch instead of overfitting to an unknown internal formula.

---

## 6. Summary

This solution:

- Correctly parses and normalises the schedule data.
- Implements four cost functions with appropriate graph models and Dijkstra-based search.
- Matches the official examples for `stops`, `timeintrain`, and `price`.
- Provides a clear, modular structure and a principled arrival-time model consistent with the assignment description.

This concludes the solution summary for Assignment 1.1.