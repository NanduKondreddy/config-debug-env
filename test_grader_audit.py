#!/usr/bin/env python3
"""
Runtime audit of all graders - test actual outputs without validator.
Tests what the validator will actually receive.
"""

import sys
from server.graders.grader_api import (
    grade_task1, grade_task2, grade_task3, grade_task4,
    grade_task5, grade_task6, grade_task7,
)
from server.tasks import (
    task1_json, task2_yaml, task3_dockerfile,
    task4_compose, task5_k8s, task6_github_actions, task7_nginx
)

# Test data
TESTS = [
    (1, grade_task1, task1_json.BROKEN_CONFIG, "JSON"),
    (2, grade_task2, task2_yaml.BROKEN_CONFIG, "YAML"),
    (3, grade_task3, task3_dockerfile.BROKEN_CONFIG, "Dockerfile"),
    (4, grade_task4, task4_compose.BROKEN_CONFIG, "Compose"),
    (5, grade_task5, task5_k8s.BROKEN_CONFIG, "K8s"),
    (6, grade_task6, task6_github_actions.BROKEN_CONFIG, "GitHub Actions"),
    (7, grade_task7, task7_nginx.BROKEN_CONFIG, "Nginx"),
]

print("=" * 80)
print("GRADER RUNTIME AUDIT - ALL GRADERS WITH BROKEN CONFIGS")
print("Validator Contract: All graders must return FLOAT in (0, 1) ONLY")
print("=" * 80)
print()

failures = []
all_valid = True

for task_num, grader_func, broken_config, name in TESTS:
    task_id = f"task{task_num}_{name.lower().replace(' ', '_')}"
    
    print(f"Testing Task {task_num} ({name})...")
    print(f"  Grader: {grader_func.__name__}")
    
    try:
        result = grader_func(broken_config)
        
        # Analyze output - MUST be float only
        result_type = type(result).__name__
        print(f"  Output type: {result_type}")
        
        if isinstance(result, float):
            reward = result
            is_valid = 0 < reward < 1
            
            print(f"  Value: {reward}")
            print(f"  In bounds (0, 1): {is_valid}")
            print(f"  Exactly 0.0: {reward == 0.0}")
            print(f"  Exactly 1.0: {reward == 1.0}")
            print(f"  NaN check: {reward != reward}")
            print(f"  Inf check: {abs(reward) > 1e308}")
            
            if not is_valid:
                all_valid = False
                failures.append(f"Task {task_num}: Reward {reward} NOT in (0, 1)")
                print(f"  ❌ INVALID: Reward {reward} is not in (0, 1) range")
            else:
                print(f"  ✅ Valid")
        else:
            all_valid = False
            failures.append(f"Task {task_num}: Expected FLOAT, got {result_type}")
            print(f"  ❌ INVALID: Expected float, got {result_type}")
            print(f"  Value: {result}")
    
    except Exception as e:
        all_valid = False
        failures.append(f"Task {task_num}: Exception - {type(e).__name__}: {str(e)}")
        print(f"  ❌ EXCEPTION: {type(e).__name__}: {str(e)}")
    
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"All graders valid: {all_valid}")
print(f"Total tests: {len(TESTS)}")
print(f"Passed: {len(TESTS) - len(failures)}")
print(f"Failed: {len(failures)}")

if failures:
    print("\nFailures:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
else:
    print("\n✅ All graders return valid FLOATS in (0, 1)!")
    sys.exit(0)
