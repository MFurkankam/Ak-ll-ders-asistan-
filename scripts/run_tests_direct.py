import sys
import traceback
from pathlib import Path

# ensure repo root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_mastery import test_compute_topic_mastery  # noqa: E402
from tests.test_compute_with_attempts import test_compute_with_filtered_attempts  # noqa: E402
from tests.test_filters import test_attempt_filtering  # noqa: E402


def run_test(func):
    try:
        func()
        print(f"{func.__name__}: PASS")
    except AssertionError as e:
        print(f"{func.__name__}: FAIL - AssertionError: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"{func.__name__}: ERROR - {e}")
        traceback.print_exc()


if __name__ == '__main__':
    run_test(test_compute_topic_mastery)
    run_test(test_compute_with_filtered_attempts)
    run_test(test_attempt_filtering)
