from typing import Dict, Any, Tuple, List, Set


def build_graph_stops(
    trains: Dict[str, List[Dict[str, Any]]],
    station_index: Dict[str, List[Tuple[str, int]]],
    from_station: str,
    to_station: str,
):
    """Graph for `stops` cost function.

    Nodes are *stations* (station codes). Each train segment between two
    consecutive stops adds an edge from station A to station B with cost 1
    (entering a new station). This directly matches the definition in the
    assignment: number of stations entered by train, excluding the origin.
    """

    # Build adjacency list: station -> list of (next_station, edge_cost, edge_data)
    adj: Dict[str, List[Tuple[str, float, Dict[str, Any]]]] = {}

    for train_no, stops in trains.items():
        for i in range(len(stops) - 1):
            cur = stops[i]
            nxt = stops[i + 1]
            a = cur["station"]
            b = nxt["station"]
            if a not in adj:
                adj[a] = []
            adj[a].append(
                (
                    b,
                    1.0,
                    {
                        "train": train_no,
                        "from_islno": cur["islno"],
                        "to_islno": nxt["islno"],
                    },
                )
            )

    def graph(node: str):
        return adj.get(node, [])

    start_node = from_station
    goal_node = to_station
    return graph, start_node, goal_node


def build_graph_timeintrain(trains: Dict[str, List[Dict[str, Any]]], station_index: Dict[str, List[Tuple[str, int]]],
                            from_station: str, to_station: str):
    """Graph where nodes are (train, idx) and cost is time in train in seconds."""

    def graph(node):
        train_no, idx = node
        stops = trains[train_no]
        cur = stops[idx]
        res = []
        # continue on train
        if idx + 1 < len(stops):
            nxt = stops[idx + 1]
            dt = (nxt["arr"] - cur["dep"]).total_seconds()
            res.append(((train_no, idx + 1), float(dt), {
                "train": train_no,
                "from_islno": cur["islno"],
                "to_islno": nxt["islno"],
            }))
        # transfers at station without cost in this metric
        station = cur["station"]
        for t2, i2 in station_index[station]:
            if t2 == train_no and i2 == idx:
                continue
            res.append(((t2, i2), 0.0, None))
        return res

    start_nodes = [(t, i) for (t, i) in station_index[from_station]]
    goal_nodes: Set[Tuple[str, int]] = set()
    for t, i in station_index[to_station]:
        goal_nodes.add((t, i))

    return graph, start_nodes, goal_nodes


def build_graph_price(
    trains: Dict[str, List[Dict[str, Any]]],
    station_index: Dict[str, List[Tuple[str, int]]],
    from_station: str,
    to_station: str,
):
    """Graph for `price` cost function.

    State keeps track of how many segments have been used on the *current* train,
    capped at 10. This models the rule that a train ticket costs 10 and covers
    an arbitrary number of segments on that train, while a stop ticket costs 1
    per segment.

    State: (train_no, idx, used_segments) where used_segments in [0, 10].
    Edge weights are price increments.
    """

    day = 24 * 3600

    def graph(state):
        train_no, idx, used = state
        stops = trains[train_no]
        cur = stops[idx]
        res: List[Tuple[Tuple[str, int, int], float, Dict[str, Any] | None]] = []

        # continue on same train
        if idx + 1 < len(stops):
            nxt = stops[idx + 1]
            # each additional segment on the same train costs 1 until we reach
            # 10 segments; beyond that it's free (already paid train ticket).
            new_used = used + 1
            if new_used > 10:
                new_used = 10
            # if we haven't reached 10 yet, this segment costs 1; otherwise 0
            seg_cost = 1.0 if used < 10 else 0.0
            res.append(
                (
                    (train_no, idx + 1, new_used),
                    seg_cost,
                    {
                        "train": train_no,
                        "from_islno": cur["islno"],
                        "to_islno": nxt["islno"],
                    },
                )
            )

        # transfer to another train at same station, price does not change yet,
        # we will start counting segments on the new train from zero.
        station = cur["station"]
        for t2, i2 in station_index[station]:
            if t2 == train_no and i2 == idx:
                continue
            res.append(((t2, i2, 0), 0.0, None))

        return res

    # starting states: from_station on any train, with 0 segments used so far
    start_states: List[Tuple[str, int, int]] = []
    for t, i in station_index[from_station]:
        start_states.append((t, i, 0))

    goal_states: Set[Tuple[str, int, int]] = set()
    for t, i in station_index[to_station]:
        # any used count is acceptable at destination
        for used in range(0, 11):
            goal_states.add((t, i, used))

    return graph, start_states, goal_states


## arrivaltime graph is now implemented via a specialised Dijkstra
## in `search.dijkstra_arrivaltime`, so we no longer expose a generic
## graph builder here.
