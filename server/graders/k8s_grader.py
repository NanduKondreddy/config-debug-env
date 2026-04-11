import yaml
from typing import Tuple, List


def grade_task5(fixed_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 5: Multi-step Kubernetes Deployment YAML debugging.
    
    Bug 1: replicas = "three" (string, should be integer) → 0.4 reward
    Bug 2: containerPort = "80" (string, should be integer) → +0.3 reward
    Bug 3: cpu = "500" (missing 'm' suffix, should be "500m") → +0.3 reward
    
    Returns: (reward, error_message, bugs_fixed_list)
    """
    reward = 0.05
    errors = []
    fixed = []

    # Parse YAML
    try:
        config = yaml.safe_load(fixed_config)
    except Exception as e:
        return 0.05, f"Invalid YAML format: {str(e)}", ["yaml"]

    # --- STEP 1: replicas fix (0.0 → 0.4) ---
    try:
        replicas = config["spec"]["replicas"]
        if isinstance(replicas, int):
            reward += 0.4
            fixed.append("replicas")
        else:
            errors.append("replicas must be an integer (not string)")
    except Exception:
        errors.append("missing or invalid replicas field")

    # --- STEP 2: containerPort fix (0.4 → 0.7) ---
    try:
        port = config["spec"]["template"]["spec"]["containers"][0]["ports"][0]["containerPort"]
        if isinstance(port, int):
            reward += 0.3
            fixed.append("port")
        else:
            errors.append("containerPort must be integer (not string)")
    except Exception:
        errors.append("missing or invalid containerPort")

    # --- STEP 3: cpu resource unit fix (0.7 → 1.0) ---
    try:
        cpu = config["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"]
        if isinstance(cpu, str) and cpu.endswith("m"):
            reward += 0.3
            fixed.append("cpu")
        else:
            errors.append("cpu must be in millicores format (e.g., 500m, not plain integer)")
    except Exception:
        errors.append("missing or invalid cpu limit")

    reward = round(min(reward, 1.0), 2)

    if reward == 1.0:
        return 0.95, "Deployment config is fully valid", fixed

    # Clamp to strict (0,1) range for validator
    reward = max(0.05, min(0.95, reward))
    error_msg = " ; ".join(errors) if errors else "Configuration has issues"
    return reward, error_msg, fixed
