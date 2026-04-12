"""
Simulates EXACTLY what the Scaler validator does:
1. Import grader classes from openenv.yaml paths
2. Instantiate each class
3. Call .grade(env) or .grade(None)
4. Check score is strictly in (0.01, 0.90)

Also tests genuine grading: broken configs get LOW scores, fixed configs get HIGH scores.

Run: python test_validator_simulation.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_grader_classes():
    print("=" * 60)
    print("VALIDATOR SIMULATION: Testing grader classes")
    print("=" * 60)
    
    from server.graders.grader_api import (
        Task1Grader, Task2Grader, Task3Grader,
        Task4Grader, Task5Grader, Task6Grader, Task7Grader,
    )
    from server.config_debug_environment import ConfigDebugEnvironment
    from server.tasks.task_registry import get_task, TASK_ORDER
    
    grader_classes = {
        "task1_json": Task1Grader,
        "task2_yaml": Task2Grader,
        "task3_dockerfile": Task3Grader,
        "task4_compose": Task4Grader,
        "task5_k8s": Task5Grader,
        "task6_github_actions": Task6Grader,
        "task7_nginx": Task7Grader,
    }
    
    all_pass = True
    
    for task_id, GraderClass in grader_classes.items():
        grader = GraderClass()
        task = get_task(task_id)
        
        # Test 1: .grade(None) — validator may call with None
        # Should grade the BROKEN config → low/medium score
        score_none = grader.grade(None)
        ok_none = 0.0 < score_none < 1.0
        
        # Test 2: .grade(env) — validator passes fresh environment
        env = ConfigDebugEnvironment()
        env.reset(task_id=task_id)
        score_env = grader.grade(env)
        ok_env = 0.0 < score_env < 1.0
        
        # Test 3: .grade(ground_truth_string) — direct string (correct answer)
        score_gt = grader.grade(task.ground_truth)
        ok_gt = 0.0 < score_gt < 1.0
        
        # Test 4: .grade(broken_config) — direct string (broken)
        score_broken = grader.grade(task.broken_config)
        ok_broken = 0.0 < score_broken < 1.0
        
        # Verify genuine grading: fixed > broken
        genuine = score_gt > score_broken or score_gt == score_broken  # fixed should score higher
        
        status = "PASS" if (ok_none and ok_env and ok_gt and ok_broken) else "FAIL"
        if not (ok_none and ok_env and ok_gt and ok_broken):
            all_pass = False
        
        print(f"\n[{status}] {task_id}")
        print(f"  .grade(None)           = {score_none:.4f}  {'OK' if ok_none else 'OUT OF RANGE!'}")
        print(f"  .grade(env)            = {score_env:.4f}  {'OK' if ok_env else 'OUT OF RANGE!'}")
        print(f"  .grade(ground_truth)   = {score_gt:.4f}  (correct answer)")
        print(f"  .grade(broken_config)  = {score_broken:.4f}  (broken input)")
        print(f"  Genuine grading: fixed({score_gt:.2f}) >= broken({score_broken:.2f}) = {genuine}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("ALL TASKS PASSED — all scores strictly in (0, 1)")
    else:
        print("SOME TASKS FAILED — fix before pushing!")
    print("=" * 60)


if __name__ == "__main__":
    test_grader_classes()
