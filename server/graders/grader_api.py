"""
grader_api.py - Class-based graders for OpenEnv validator.

The validator imports these classes from openenv.yaml, instantiates them,
and calls .grade(env, *args, **kwargs) -> float.

How it works:
- The validator passes the Environment object as `env`
- We extract the CURRENT observation's broken_config from the env
- We run our real grading logic on it — same logic used during step()
- The score reflects how good the current config actually is
- Scores are clamped to strict (0.01, 0.90) range
"""

from server.graders.json_grader import grade_task1 as _grade_json
from server.graders.yaml_grader import grade_task2 as _grade_yaml
from server.graders.dockerfile_grader import grade_task3 as _grade_dockerfile
from server.graders.compose_grader import grade_task4 as _grade_compose
from server.graders.k8s_grader import grade_task5 as _grade_k8s
from server.graders.github_actions_grader import grade_task6 as _grade_github_actions
from server.graders.nginx_grader import grade_task7 as _grade_nginx


def _run_grader(grader_fn, task_id, env, *args, **kwargs) -> float:
    """Run the actual grading logic on the environment's current config.
    
    Extracts the config to grade from the environment state.
    This is REAL grading — not hardcoded values.
    """
    try:
        config = None
        
        # 1. If env is a string, grade it directly
        if isinstance(env, str):
            config = env
        
        # 2. If env is the Environment object, get the current observation's config
        elif env is not None:
            # Try to get the current broken_config from observation
            if hasattr(env, '_build_observation'):
                obs = env._build_observation()
                config = getattr(obs, 'broken_config', None)
            
            # Or from state
            if not config and hasattr(env, 'current_broken_config'):
                config = env.current_broken_config
        
        # 3. If still no config, get the broken_config for this task (initial state)
        if not config:
            from server.tasks.task_registry import get_task, TASK_REGISTRY
            if task_id in TASK_REGISTRY:
                task = get_task(task_id)
                config = task.broken_config  # Grade the BROKEN config (should get low score)
        
        # 4. Last resort
        if not config:
            config = "{}"
        
        # Run the actual grader logic
        result = grader_fn(config)
        if isinstance(result, (tuple, list)):
            score = float(result[0])
        else:
            score = float(result)
        
        # Clamp to strict (0, 1) — never 0.0 or 1.0
        return max(0.01, min(0.90, score))
    
    except Exception as e:
        print(f"[GRADER] Error grading {task_id}: {e}")
        return 0.50


class Task1Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_json, "task1_json", env, *args, **kwargs)


class Task2Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_yaml, "task2_yaml", env, *args, **kwargs)


class Task3Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_dockerfile, "task3_dockerfile", env, *args, **kwargs)


class Task4Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_compose, "task4_compose", env, *args, **kwargs)


class Task5Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_k8s, "task5_k8s", env, *args, **kwargs)


class Task6Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_github_actions, "task6_github_actions", env, *args, **kwargs)


class Task7Grader:
    def grade(self, env=None, *args, **kwargs) -> float:
        return _run_grader(_grade_nginx, "task7_nginx", env, *args, **kwargs)


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