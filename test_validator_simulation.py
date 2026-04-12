"""
Simulates EXACTLY what the Scaler validator does:
1. Import grader classes from openenv.yaml paths
2. Instantiate each class
3. Call .grade(env) or .grade(None)
4. Check score is strictly in (0.01, 0.99)

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
    
    graders = {
        "task1_json": Task1Grader(),
        "task2_yaml": Task2Grader(),
        "task3_dockerfile": Task3Grader(),
        "task4_compose": Task4Grader(),
        "task5_k8s": Task5Grader(),
        "task6_github_actions": Task6Grader(),
        "task7_nginx": Task7Grader(),
    }
    
    all_pass = True
    
    for task_id, grader in graders.items():
        # Test 1: .grade(None) — validator may call with None
        score_none = grader.grade(None)
        ok_none = 0.0 < score_none < 1.0
        
        # Test 2: .grade(env) — validator passes environment
        from server.config_debug_environment import ConfigDebugEnvironment
        env = ConfigDebugEnvironment()
        env.reset(task_id=task_id)
        score_env = grader.grade(env)
        ok_env = 0.0 < score_env < 1.0
        
        # Test 3: .grade(ground_truth_string) — direct string
        from server.tasks.task_registry import get_task
        task = get_task(task_id)
        score_gt = grader.grade(task.ground_truth)
        ok_gt = 0.0 < score_gt < 1.0
        
        status = "PASS" if (ok_none and ok_env and ok_gt) else "FAIL"
        if not (ok_none and ok_env and ok_gt):
            all_pass = False
        
        print(f"\n[{status}] {task_id}")
        print(f"  .grade(None)         = {score_none:.4f}  {'OK' if ok_none else 'OUT OF RANGE!'}")
        print(f"  .grade(env)          = {score_env:.4f}  {'OK' if ok_env else 'OUT OF RANGE!'}")
        print(f"  .grade(ground_truth) = {score_gt:.4f}  {'OK' if ok_gt else 'OUT OF RANGE!'}")
        
        # Strict check
        if score_none == 0.0 or score_none == 1.0:
            print(f"  FATAL: score is exactly {score_none} — validator rejects 0.0 and 1.0!")
            all_pass = False
        if score_env == 0.0 or score_env == 1.0:
            print(f"  FATAL: score is exactly {score_env} — validator rejects 0.0 and 1.0!")
            all_pass = False
        if score_gt == 0.0 or score_gt == 1.0:
            print(f"  FATAL: score is exactly {score_gt} — validator rejects 0.0 and 1.0!")
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("ALL TASKS PASSED — safe to push and submit!")
    else:
        print("SOME TASKS FAILED — fix before pushing!")
    print("=" * 60)


def test_docker_verification():
    """The exact Docker test command from the Meta AI email."""
    print("\n\nDOCKER VERIFICATION EQUIVALENT:")
    print("-" * 40)
    
    from server.graders.grader_api import (
        Task1Grader, Task2Grader, Task3Grader,
        Task4Grader, Task5Grader, Task6Grader, Task7Grader,
    )
    
    for name, cls in [
        ("Task1Grader", Task1Grader),
        ("Task2Grader", Task2Grader),
        ("Task3Grader", Task3Grader),
        ("Task4Grader", Task4Grader),
        ("Task5Grader", Task5Grader),
        ("Task6Grader", Task6Grader),
        ("Task7Grader", Task7Grader),
    ]:
        score = cls().grade(None)
        print(f"{name}().grade(None) = {score}")


if __name__ == "__main__":
    test_grader_classes()
    test_docker_verification()
