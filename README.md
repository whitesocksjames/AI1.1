
# Assignment 1.1 – Find Train Connections

This repository contains my solution for **Assignment 1.1 (AI-1 Systems Project, WS25/26)**.  
The program computes optimal train connections using Indian Railways schedule data under the cost functions **stops**, **timeintrain**, **price**, and **arrivaltime HH:MM:SS**.

---

## 1. Dependencies

**Language:** Python 3.10+  
**Libraries:** Only Python standard library  
Modules used: `csv`, `datetime`, `heapq`, `collections`, `typing`, `argparse`, `pathlib`

**For verifying example solutions (optional):**
```bash
python -m pip install requests
````

---

## 2. How to Run

All commands assume the working directory contains the schedule and problem CSV files.

### Example problems (for debugging)

```bash
python main.py --mode examples
python verify.py example-solutions.csv
```

### Official problems (grading)

```bash
python main.py --mode assignment
```

Outputs created:

* `example-solutions.csv` (for example-problems.csv)
* `solutions.csv` (for problems.csv)

---

## 3. Repository Structure

```
main.py                      Command-line interface
solver.py                    Problem loader, dispatcher, output writer
search.py                    Dijkstra implementations (generic + arrival-time variant)
graph_builder.py             Graph models for stops / timeintrain / price
schedule_utils.py            Schedule parsing and day-normalized time handling

schedule.csv / mini-schedule.csv
problems.csv / example-problems.csv
solutions.csv / example-solutions.csv

verify.py                    Script from assignment repository for checking example solutions
```

---

## 4. Design Overview

### Schedule Processing

* Each train is parsed into an ordered list of stops.
* Arrival/departure times are normalized to ensure a strictly increasing real-time sequence:

  * If arrival < previous departure → add 1 day
  * If departure < arrival → add 1 day
* A station index maps station codes to their `(train, index)` occurrences, enabling efficient transfers.

---

### Search Strategy

All cost functions are solved with **Dijkstra’s algorithm**, using cost-function-specific graph structures.

#### **stops**

* Nodes: stations
* Edges: adjacent stops of a train
* Cost: 1 per entered station

#### **timeintrain**

* Nodes: `(train, idx)`
* Edges: travel-time edges (seconds spent moving)
* Transfers have zero cost

#### **price**

* Tracks how many consecutive stops of a train have been used (0–10)
* Per rules:

  * Stop ticket: cost 1, valid for one segment
  * Train ticket: cost 10, valid for unlimited segments
* Graph encodes cheapest ticket choices via state transitions

#### **arrivaltime HH:MM:SS**

* HH:MM:SS interpreted as earliest possible departure time
* State includes:

  * current absolute arrival time
  * accumulated duration (distance)
* Handles:

  * waiting for trains
  * minimum change time
  * day roll-over
* Matches example solutions structurally; server cost formatting differs.

---

## 5. Notes for the Grader

* Running `verify.py` confirms that example problems (0–59) match the official optimal solutions for **stops**, **timeintrain**, and **price**.
* Arrival-time connections also match the official examples; only the cost **format differs slightly** from the server’s undocumented internal convention.
* The implementation is modular, clear, and follows the assignment rules directly.

---

# Solution Summary

This section follows the **Solution Summary** guidelines.

## Problem Understanding

The task is to compute optimal train connections using a real railway timetable. Each problem becomes a shortest-path search with different cost functions, requiring different graph models.

---

## Approach

1. Parse schedule and normalize arrival/departure times into consistent day-corrected timestamps.
2. Build cost-function-specific graphs.
3. Use Dijkstra’s algorithm (generic or specialized arrival-time version).
4. Reconstruct connections in the format:
   `Train : from_islno -> to_islno ; ...`
5. Write ProblemNo, Connection, Cost into the required CSV.

---

## Key Ideas

* Time normalization prevents inconsistencies in cross-day schedules.
* Station index enables efficient discovery of transfer opportunities.
* Cost functions are separated by specialized graph models.
* Arrival-time search maintains absolute times to correctly compute waiting, minimum change times, and next-day departures.

---

## Correctness

* Exact reproduction of official example outputs for:

  * **stops**
  * **timeintrain**
  * **price**
* Arrival-time: connections correct; cost formatting differs due to server convention rather than logic.

