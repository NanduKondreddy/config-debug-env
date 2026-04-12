from typing import Tuple, List


def grade_task7(fixed_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 7: Nginx reverse proxy config (3 bugs, progressive grading).
    
    Progressive Validation:
    1. Syntax: All directives must end with semicolons
    2. Protocol: proxy_pass directives must include http:// prefix
    3. Routing: API endpoint must have proper headers and path
    
    Bugs:
    - Bug 1 (Syntax): Missing semicolons in listen, error_log, proxy_pass directives
    - Bug 2 (Protocol): proxy_pass for / missing http:// prefix
    - Bug 3 (Routing): API endpoint path or headers incomplete
    
    Returns: (reward, error_message, bugs_fixed_list)
    Reward is emergent from fixes.
    """
    bugs_fixed = []
    errors = []
    reward = 0.05

    config = fixed_config.strip()

    # ===== LEVEL 1: SYNTAX VALIDATION (Semicolons) =====
    required_lines_with_semicolons = [
        "listen 80;",
        "error_log logs/error.log;",
    ]
    
    # Check main location / proxy_pass has both http:// AND semicolon
    has_main_proxy_correct = (
        "proxy_pass http://localhost:3000;" in config
    )
    
    syntax_checks = [
        ("listen 80;" in config, "Missing semicolon after 'listen 80'"),
        ("error_log logs/error.log;" in config, "Missing semicolon after 'error_log'"),
        (has_main_proxy_correct, "proxy_pass for '/' missing http:// or semicolon"),
    ]
    
    syntax_passed = all(check[0] for check in syntax_checks)
    
    if syntax_passed:
        bugs_fixed.append("syntax_semicolons_valid")
        reward += 0.35
    else:
        for check, error in syntax_checks:
            if not check:
                errors.append(error)

    # ===== LEVEL 2: PROTOCOL VALIDATION =====
    # Only proceed if syntax is mostly fixed
    if "syntax_semicolons_valid" in bugs_fixed:
        # Main location must use http://
        if "location / {" in config:
            if "proxy_pass http://localhost:3000;" in config:
                bugs_fixed.append("protocol_valid")
                reward += 0.30
            else:
                errors.append("location / requires 'proxy_pass http://localhost:3000;'")
        else:
            errors.append("Missing or malformed 'location /' directive")

    # ===== LEVEL 3: ROUTING LOGIC VALIDATION =====
    # Check API endpoint routing
    if "syntax_semicolons_valid" in bugs_fixed:
        api_check = (
            ("location /api/" in config or "location /api {" in config) and
            "proxy_set_header Host $host;" in config and
            "proxy_set_header X-Real-IP $remote_addr;" in config
        )
        
        if api_check:
            bugs_fixed.append("routing_headers_valid")
            reward += 0.30
        else:
            errors.append(
                "API route missing proper headers or path. "
                "Required: 'location /api/', 'proxy_set_header Host $host;', 'proxy_set_header X-Real-IP $remote_addr;'"
            )

    # ===== FINAL REWARD CALCULATION =====
    reward = min(0.99, reward)
    if len(bugs_fixed) == 3:  # All bugs fixed
        reward = 0.99
    
    reward = max(0.01, min(0.99, reward))
    
    error_msg = " ; ".join(errors) if errors else "All checks passed!"
    return reward, error_msg, bugs_fixed

