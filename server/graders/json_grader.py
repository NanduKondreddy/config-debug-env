import json
from typing import Tuple, List


def grade_task1(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 1: Broken JSON Config (3 bugs, progressive grading)
    
    Progressive Validation:
    1. Syntax: JSON must parse validly
    2. Structure: env must be object (not array), volumes must be object
    3. Semantics: All required fields present with correct types
    
    Bugs:
    - Bug 1 (Syntax): Missing comma after app_name
    - Bug 2 (Structural): env is array instead of object with key-value pairs
    - Bug 3 (Structural): volumes is array instead of object mapping
    
    Returns: (reward, error_message, bugs_fixed_list)
    Reward is emergent from fixes, not hard-coded.
    """
    bugs_fixed = []
    error_messages = []
    reward = 0.0

    # ===== LEVEL 1: SYNTAX VALIDATION =====
    try:
        config = json.loads(submitted_config)
        bugs_fixed.append("json_syntax_valid")
        reward += 0.3
    except json.JSONDecodeError as e:
        error_messages.append(f"JSON parse error: {str(e)}")
        # Return early with syntax failure
        error_msg = "; ".join(error_messages) if error_messages else "JSON syntax error"
        return max(0.01, min(0.99, reward)), error_msg, bugs_fixed

    # ===== LEVEL 2: STRUCTURAL VALIDATION =====
    # Check env structure
    if "env" in config:
        if isinstance(config["env"], dict):
            bugs_fixed.append("env_is_object")
            reward += 0.25
        else:
            error_messages.append(
                f"Field 'env' should be object (dict), got {type(config['env']).__name__}"
            )
    else:
        error_messages.append("Missing required field: 'env'")

    # Check volumes structure
    if "volumes" in config:
        if isinstance(config["volumes"], dict):
            bugs_fixed.append("volumes_is_object")
            reward += 0.25
        else:
            error_messages.append(
                f"Field 'volumes' should be object (dict), got {type(config['volumes']).__name__}"
            )
    else:
        error_messages.append("Missing required field: 'volumes'")

    # ===== LEVEL 3: SEMANTIC VALIDATION =====
    # Only check semantics if structure is correct
    if "env_is_object" in bugs_fixed and isinstance(config.get("env"), dict):
        env = config["env"]
        required_env_keys = {"LOG_LEVEL", "DB_HOST", "PORT"}
        if required_env_keys.issubset(env.keys()):
            bugs_fixed.append("env_all_keys_present")
            reward += 0.15
        else:
            missing = required_env_keys - set(env.keys())
            error_messages.append(f"Missing env keys: {missing}")

    if "volumes_is_object" in bugs_fixed and isinstance(config.get("volumes"), dict):
        volumes = config["volumes"]
        required_vol_keys = {"data", "logs"}
        if required_vol_keys.issubset(volumes.keys()):
            bugs_fixed.append("volumes_all_keys_present")
            reward += 0.05
        else:
            missing = required_vol_keys - set(volumes.keys())
            error_messages.append(f"Missing volume keys: {missing}")

    # ===== FINAL REWARD CALCULATION =====
    # Reward is emergent from actual fixes, not hard-coded
    reward = min(0.99, reward)  # Cap at 0.99 for non-perfect
    if len(bugs_fixed) == 5:  # All bugs fixed
        reward = 0.99
    
    reward = max(0.01, min(0.99, reward))  # Enforce strict (0,1) interval
    
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed

