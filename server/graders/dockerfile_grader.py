import re
from typing import Tuple, List

ALLOWED_BASE_IMAGES = [
    "python:3.9-slim", "python:3.10-slim", "python:3.11-slim",
    "python:3.9", "python:3.10", "python:3.11",
    "python:3.9-alpine", "python:3.10-alpine", "python:3.11-alpine",
    "python:3.9-slim-bullseye", "python:3.9-slim-bookworm",
    "node:18", "node:20", "node:18-slim", "node:20-slim",
    "ubuntu:22.04", "ubuntu:20.04", "debian:bullseye-slim",
]


def grade_task3(submitted_config: str) -> Tuple[float, str, List[str]]:
    """
    Grade Task 3: Broken Dockerfile (3 bugs)
    Bug 1 (Syntax): RUN command with wrong escape character (^ instead of \\)
    Bug 2 (Semantic): Wrong base image tag (python:3.9-slm instead of python:3.9-slim)
    Bug 3 (Runtime): Missing EXPOSE directive

    Returns: (reward, error_message, bugs_fixed_list)
    """
    bugs_fixed = []
    total_bugs = 3
    error_messages = []

    lines = submitted_config.strip().split("\n")

    # Bug 2: Check base image is valid
    from_lines = [l for l in lines if l.strip().upper().startswith("FROM")]
    if from_lines:
        from_image = from_lines[0].strip().split()[1] if len(from_lines[0].strip().split()) > 1 else ""
        if from_image in ALLOWED_BASE_IMAGES:
            bugs_fixed.append("valid_base_image")
        else:
            error_messages.append(
                f"Base image '{from_image}' is not a recognized valid image. "
                f"Did you mean 'python:3.9-slim'?"
            )
    else:
        error_messages.append("Missing FROM instruction in Dockerfile")

    # Bug 1: Check RUN syntax - no ^ for line continuation
    run_blocks = []
    in_run = False
    current_run = []
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("RUN "):
            in_run = True
            current_run = [line]
        elif in_run:
            if current_run[-1].rstrip().endswith("\\"):
                current_run.append(line)
            else:
                run_blocks.append("\n".join(current_run))
                in_run = False
                current_run = []
                if stripped.upper().startswith("RUN "):
                    in_run = True
                    current_run = [line]
        if not in_run and current_run:
            run_blocks.append("\n".join(current_run))
            current_run = []
    if current_run:
        run_blocks.append("\n".join(current_run))

    has_caret = any("^" in line and not line.strip().startswith("#") for line in lines)
    # Check if multi-line RUN uses proper backslash
    has_proper_continuation = any(
        line.rstrip().endswith("\\") for line in lines
        if not line.strip().startswith("#")
    )

    if not has_caret:
        bugs_fixed.append("run_syntax_correct")
    else:
        error_messages.append(
            "RUN command uses '^' for line continuation. "
            "Dockerfiles use '\\' for multi-line commands."
        )

    # Bug 3: Check EXPOSE directive present
    expose_lines = [l for l in lines if l.strip().upper().startswith("EXPOSE")]
    if expose_lines:
        bugs_fixed.append("expose_present")
    else:
        error_messages.append(
            "Missing EXPOSE directive. The application port should be exposed."
        )

    # Calculate reward
    reward = len(bugs_fixed) / total_bugs

    # Bonus for having a parseable Dockerfile structure
    has_from = any(l.strip().upper().startswith("FROM") for l in lines)
    has_cmd_or_entrypoint = any(
        l.strip().upper().startswith(("CMD", "ENTRYPOINT")) for l in lines
    )
    if has_from and has_cmd_or_entrypoint:
        reward = min(1.0, reward + 0.1)

    if len(bugs_fixed) == total_bugs:
        reward = 0.99

    # Clamp to strict (0,1) range for validator
    reward = max(0.01, min(0.99, reward))
    error_msg = "; ".join(error_messages) if error_messages else "All checks passed!"
    return reward, error_msg, bugs_fixed
