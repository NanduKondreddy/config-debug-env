"""Grader API wrapper layer for dual compatibility.

Two strategies:
1. Validator may import graders directly expecting float returns
2. Runtime environment expects tuple returns

This module provides BOTH interfaces to maximize compatibility.
"""

from server.graders.json_grader import grade_task1 as _g1
from server.graders.yaml_grader import grade_task2 as _g2
from server.graders.dockerfile_grader import grade_task3 as _g3


def _extract_and_clamp_reward(result):
    """Extract and clamp reward from grader result.
    
    Returns:
        float: Clamped reward in (0.001, 0.999) range per validator spec
               (strictly between 0 and 1, not including exact boundaries)
    """
    if isinstance(result, tuple):
        reward, _, _ = result
    else:
        reward = result
    
    # Clamp to strict (0.001, 0.999) range to satisfy validator requirement
    return max(0.001, min(0.999, float(reward)))


def _tuple_from_raw(result):
    """Convert raw grader result to tuple format.
    
    Returns:
        tuple: (clamped_reward, error_msg, bugs_fixed)
    """
    if isinstance(result, tuple):
        reward, error_msg, bugs_fixed = result
        clamped_reward = _extract_and_clamp_reward((reward, None, None))
        return clamped_reward, error_msg, bugs_fixed
    else:
        # If raw is float, return with empty strings/lists
        clamped_reward = _extract_and_clamp_reward(result)
        return clamped_reward, "", []


# =============================================================================
# VALIDATOR INTERFACE: Float-only graders (for direct import/inspection)
# =============================================================================

def grade_task1_float(x):
    """Task 1 (JSON) grader - returns float only for validator compatibility."""
    result = _g1(x)
    return _extract_and_clamp_reward(result)


def grade_task2_float(x):
    """Task 2 (YAML) grader - returns float only for validator compatibility."""
    result = _g2(x)
    return _extract_and_clamp_reward(result)


def grade_task3_float(x):
    """Task 3 (Dockerfile) grader - returns float only for validator compatibility."""
    result = _g3(x)
    return _extract_and_clamp_reward(result)


# =============================================================================
# RUNTIME INTERFACE: Tuple-returning graders (for environment.py)
# =============================================================================

def grade_task1(x):
    """Task 1 (JSON) grader - returns tuple for runtime environment."""
    result = _g1(x)
    return _tuple_from_raw(result)


def grade_task2(x):
    """Task 2 (YAML) grader - returns tuple for runtime environment."""
    result = _g2(x)
    return _tuple_from_raw(result)


def grade_task3(x):
    """Task 3 (Dockerfile) grader - returns tuple for runtime environment."""
    result = _g3(x)
    return _tuple_from_raw(result)
