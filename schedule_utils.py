import csv
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Any

TimePoint = datetime

TIME_FMT = "%H:%M:%S"


def _parse_time(t: str) -> datetime:
    t = t.strip().strip("'")
    return datetime(2000, 1, 1, *map(int, t.split(":")))


def parse_hhmmss(t: str) -> datetime:
    """Parse HH:MM:SS (no quotes) as a datetime on base date.

    Used for arrivaltime start times.
    """
    t = t.strip()
    return datetime(2000, 1, 1, *map(int, t.split(":")))


def load_schedule(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load schedule csv into dict[train_no] -> ordered list of stops.

    Handles overnight roll-over so that arrival/dep times are non-decreasing
    within a train.
    """
    trains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            train_no = row["Train No."].strip().strip("'")
            islno = int(row["islno"])
            station = row["station Code"].strip()
            arr_raw = row["Arrival time"]
            dep_raw = row["Departure time"]

            arr = _parse_time(arr_raw)
            dep = _parse_time(dep_raw)

            trains[train_no].append({
                "islno": islno,
                "station": station,
                "arr": arr,
                "dep": dep,
            })

    # fix overnight within each train
    for train_no, stops in trains.items():
        stops.sort(key=lambda s: s["islno"])
        last_time: datetime | None = None
        day_offset = timedelta(0)
        for s in stops:
            # arrival
            if last_time is None:
                s["arr"] += day_offset
                s["dep"] += day_offset
                last_time = s["dep"]
                continue

            arr = s["arr"] + day_offset
            if arr < last_time:
                day_offset += timedelta(days=1)
                arr = s["arr"] + day_offset
            dep = s["dep"] + day_offset
            if dep < arr:
                dep += timedelta(days=1)

            s["arr"] = arr
            s["dep"] = dep
            last_time = dep

    return trains


def build_station_index(trains: Dict[str, List[Dict[str, Any]]]):
    """Return mapping station -> list of (train_no, index) where index into trains[train_no]."""
    index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for train_no, stops in trains.items():
        for i, stop in enumerate(stops):
            index[stop["station"]].append((train_no, i))
    return index
