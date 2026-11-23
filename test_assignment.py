"""Monday Stage 1 checks: shared topics and Jaccard similarity."""

from copy import deepcopy
from math import isclose

from main import jaccard, shared_count
from resource_support import tags_for


def test_shared_count():
    left = ["queues", "collections"]
    right = ["queues", "stacks"]
    assert shared_count(left, right) == 1
    assert shared_count([], []) == 0

    repeated_left = ["queues", "queues", "collections"]
    repeated_right = ["queues", "queues", "stacks"]
    assert shared_count(repeated_left, repeated_right) == 1


def test_jaccard():
    left = ["queues", "collections"]
    right = ["queues", "stacks"]
    assert isclose(jaccard(left, right), 1 / 3)
    assert jaccard([], []) == 0
    assert jaccard(["queues"], ["stacks"]) == 0


def test_stage_1_tag_boundaries():
    left = {"id": "left", "tags": ["queues", "queues", "collections"]}
    right = {"id": "right", "tags": ["queues", "queues", "stacks"]}
    missing = {"id": "missing"}
    none_tags = {"id": "none", "tags": None}

    left_before = deepcopy(left)
    right_before = deepcopy(right)

    assert tags_for(left) == {"queues", "collections"}
    assert tags_for(right) == {"queues", "stacks"}
    assert tags_for(missing) == set()
    assert tags_for(none_tags) == set()
    assert jaccard(tags_for(left), tags_for(right)) == 1 / 3
    assert jaccard(tags_for(missing), tags_for(right)) == 0

    assert left == left_before
    assert right == right_before


def main():
    test_shared_count()
    test_jaccard()
    test_stage_1_tag_boundaries()
    print("Monday Stage 1 checks passed.")


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Run tests without Python optimization (-O).")
    main()