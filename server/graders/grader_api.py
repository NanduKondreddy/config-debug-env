"""Grader API wrapper layer for OpenEnv validator compatibility.

OpenEnv validator expects graders to:
1. Be callable
2. Return float only (not tuple)
3. Return values in [0.0, 1.0] range

Our graders return (reward, error_msg, bugs_fixed).
This wrapper extracts just the float reward.
"""

from server.graders.json_grader import grade_task1 as _g1
from server.graders.yaml_grader import grade_task2 as _g2
from server.graders.dockerfile_grader import grade_task3 as _g3


def _extract(result):
    """Extract float reward from grader result tuple or return as-is if already float.
    Clamp to strict (0.001, 0.999) range for validator compatibility."""
    if isinstance(result, tuple):
        r = float(result[0])
    else:
        r = float(result)
    # Strict bounds: not 0.0, not 1.0
    return max(0.001, min(0.999, r))


def grade_task1(x):
    """Task 1 (JSON) grader wrapper."""
    return _extract(_g1(x))


def grade_task2(x):
    """Task 2 (YAML) grader wrapper."""
    return _extract(_g2(x))


def grade_task3(x):
    """Task 3 (Dockerfile) grader wrapper."""
    return _extract(_g3(x))
