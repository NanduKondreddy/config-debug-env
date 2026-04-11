from typing import Callable, Dict, List, Tuple, Union

from server.tasks import task1_json, task2_yaml, task3_dockerfile
from server.graders.grader_api import grade_task1_float, grade_task2_float, grade_task3_float


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
        # Grader returns float (for validator compatibility)
        # Environment will handle conversion to tuple format if needed
        self.grader: Callable[[str], float] = grader_func


TASK_ORDER = [
    "task1_json",
    "task2_yaml",
    "task3_dockerfile",
]

TASK_REGISTRY: Dict[str, TaskInfo] = {
    "task1_json": TaskInfo(task1_json, grade_task1_float),
    "task2_yaml": TaskInfo(task2_yaml, grade_task2_float),
    "task3_dockerfile": TaskInfo(task3_dockerfile, grade_task3_float),
}


def get_task(task_id: str) -> TaskInfo:
    return TASK_REGISTRY[task_id]


def get_all_task_ids() -> List[str]:
    return list(TASK_ORDER)
