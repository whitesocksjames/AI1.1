from typing import List, Dict, Any


def build_connection_string(segments: List[Dict[str, Any]]) -> str:
    """Segments: each dict must have 'train', 'from_islno', 'to_islno'.

    They are assumed to be ordered along the path; consecutive entries
    with same train will be merged.
    """
    if not segments:
        return ""

    merged: List[Dict[str, Any]] = []
    cur = dict(segments[0])
    for seg in segments[1:]:
        if seg["train"] == cur["train"] and seg["from_islno"] == cur["to_islno"]:
            cur["to_islno"] = seg["to_islno"]
        else:
            merged.append(cur)
            cur = dict(seg)
    merged.append(cur)

    parts = []
    for seg in merged:
        parts.append(f"{seg['train']} : {seg['from_islno']} -> {seg['to_islno']}")
    return " ; ".join(parts)
