from typing import Callable, Dict, Tuple, List

from server.tasks import task1_json, task2_yaml, task3_dockerfile
from server.tasks import task4_compose, task5_k8s, task6_github_actions, task7_nginx

# INTERNAL USE: Import directly from raw grader files (return tuples)
# grader_api.py is separate and returns float-only (for openenv.yaml validator)
from server.graders.json_grader import grade_task1
from server.graders.yaml_grader import grade_task2
from server.graders.dockerfile_grader import grade_task3
from server.graders.compose_grader import grade_task4
from server.graders.k8s_grader import grade_task5
from server.graders.github_actions_grader import grade_task6
from server.graders.nginx_grader import grade_task7


def _clamp_grader(fn):
    """Wrap raw grader to clamp reward to (0.01, 0.90) while preserving tuple return."""
    def wrapper(submitted_config: str) -> Tuple[float, str, List[str]]:
        reward, error_msg, bugs_fixed = fn(submitted_config)
        reward = max(0.01, min(0.90, float(reward)))
        return reward, error_msg, bugs_fixed
    wrapper.__name__ = fn.__name__
    wrapper.__qualname__ = fn.__qualname__
    return wrapper


class TaskInfo:
    def __init__(self, module, grader_func: Callable):
        self.task_id: str = module.TASK_ID
        self.difficulty: str = module.DIFFICULTY
        self.file_type: str = module.FILE_TYPE
        self.num_bugs: int = module.NUM_BUGS
        self.description: str = module.DESCRIPTION
        self.broken_config: str = module.BROKEN_CONFIG
        self.error_message: str = module.ERROR_MESSAGE
        self.ground_truth: str = module.GROUND_TRUTH
        self.grader: Callable[[str], Tuple[float, str, List[str]]] = grader_func


TASK_ORDER = [
    "task1_json",
    "task2_yaml",
    "task3_dockerfile",
    "task4_compose",
    "task5_k8s",
    "task6_github_actions",
    "task7_nginx",
]

TASK_REGISTRY: Dict[str, TaskInfo] = {
    "task1_json": TaskInfo(task1_json, _clamp_grader(grade_task1)),
    "task2_yaml": TaskInfo(task2_yaml, _clamp_grader(grade_task2)),
    "task3_dockerfile": TaskInfo(task3_dockerfile, _clamp_grader(grade_task3)),
    "task4_compose": TaskInfo(task4_compose, _clamp_grader(grade_task4)),
    "task5_k8s": TaskInfo(task5_k8s, _clamp_grader(grade_task5)),
    "task6_github_actions": TaskInfo(task6_github_actions, _clamp_grader(grade_task6)),
    "task7_nginx": TaskInfo(task7_nginx, _clamp_grader(grade_task7)),
}


def get_task(task_id: str) -> TaskInfo:
    return TASK_REGISTRY[task_id]


def get_all_task_ids() -> List[str]:
    return list(TASK_ORDER)