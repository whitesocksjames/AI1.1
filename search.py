from typing import Dict, Hashable, Any, Tuple, List
import heapq


def dijkstra(graph, start, is_goal):
    """Generic Dijkstra.

    graph(node) -> iterable of (next_node, edge_cost, edge_data)
    is_goal(node) -> bool

    Returns (prev, dist, goal_node) where prev is mapping child->(parent, edge_data).
    """
    dist: Dict[Hashable, float] = {start: 0.0}
    prev: Dict[Hashable, Tuple[Hashable | None, Any]] = {start: (None, None)}
    pq: List[Tuple[float, Hashable]] = [(0.0, start)]

    while pq:
        cost, node = heapq.heappop(pq)
        if cost != dist.get(node, float("inf")):
            continue
        if is_goal(node):
            return prev, dist, node

        for nxt, w, e_data in graph(node):
            new_cost = cost + w
            if new_cost < dist.get(nxt, float("inf")):
                dist[nxt] = new_cost
                prev[nxt] = (node, e_data)
                heapq.heappush(pq, (new_cost, nxt))

    return prev, dist, None


def reconstruct_path(prev: Dict[Hashable, Tuple[Hashable | None, Any]], goal) -> List[Any]:
    path: List[Any] = []
    node = goal
    while node is not None and node in prev:
        parent, edge_data = prev[node]
        if edge_data is not None:
            path.append(edge_data)
        node = parent
    path.reverse()
    return path


def dijkstra_arrivaltime(
    trains,
    station_index,
    from_station: str,
    to_station: str,
    start_time,
    change_time_seconds: int,
):
    """Dijkstra specialised for `arrivaltime`.

    dist[state] stores the *elapsed travel time in seconds* since the
    given ``start_time`` (not an absolute timestamp). To decide whether
    we can still catch a train, we additionally maintain the current
    absolute timestamp for each state.

    A state is represented as ``(train_no, idx)``, meaning we are on
    train ``train_no`` at stop index ``idx`` in ``trains[train_no]``.
    """

    import math

    day = 24 * 3600

    def roll_forward(base_ts: float, target_ts: float) -> float:
        """Roll ``target_ts`` forward in 24h steps until it is >= ``base_ts``.

        Both arguments are absolute timestamps (seconds since epoch).
        """

    start_ts = start_time.timestamp()

    # dist: minimal elapsed time; cur_abs_time: absolute arrival timestamp
    dist: Dict[Hashable, float] = {}
    prev: Dict[Hashable, Tuple[Hashable | None, Any]] = {}
    cur_abs_time: Dict[Hashable, float] = {}
    pq: List[Tuple[float, Hashable]] = []

    # Initialization: we are at from_station, waiting from start_ts
    for t, i in station_index[from_station]:
        stops = trains[t]
        cur = stops[i]

        # 需要至少一个后续区间
        if i + 1 >= len(stops):
            continue

        seg_from = cur
        seg_to = stops[i + 1]

        dep_raw = seg_from["dep"].timestamp()
        # earliest departure we can catch on this train
        dep = roll_forward(start_ts, dep_raw)
        arr_raw = seg_to["arr"].timestamp()
        if arr_raw < dep:
            arr_raw += day
        arrival_abs = arr_raw

        state = (t, i + 1)
        travel_time = arrival_abs - start_ts  # 从 start_ts 到这里的总耗时
        if travel_time < dist.get(state, math.inf):
            dist[state] = travel_time
            cur_abs_time[state] = arrival_abs
            prev[state] = (None, {
                "train": t,
                "from_islno": seg_from["islno"],
                "to_islno": seg_to["islno"],
            })
            pq.append((travel_time, state))

    if not pq:
        return prev, dist, None

    heapq.heapify(pq)

    def is_goal(state):
        t, idx = state
        return trains[t][idx]["station"] == to_station

    best_goal_state = None

    while pq:
        cur_cost, state = heapq.heappop(pq)
        if cur_cost != dist.get(state, math.inf):
            continue

        if is_goal(state):
            best_goal_state = state
            break

        t, idx = state
        stops = trains[t]
        cur = stops[idx]
        current_time = cur_abs_time[state]

        # 1) 继续坐同一辆车
        if idx + 1 < len(stops):
            seg_from = cur
            seg_to = stops[idx + 1]

            dep_raw = seg_from["dep"].timestamp()
            dep = roll_forward(current_time, dep_raw)
            arr_raw = seg_to["arr"].timestamp()
            if arr_raw < dep:
                arr_raw += day
            arrival_abs = arr_raw

            new_state = (t, idx + 1)
            new_cost = arrival_abs - start_ts
            if new_cost < dist.get(new_state, math.inf):
                dist[new_state] = new_cost
                cur_abs_time[new_state] = arrival_abs
                prev[new_state] = (state, {
                    "train": t,
                    "from_islno": seg_from["islno"],
                    "to_islno": seg_to["islno"],
                })
                heapq.heappush(pq, (new_cost, new_state))

        # 2) 在当前站换乘到别的车
        station = cur["station"]
        for t2, i2 in station_index[station]:
            if t2 == t and i2 == idx:
                continue
            stops2 = trains[t2]
            if i2 + 1 >= len(stops2):
                continue

            seg_from2 = stops2[i2]
            seg_to2 = stops2[i2 + 1]

            earliest = current_time + change_time_seconds
            dep_raw = seg_from2["dep"].timestamp()
            dep = roll_forward(earliest, dep_raw)
            arr_raw = seg_to2["arr"].timestamp()
            if arr_raw < dep:
                arr_raw += day
            arrival_abs = arr_raw

            new_state = (t2, i2 + 1)
            new_cost = arrival_abs - start_ts
            if new_cost < dist.get(new_state, math.inf):
                dist[new_state] = new_cost
                cur_abs_time[new_state] = arrival_abs
                prev[new_state] = (state, {
                    "train": t2,
                    "from_islno": seg_from2["islno"],
                    "to_islno": seg_to2["islno"],
                })
                heapq.heappush(pq, (new_cost, new_state))

    return prev, dist, best_goal_state
