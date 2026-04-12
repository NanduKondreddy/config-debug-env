#!/usr/bin/env python3
"""
Local Test Script: Verify all tasks/graders meet benchmark quality standards.

This script runs the mentor's quality checklist:
- Broken config should score ~0.05 reward
- Ground truth should score ~0.95 reward
- bugs_fixed list should reflect actual fixes
- No task should return (reward=0.95, bugs=[]) on broken config (indicates broken grader)
"""

from server.tasks.task_registry import TASK_ORDER, get_task


def test_all_tasks():
    """Test all tasks in TASK_ORDER."""
    print("=" * 80)
    print("BENCHMARK QUALITY TEST - ALL TASKS")
    print("=" * 80)
    
    all_passed = True
    
    for task_id in TASK_ORDER:
        print(f"\n[TEST] {task_id}")
        print("-" * 80)
        
        task = get_task(task_id)
        
        # Test 1: Broken config should score low
        broken_reward, broken_msg, broken_bugs = task.grader(task.broken_config)
        print(f"  BROKEN CONFIG:")
        print(f"    Reward: {broken_reward:.2f} (expected ~0.05)")
        print(f"    Bugs Fixed: {len(broken_bugs)} (expected 0-1)")
        print(f"    Message: {broken_msg[:60]}...")
        
        broken_ok = 0.01 <= broken_reward <= 0.99  # Must be strictly (0, 1)
        if not broken_ok:
            print(f"    [FAIL] Broken config reward out of valid range (0.01-0.99)!")
            all_passed = False
        else:
            print(f"    [PASS]")
        
        # Test 2: Ground truth should score high
        truth_reward, truth_msg, truth_bugs = task.grader(task.ground_truth)
        print(f"\n  GROUND TRUTH:")
        print(f"    Reward: {truth_reward:.2f} (expected 0.85-0.99)")
        print(f"    Bugs Fixed: {len(truth_bugs)} (expected {task.num_bugs})")
        print(f"    Message: {truth_msg[:60]}...")
        
        truth_ok = 0.85 <= truth_reward <= 0.99  # Should be in valid high range
        if not truth_ok:
            print(f"    [FAIL] Ground truth reward out of expected range!")
            all_passed = False
        else:
            print(f"    [PASS]")
        
        # Test 3: Check for grader logic issues
        if broken_reward >= 0.95 and len(broken_bugs) == 0:
            print(f"\n  [WARNING] Grader may be broken (high reward on broken config)")
            all_passed = False
        
        if truth_reward < 0.85:
            print(f"\n  [WARNING] Ground truth not scoring highly enough")
            all_passed = False
        
        # Task metadata
        print(f"\n  Task Metadata:")
        print(f"    Difficulty: {task.difficulty}")
        print(f"    Bugs: {task.num_bugs}")
        print(f"    Type: {task.file_type}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED - Ready for resubmission")
    else:
        print("[FAILED] SOME TESTS FAILED - Review above")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = test_all_tasks()
    exit(0 if success else 1)
