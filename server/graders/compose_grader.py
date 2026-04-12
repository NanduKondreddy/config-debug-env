import yaml
from typing import Tuple, List


def grade_task4(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 4: Broken docker-compose.yml (4 bugs)
    Bug 1 (Syntax): Wrong indentation on volumes key
    Bug 2 (Semantic): Service references non-existent network name
    Bug 3 (Runtime): Port mapping "8080:80" should be "8080:3000"
    Bug 4 (Integration): depends_on references "postgres" but service is defined as "db"

    Returns: (reward, error_message, bugs_fixed_list)
    """
    bugs_fixed = []
    total_bugs = 4
    error_messages = []

    # Bug 1: Check if YAML parses (syntax layer)
    try:
        config = yaml.safe_load(submitted_config)
        if not isinstance(config, dict):
            error_messages.append("docker-compose config is not a valid mapping")
            return 0.05, "; ".join(error_messages), bugs_fixed
        bugs_fixed.append("syntax_valid_yaml")
    except yaml.YAMLError as e:
        error_messages.append(f"YAML parse error: {str(e)}")
        return 0.05, "; ".join(error_messages), bugs_fixed

    services = config.get("services", {})
    if not isinstance(services, dict):
        error_messages.append("'services' key is missing or not a mapping")
        reward = len(bugs_fixed) / total_bugs
        reward = max(0.01, min(0.99, reward))  # Enforce strict bounds
        return reward, "; ".join(error_messages), bugs_fixed

    defined_service_names = set(services.keys())
    defined_networks = set(config.get("networks", {}).keys()) if isinstance(config.get("networks"), dict) else set()

    # Bug 4: Check depends_on references valid service names
    all_deps_valid = True
    for svc_name, svc_config in services.items():
        if not isinstance(svc_config, dict):
            continue
        deps = svc_config.get("depends_on", [])
        if isinstance(deps, list):
            for dep in deps:
                if dep not in defined_service_names:
                    all_deps_valid = False
                    error_messages.append(
                        f"Service '{svc_name}' depends_on '{dep}', "
                        f"but no service named '{dep}' is defined. "
                        f"Defined services: {sorted(defined_service_names)}"
                    )

    if all_deps_valid:
        bugs_fixed.append("depends_on_valid")

    # Bug 2: Check all referenced networks exist in top-level networks
    all_nets_valid = True
    for svc_name, svc_config in services.items():
        if not isinstance(svc_config, dict):
            continue
        svc_networks = svc_config.get("networks", [])
        if isinstance(svc_networks, list):
            for net in svc_networks:
                if net not in defined_networks:
                    all_nets_valid = False
                    error_messages.append(
                        f"Service '{svc_name}' references network '{net}', "
                        f"but it's not defined in top-level networks. "
                        f"Defined networks: {sorted(defined_networks)}"
                    )

    if all_nets_valid:
        bugs_fixed.append("networks_valid")

    # Bug 3: Check port mapping - web service should map to 3000
    web_svc = services.get("web", {})
    if isinstance(web_svc, dict):
        ports = web_svc.get("ports", [])
        port_correct = False
        for port_mapping in ports:
            port_str = str(port_mapping)
            # Check the container port (right side) is 3000
            if ":3000" in port_str:
                port_correct = True
                break
        if port_correct:
            bugs_fixed.append("port_mapping_correct")
        else:
            error_messages.append(
                "Web service port mapping is incorrect. "
                "The application runs on port 3000, so the container port should be 3000."
            )
    else:
        error_messages.append("Web service is missing or misconfigured")

    # Calculate reward
    reward = len(bugs_fixed) / total_bugs

    # Bonus for parsing
    if len(bugs_fixed) >= 1:
        reward = min(1.0, reward + 0.1)

    if len(bugs_fixed) == total_bugs:
        reward = 0.95

    # Clamp to strict (0,1) range for validator
    reward = max(0.01, min(0.99, reward))
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed
