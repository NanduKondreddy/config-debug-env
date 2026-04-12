import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("GRADER VERIFICATION")
    print("=" * 60)

    print("\n[TEST 1] Importing grader_api functions...")
    try:
        from server.graders.grader_api import (
            grade_task1, grade_task2, grade_task3,
            grade_task4, grade_task5, grade_task6, grade_task7,
        )
        print("  OK - All 7 graders imported")
    except ImportError as e:
        print(f"  FAIL - {e}")
        sys.exit(1)

    print("\n[TEST 2] Calling graders, checking type + range...")
    graders = [
        ("task1", grade_task1), ("task2", grade_task2),
        ("task3", grade_task3), ("task4", grade_task4),
        ("task5", grade_task5), ("task6", grade_task6),
        ("task7", grade_task7),
    ]
    all_ok = True
    for name, fn in graders:
        try:
            result = fn("{}")
            if not isinstance(result, float):
                print(f"  FAIL - {name}: returned {type(result).__name__}, need float")
                all_ok = False
            elif result <= 0.0 or result >= 1.0:
                print(f"  FAIL - {name}: score={result} NOT in (0,1)")
                all_ok = False
            else:
                print(f"  OK   - {name}: score={result}")
        except Exception as e:
            print(f"  FAIL - {name}: {e}")
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("ALL PASSED - Push and submit!")
    else:
        print("FAILED - Fix before submitting!")
    print("=" * 60)

if __name__ == "__main__":
    main()