import csv
from typing import Dict, Any, List, Tuple

from schedule_utils import load_schedule, build_station_index, parse_hhmmss
from search import dijkstra, reconstruct_path, dijkstra_arrivaltime
from formatter import build_connection_string


def _load_problems(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def _get_schedule(trains_cache: Dict[str, Dict[str, Any]], schedule_file: str):
    if schedule_file not in trains_cache:
        trains_cache[schedule_file] = {
            "trains": load_schedule(schedule_file),
        }
        trains_cache[schedule_file]["station_index"] = build_station_index(trains_cache[schedule_file]["trains"])
    return trains_cache[schedule_file]


def _solve_single(problem: Dict[str, Any], trains_cache: Dict[str, Dict[str, Any]]) -> Tuple[str, Any]:
    from_station = problem["FromStation"].strip()
    to_station = problem["ToStation"].strip()
    schedule_name = problem["Schedule"].strip()
    change_time = int(problem["ChangeTime"]) * 60  # minutes -> seconds

    # CostFunction can be e.g. "stops", "timeintrain", "price",
    # or "arrivaltime 19:00:00" (with target arrival time).
    raw_cf = problem["CostFunction"].strip()
    parts = raw_cf.split()
    cost_function = parts[0]
    target_time_str = parts[1] if len(parts) > 1 else None

    schedule_data = _get_schedule(trains_cache, schedule_name)
    trains = schedule_data["trains"]
    station_index = schedule_data["station_index"]

    # Dispatch to the specific strategy for each cost function
    if cost_function == "stops":
        from graph_builder import build_graph_stops

        graph, start_node, goal_station = build_graph_stops(trains, station_index, from_station, to_station)

        def graph_wrap(node):
            for nxt, w, e in graph(node):
                yield nxt, w, e

        def is_goal(node):
            return node == goal_station

        prev, dist, goal_node = dijkstra(graph_wrap, start_node, is_goal)
        if goal_node is None:
            return "", float("inf")

        segments = reconstruct_path(prev, goal_node)
        conn_str = build_connection_string(segments)
        return conn_str, dist[goal_node]

    elif cost_function == "timeintrain":
        from graph_builder import build_graph_timeintrain

        graph, start_nodes, goal_nodes = build_graph_timeintrain(trains, station_index, from_station, to_station)

        super_source = ("SOURCE",)

        def graph_wrap(node):
            if node == super_source:
                for n in start_nodes:
                    yield n, 0.0, None
                return
            for nxt, w, e in graph(node):
                yield nxt, w, e

        def is_goal(node):
            return node in goal_nodes

        prev, dist, goal_node = dijkstra(graph_wrap, super_source, is_goal)
        if goal_node is None:
            return "", float("inf")
        segments = reconstruct_path(prev, goal_node)
        conn_str = build_connection_string(segments)
        return conn_str, dist[goal_node]

    elif cost_function == "arrivaltime":
        if target_time_str is None:
            raise ValueError("arrivaltime requires a start time, e.g. 'arrivaltime 11:30:00'")
        start_time = parse_hhmmss(target_time_str)

        # 使用 specialised arrivaltime dijkstra，它直接以 start_time 为 0
        # 返回每个状态的最小总耗时（秒）
        prev, dist, goal_state = dijkstra_arrivaltime(
            trains,
            station_index,
            from_station,
            to_station,
            start_time,
            change_time,
        )
        if goal_state is None:
            return "", float("inf")

        segments = reconstruct_path(prev, goal_state)
        conn_str = build_connection_string(segments)

        # dijkstra_arrivaltime already measures time from start_time,
        # so dist[goal_state] is the total travel time in seconds
        total_sec = int(dist[goal_state])
        days, rem = divmod(total_sec, 24 * 3600)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        cost_str = f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
        return conn_str, cost_str

    elif cost_function == "price":
        from graph_builder import build_graph_price

        graph, start_states, goal_states = build_graph_price(trains, station_index, from_station, to_station)
        super_source = ("SOURCE",)

        def graph_wrap(node):
            if node == super_source:
                for n in start_states:
                    yield n, 0.0, None
                return
            for nxt, w, e in graph(node):
                yield nxt, w, e

        def is_goal(node):
            return node in goal_states

        prev, dist, goal_node = dijkstra(graph_wrap, super_source, is_goal)
        if goal_node is None:
            return "", float("inf")

        segments = reconstruct_path(prev, goal_node)
        conn_str = build_connection_string(segments)
        # dist[goal_node] already represents the minimal ticket price
        return conn_str, dist[goal_node]

    else:
        # include raw value for easier debugging
        raise ValueError(f"Unknown cost function {raw_cf}")


def solve_problems(problem_file: str, output_file: str, force_schedule: str | None = None):
    problems = _load_problems(problem_file)
    trains_cache: Dict[str, Dict[str, Any]] = {}

    with open(output_file, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["ProblemNo", "Connection", "Cost"])

        for p in problems:
            if force_schedule is not None:
                p["Schedule"] = force_schedule

            conn, cost = _solve_single(p, trains_cache)

            # arrivaltime returns a formatted string, other cost
            # functions return numeric values
            if isinstance(cost, (int, float)):
                out_cost = int(cost) if cost != float("inf") else "inf"
            else:
                out_cost = cost

            writer.writerow([p["ProblemNo"], conn, out_cost])
