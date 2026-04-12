import yaml
from typing import Tuple, List


def grade_task2(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 2: Broken YAML Config (3 bugs, progressive grading)
    
    Progressive Validation:
    1. Syntax: YAML must parse validly
    2. Structure: env must be object (not array)
    3. Semantics: All jobs must have 'timeout' field
    
    Bugs:
    - Bug 1 (Syntax): Wrong indentation (3 spaces instead of 2)
    - Bug 2 (Structural): env is array instead of object
    - Bug 3 (Semantic): Missing 'timeout' field in jobs
    
    Returns: (reward, error_message, bugs_fixed_list)
    Reward is emergent from fixes, not hard-coded.
    """
    bugs_fixed = []
    error_messages = []
    reward = 0.0

    # ===== LEVEL 1: SYNTAX VALIDATION =====
    try:
        config = yaml.safe_load(submitted_config)
        if isinstance(config, dict):
            bugs_fixed.append("yaml_syntax_valid")
            reward += 0.3
        else:
            error_messages.append("YAML parsed but result is not a mapping/dictionary")
            return max(0.01, min(0.90, reward)), "; ".join(error_messages), bugs_fixed
    except yaml.YAMLError as e:
        error_messages.append(f"YAML parse error: {str(e)}")
        return max(0.01, min(0.90, reward)), "; ".join(error_messages), bugs_fixed

    # ===== LEVEL 2: STRUCTURAL VALIDATION =====
    # Check env structure
    pipeline = config.get("pipeline", config)
    if isinstance(pipeline, dict):
        if "env" in pipeline:
            env = pipeline["env"]
            if isinstance(env, dict):
                bugs_fixed.append("env_is_object")
                reward += 0.35
            else:
                error_messages.append(
                    f"Field 'env' should be object (dict), got {type(env).__name__}"
                )
        else:
            error_messages.append("Missing required field: 'env'")

    # ===== LEVEL 3: SEMANTIC VALIDATION =====
    # Check jobs have timeout fields (only if we can parse jobs)
    if "yaml_syntax_valid" in bugs_fixed:
        jobs = pipeline.get("jobs", {})
        if isinstance(jobs, dict) and len(jobs) > 0:
            all_jobs_have_timeout = all(
                isinstance(job, dict) and "timeout" in job
                for job in jobs.values()
            )
            if all_jobs_have_timeout:
                bugs_fixed.append("all_jobs_have_timeout")
                reward += 0.35
            else:
                jobs_without_timeout = [
                    name for name, job in jobs.items()
                    if not (isinstance(job, dict) and "timeout" in job)
                ]
                error_messages.append(
                    f"Jobs missing 'timeout' field: {', '.join(jobs_without_timeout)}"
                )
        else:
            error_messages.append("No valid jobs found or jobs is not an object")

    # ===== FINAL REWARD CALCULATION =====
    reward = max(0.01, min(0.90, reward))
    
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed

