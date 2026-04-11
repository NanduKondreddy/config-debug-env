import yaml
from typing import Tuple, List


def grade_task2(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 2: Broken YAML Config (2 bugs)
    Bug 1 (Syntax): Wrong indentation on nested key (3 spaces instead of 2)
    Bug 2 (Semantic): Missing required field "version"

    Returns: (reward, error_message, bugs_fixed_list)
    """
    bugs_fixed = []
    total_bugs = 2
    error_messages = []

    # Bug 1: Check if YAML parses (syntax layer)
    try:
        config = yaml.safe_load(submitted_config)
        if isinstance(config, dict):
            bugs_fixed.append("syntax_valid_yaml")
        else:
            error_messages.append("YAML parsed but result is not a mapping/dictionary")
            reward = len(bugs_fixed) / total_bugs
            return reward, "; ".join(error_messages), bugs_fixed
    except yaml.YAMLError as e:
        error_messages.append(f"YAML parse error: {str(e)}")
        reward = len(bugs_fixed) / total_bugs
        return reward, "; ".join(error_messages), bugs_fixed

    # Bug 2: Check required field "version" exists
    service = config.get("service", config)
    if isinstance(service, dict) and "version" in service:
        bugs_fixed.append("version_field_present")
    else:
        error_messages.append(
            "Missing required field: 'version' under 'service'"
        )

    # Calculate reward
    reward = len(bugs_fixed) / total_bugs

    # Bonus for full parse
    if len(bugs_fixed) >= 1:
        reward = min(1.0, reward + 0.1)

    if len(bugs_fixed) == total_bugs:
        reward = 1.0

    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed
