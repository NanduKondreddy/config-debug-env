"""Grader API wrapper layer for OpenEnv validator compatibility.

OpenEnv validator expects graders to:
1. Be callable
2. Return tuple: (reward: float, error_msg: str, bugs_fixed: list)
3. Return reward in [0.0, 1.0] range (clamped to avoid exact 0/1)

Our graders already return this format, but we clamp rewards here.
"""

from server.graders.json_grader import grade_task1 as _g1
from server.graders.yaml_grader import grade_task2 as _g2
from server.graders.dockerfile_grader import grade_task3 as _g3


def _clamp_reward(result):
    """Extract and clamp reward from grader result tuple.
    Returns the original tuple with clamped reward."""
    if isinstance(result, tuple):
        reward, error_msg, bugs_fixed = result
        # Clamp to strict (0.001, 0.999) range to avoid exact boundaries
        clamped_reward = max(0.001, min(0.999, float(reward)))
        return clamped_reward, error_msg, bugs_fixed
    # Fallback (shouldn't happen)
    return result


def grade_task1(x):
    """Task 1 (JSON) grader wrapper - returns tuple with clamped reward."""
    return _clamp_reward(_g1(x))


def grade_task2(x):
    """Task 2 (YAML) grader wrapper - returns tuple with clamped reward."""
    return _clamp_reward(_g2(x))


def grade_task3(x):
    """Task 3 (Dockerfile) grader wrapper - returns tuple with clamped reward."""
    return _clamp_reward(_g3(x))
