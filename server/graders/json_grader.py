import json
from typing import Tuple, List


def grade_task1(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 1: Broken JSON Config (2 bugs)
    Bug 1 (Syntax): Missing comma between key-value pairs
    Bug 2 (Semantic): Wrong data type for "port" field (string instead of int)

    Returns: (reward, error_message, bugs_fixed_list)
    """
    bugs_fixed = []
    total_bugs = 2
    error_messages = []

    # Bug 1: Check if JSON parses (syntax layer)
    try:
        config = json.loads(submitted_config)
        bugs_fixed.append("syntax_valid_json")
    except json.JSONDecodeError as e:
        error_messages.append(f"JSON parse error: {str(e)}")
        reward = len(bugs_fixed) / total_bugs
        return reward, "; ".join(error_messages), bugs_fixed

    # Bug 2: Check port is integer (semantic layer)
    if "port" in config:
        if isinstance(config["port"], int):
            bugs_fixed.append("port_is_integer")
        else:
            error_messages.append(
                f"Field 'port' should be integer, got {type(config['port']).__name__}"
            )
    else:
        error_messages.append("Missing required field: 'port'")

    # Calculate reward
    reward = len(bugs_fixed) / total_bugs

    # Bonus for full parse
    if len(bugs_fixed) >= 1:
        reward = min(1.0, reward + 0.1)

    if len(bugs_fixed) == total_bugs:
        reward = 0.95

    # Clamp to strict (0,1) range for validator
    reward = max(0.05, min(0.95, reward))
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed
