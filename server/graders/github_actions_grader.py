import yaml
from typing import Tuple, List

VALID_RUNNERS = [
    "ubuntu-latest", "ubuntu-22.04", "ubuntu-20.04", "ubuntu-24.04",
    "macos-latest", "macos-14", "macos-13", "macos-12",
    "windows-latest", "windows-2022", "windows-2019",
]

VALID_CHECKOUT_PARAMS = [
    "repository", "ref", "token", "ssh-key", "ssh-known-hosts", "ssh-strict",
    "persist-credentials", "path", "clean", "filter", "sparse-checkout",
    "sparse-checkout-cone-mode", "fetch-depth", "fetch-tags",
    "show-progress", "lfs", "submodules", "set-safe-directory",
]


def grade_task6(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 6: Broken GitHub Actions Workflow (5 bugs)
    Bug 1 (Syntax): Missing colon after 'on' trigger
    Bug 2 (Semantic): runs-on uses "ubuntu-latets" (typo)
    Bug 3 (Semantic): actions/checkout with invalid parameter name "fetch-deph"
    Bug 4 (Runtime): env var references secrets but not defined in env block (acceptable)
    Bug 5 (Integration): Upload artifact name "build-output" vs download "build-artifact"

    Returns: (reward, error_message, bugs_fixed_list)
    """
    bugs_fixed = []
    total_bugs = 5
    error_messages = []

    # Bug 1: Check if YAML parses (syntax layer - the missing colon after 'on')
    try:
        config = yaml.safe_load(submitted_config)
        if not isinstance(config, dict):
            error_messages.append("GitHub Actions workflow is not a valid mapping")
            return 0.05, "; ".join(error_messages), bugs_fixed
        bugs_fixed.append("syntax_valid_yaml")
    except yaml.YAMLError as e:
        error_messages.append(f"YAML parse error: {str(e)}")
        return 0.05, "; ".join(error_messages), bugs_fixed

    jobs = config.get("jobs", {})
    if not isinstance(jobs, dict):
        error_messages.append("'jobs' key is missing or not a mapping")
        reward = len(bugs_fixed) / total_bugs
        return reward, "; ".join(error_messages), bugs_fixed

    # Bug 2: Check runner names
    all_runners_valid = True
    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            continue
        runner = job_config.get("runs-on", "")
        if runner and runner not in VALID_RUNNERS:
            all_runners_valid = False
            error_messages.append(
                f"Job '{job_name}' uses runner '{runner}' which is not valid. "
                f"Did you mean 'ubuntu-latest'?"
            )
    if all_runners_valid:
        bugs_fixed.append("valid_runners")

    # Bug 3: Check checkout action parameters
    checkout_params_valid = True
    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            continue
        steps = job_config.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses", "")
            if "actions/checkout" in str(uses):
                with_params = step.get("with", {})
                if isinstance(with_params, dict):
                    for param_name in with_params.keys():
                        if param_name not in VALID_CHECKOUT_PARAMS:
                            checkout_params_valid = False
                            error_messages.append(
                                f"actions/checkout parameter '{param_name}' is invalid. "
                                f"Did you mean 'fetch-depth'?"
                            )
    if checkout_params_valid:
        bugs_fixed.append("checkout_params_valid")

    # Bug 4: Check that env vars used with secrets are defined in env block
    # This is more of a best-practice check - we'll check the env block exists on steps using secrets
    env_usage_valid = True
    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            continue
        steps = job_config.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            step_env = step.get("env", {})
            run_cmd = str(step.get("run", ""))
            # Check if run uses env vars that aren't defined
            if "${{" in run_cmd and "secrets." in run_cmd:
                if not step_env:
                    env_usage_valid = False
                    error_messages.append(
                        f"Step '{step.get('name', 'unnamed')}' references secrets "
                        f"in run command but doesn't define them in env block."
                    )
    if env_usage_valid:
        bugs_fixed.append("env_vars_defined")

    # Bug 5: Check artifact name consistency between upload and download
    upload_names = set()
    download_names = set()
    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            continue
        steps = job_config.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = str(step.get("uses", ""))
            with_params = step.get("with", {})
            if not isinstance(with_params, dict):
                continue
            if "upload-artifact" in uses:
                name = with_params.get("name", "")
                if name:
                    upload_names.add(name)
            elif "download-artifact" in uses:
                name = with_params.get("name", "")
                if name:
                    download_names.add(name)

    if download_names and upload_names:
        if download_names.issubset(upload_names):
            bugs_fixed.append("artifact_names_match")
        else:
            mismatched = download_names - upload_names
            error_messages.append(
                f"Artifact name mismatch: download references {sorted(mismatched)} "
                f"but upload defines {sorted(upload_names)}. Names must match."
            )
    elif not download_names and not upload_names:
        bugs_fixed.append("artifact_names_match")
    else:
        error_messages.append("Artifact upload/download configuration is incomplete")

    # Calculate reward
    reward = len(bugs_fixed) / total_bugs

    if len(bugs_fixed) >= 1:
        reward = min(1.0, reward + 0.1)

    if len(bugs_fixed) == total_bugs:
        reward = 0.95

    # Clamp to strict (0,1) range for validator
    reward = max(0.05, min(0.95, reward))
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed
