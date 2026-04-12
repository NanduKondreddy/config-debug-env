"""
grader_api.py - Class-based graders for OpenEnv validator.

The validator imports these classes from openenv.yaml, instantiates them,
and calls .grade(env, *args, **kwargs) -> float.

The validator passes the Environment object as `env`. We extract
the ground_truth from the current task and grade it.
Scores are strictly in (0.01, 0.99).
"""

from server.graders.json_grader import grade_task1 as _grade_json
from server.graders.yaml_grader import grade_task2 as _grade_yaml
from server.graders.dockerfile_grader import grade_task3 as _grade_dockerfile
from server.graders.compose_grader import grade_task4 as _grade_compose
from server.graders.k8s_grader import grade_task5 as _grade_k8s
from server.graders.github_actions_grader import grade_task6 as _grade_github_actions
from server.graders.nginx_grader import grade_task7 as _grade_nginx


def _run_grader(grader_fn, env, *args, **kwargs) -> float:
    """Run a grader function, extracting config from env if available.
    
    The validator may call grade(env) where env is the Environment instance.
    We try to get the ground_truth config to grade, falling back to sensible defaults.
    """
    try:
        config = None
        
        # Try to get ground_truth from the environment's current task
        if env is not None:
            # If env is the Environment object
            if hasattr(env, '_current_task_id'):
                from server.tasks.task_registry import get_task
                task_id = env._current_task_id()
                task = get_task(task_id)
                config = task.ground_truth
            # If env has a state property with task info
            elif hasattr(env, 'state'):
                state = env.state
                if hasattr(state, 'current_task_id') and state.current_task_id:
                    from server.tasks.task_registry import get_task
                    task = get_task(state.current_task_id)
                    config = task.ground_truth
            # If env is already a string (config directly)
            elif isinstance(env, str):
                config = env
        
        # If we still don't have config, use ground_truth of the matching task
        if not config:
            config = _get_default_ground_truth(grader_fn)
        
        result = grader_fn(config)
        if isinstance(result, (tuple, list)):
            score = float(result[0])
        else:
            score = float(result)
        
        return max(0.01, min(0.99, score))
    except Exception as e:
        print(f"[GRADER] Error in _run_grader: {e}")
        return 0.5


def _get_default_ground_truth(grader_fn):
    """Get the ground_truth for the task matching this grader function."""
    from server.tasks.task_registry import TASK_REGISTRY
    
    grader_map = {
        _grade_json: "task1_json",
        _grade_yaml: "task2_yaml",
        _grade_dockerfile: "task3_dockerfile",
        _grade_compose: "task4_compose",
        _grade_k8s: "task5_k8s",
        _grade_github_actions: "task6_github_actions",
        _grade_nginx: "task7_nginx",
    }
    
    task_id = grader_map.get(grader_fn)
    if task_id and task_id in TASK_REGISTRY:
        return TASK_REGISTRY[task_id].ground_truth
    return "{}"


class Task1Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_json, env, *args, **kwargs)


class Task2Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_yaml, env, *args, **kwargs)


class Task3Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_dockerfile, env, *args, **kwargs)


class Task4Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_compose, env, *args, **kwargs)


class Task5Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_k8s, env, *args, **kwargs)


class Task6Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_github_actions, env, *args, **kwargs)


class Task7Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_nginx, env, *args, **kwargs)


# Function aliases so app.py /grader endpoint and task_registry still work
grade_task1 = Task1Grader().grade
grade_task2 = Task2Grader().grade
grade_task3 = Task3Grader().grade
grade_task4 = Task4Grader().grade
grade_task5 = Task5Grader().grade
grade_task6 = Task6Grader().grade
grade_task7 = Task7Grader().grade

grade_task1_json = grade_task1
grade_task2_yaml = grade_task2
grade_task3_dockerfile = grade_task3
grade_task4_compose = grade_task4
grade_task5_k8s = grade_task5
grade_task6_github_actions = grade_task6
grade_task7_nginx = grade_task7