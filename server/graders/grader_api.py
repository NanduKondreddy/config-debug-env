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
from server.graders.compose_grader import grade_task4 as _g4
from server.graders.k8s_grader import grade_task5 as _g5
from server.graders.github_actions_grader import grade_task6 as _g6
from server.graders.nginx_grader import grade_task7 as _g7


def _extract(result):
    """Extract float reward from grader result tuple or return as-is if already float."""
    if isinstance(result, tuple):
        return float(result[0])
    return float(result)


def grade_task1(x):
    """Task 1 (JSON) grader wrapper."""
    return _extract(_g1(x))


def grade_task2(x):
    """Task 2 (YAML) grader wrapper."""
    return _extract(_g2(x))


def grade_task3(x):
    """Task 3 (Dockerfile) grader wrapper."""
    return _extract(_g3(x))


def grade_task4(x):
    """Task 4 (Docker Compose) grader wrapper."""
    return _extract(_g4(x))


def grade_task5(x):
    """Task 5 (Kubernetes) grader wrapper."""
    return _extract(_g5(x))


def grade_task6(x):
    """Task 6 (GitHub Actions) grader wrapper."""
    return _extract(_g6(x))


def grade_task7(x):
    """Task 7 (Nginx) grader wrapper."""
    return _extract(_g7(x))
