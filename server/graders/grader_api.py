"""
grader_api.py - Class-based graders for OpenEnv validator.
Validator expects classes with a grade() method returning float in (0, 1).
"""

from server.graders.json_grader import grade_task1 as _r1
from server.graders.yaml_grader import grade_task2 as _r2
from server.graders.dockerfile_grader import grade_task3 as _r3
from server.graders.compose_grader import grade_task4 as _r4
from server.graders.k8s_grader import grade_task5 as _r5
from server.graders.github_actions_grader import grade_task6 as _r6
from server.graders.nginx_grader import grade_task7 as _r7


def _safe_score(fn, env, *args, **kwargs):
    try:
        config = ""
        if env is not None and hasattr(env, 'state'):
            state = env.state
            if hasattr(state, 'last_action'):
                config = state.last_action
            elif hasattr(state, 'current_config'):
                config = state.current_config
        if not config and args:
            config = str(args[0])
        if not config:
            config = "{}"
        result = fn(config)
        if isinstance(result, (tuple, list)):
            reward = float(result[0])
        else:
            reward = float(result)
        return max(0.01, min(0.99, reward))
    except Exception:
        return 0.5


class Task1Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r1, env, *args, **kwargs)


class Task2Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r2, env, *args, **kwargs)


class Task3Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r3, env, *args, **kwargs)


class Task4Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r4, env, *args, **kwargs)


class Task5Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r5, env, *args, **kwargs)


class Task6Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r6, env, *args, **kwargs)


class Task7Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _safe_score(_r7, env, *args, **kwargs)


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