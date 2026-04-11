from typing import Callable, Dict, Tuple, List

from server.tasks import task1_json, task2_yaml, task3_dockerfile
from server.graders.json_grader import grade_task1
from server.graders.yaml_grader import grade_task2
from server.graders.dockerfile_grader import grade_task3


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
]

TASK_REGISTRY: Dict[str, TaskInfo] = {
    "task1_json": TaskInfo(task1_json, grade_task1),
    "task2_yaml": TaskInfo(task2_yaml, grade_task2),
    "task3_dockerfile": TaskInfo(task3_dockerfile, grade_task3),
}


def get_task(task_id: str) -> TaskInfo:
    return TASK_REGISTRY[task_id]


def get_all_task_ids() -> List[str]:
    return list(TASK_ORDER)
