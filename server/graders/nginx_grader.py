from typing import Tuple, List


def grade_task7(fixed_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 7: Multi-step nginx config debugging.
    
    Bug 1: Missing semicolons in listen and error_log directives → 0.3 reward
    Bug 2: Missing http:// prefix in proxy_pass directive → +0.3 reward
    Bug 3: Improper routing with missing API endpoint headers → +0.4 reward
    
    Returns: (reward, error_message, bugs_fixed_list)
    """
    reward = 0.0
    errors = []
    fixed = []

    config = fixed_config.strip()

    # --- STEP 1: Syntax checks (semicolons) ---
    if "listen 80;" in config and "error_log logs/error.log;" in config:
        reward += 0.3
        fixed.append("syntax")
    else:
        errors.append("Missing semicolon in listen or error_log directives")

    # --- STEP 2: Directive correctness (proxy_pass protocol) ---
    if "proxy_pass http://localhost:3000;" in config:
        reward += 0.3
        fixed.append("proxy_pass")
    else:
        errors.append("proxy_pass for / must include http:// protocol prefix (e.g., http://localhost:3000;)")

    # --- STEP 3: Routing logic (API endpoint with headers) ---
    if ("location /api/" in config or "location /api {" in config):
        if "proxy_set_header Host" in config and "proxy_set_header X-Real-IP" in config:
            reward += 0.4
            fixed.append("routing")
        else:
            errors.append("API routing missing required proxy headers (Host and X-Real-IP)")
    else:
        errors.append("Improper API route configuration (use 'location /api/' with headers)")

    reward = round(min(reward, 1.0), 2)

    if reward == 1.0:
        return 1.0, "Nginx config fully valid", fixed

    return reward, " ; ".join(errors), fixed
