"""Optional AL09 test scaffold: complete focused checks as each stage is taught."""

from copy import deepcopy
from math import isclose
from main import shared_count, jaccard, weighted_similarity, rank_resources, catalog_digest
from resource_data import RESOURCES, PROFILE, WEIGHTS, LIMITATION_ID
from resource_support import tags_for
from resource_display import same_recommendations

TEST_STAGE = 1  # Nov 23: 1; Nov 24: 2; Nov 30: 3 after adding those checks.


def test_small_comparison():
    """Completed example: predict overlap and union independently of the code."""
    left = ["queues", "collections"]
    right = ["queues", "stacks"]
    assert shared_count(left, right) == 1
    assert isclose(jaccard(left, right), 1 / 3)


def test_stage_1_boundaries():
    """Check repeated, missing, nonmatching and empty tags without changing inputs."""
    left = {"id": "left", "tags": ["queues", "queues", "collections"]}
    right = {"id": "right", "tags": ["queues", "queues", "stacks"]}
    missing = {"id": "missing"}
    none_tags = {"id": "none", "tags": None}

    left_before = deepcopy(left)
    right_before = deepcopy(right)

    left_tags = tags_for(left)
    right_tags = tags_for(right)
    equal = {tag: 1 for tag in WEIGHTS}

    equal_top = rank_resources(RESOURCES, PROFILE, equal, 2)
    assert [record["id"] for record in equal_top] == ["LR013", "LR002"]

    queue_weights = dict(equal)
    queue_weights["queues"] = 4
    queue_top = rank_resources(RESOURCES, PROFILE, queue_weights, 2)
    assert [record["id"] for record in queue_top] == ["LR013", "LR003"]

    lr003 = next(record for record in queue_top if record["id"] == "LR003")
    assert isclose(lr003["score"], 4 / 6)
    assert lr003["contributions"].get("queues") == 4

    equal_three = rank_resources(RESOURCES, PROFILE, equal, 3)
    assert [record["id"] for record in equal_three][:2] == ["LR013", "LR002"]

    reversed_catalog = list(reversed(deepcopy(RESOURCES)))
    reversed_top = rank_resources(reversed_catalog, PROFILE, equal, 2)
    assert [record["id"] for record in reversed_top] == ["LR013", "LR002"]

    all_one_top = rank_resources(RESOURCES, PROFILE, {tag: 1 for tag in WEIGHTS}, len(RESOURCES))
    for record in all_one_top:
        resource = next(item for item in RESOURCES if item["id"] == record["id"])
        expected = jaccard(tags_for(resource), tags_for(PROFILE))
        assert isclose(record["score"], expected)
    profile_tags = tags_for(PROFILE)
    assert jaccard(tags_for(missing), profile_tags) == 0
    assert jaccard(tags_for(none_tags), profile_tags) == 0

    assert left == left_before
    assert right == right_before
    assert tags_for(left) == left_tags
    assert tags_for(right) == right_tags


def test_stage_2_rankings():
    """Check independent scores, the exact cutoff tie and changed preferences."""
    equal = {tag: 1 for tag in WEIGHTS}

    equal_top = rank_resources(RESOURCES, PROFILE, equal, 2)
    assert [record["id"] for record in equal_top] == ["LR013", "LR002"]

    queue_weights = dict(equal)
    queue_weights["queues"] = 4
    queue_top = rank_resources(RESOURCES, PROFILE, queue_weights, 2)
    assert [record["id"] for record in queue_top] == ["LR013", "LR003"]

    lr003 = next(record for record in queue_top if record["id"] == "LR003")
    assert isclose(lr003["score"], 4 / 6)
    assert lr003["matched"] == ["queues"]
    assert lr003["contributions"].get("queues") == 4
    assert lr003["union_weight"] == 6

    equal_three = rank_resources(RESOURCES, PROFILE, equal, 3)
    assert [record["id"] for record in equal_three][:3] == ["LR013", "LR002", "LR003"]

    reversed_catalog = list(reversed(deepcopy(RESOURCES)))
    reversed_top = rank_resources(reversed_catalog, PROFILE, equal, 2)
    assert [record["id"] for record in reversed_top] == ["LR013", "LR002"]

    all_one_top = rank_resources(RESOURCES, PROFILE, {}, len(RESOURCES))
    for record in all_one_top:
        resource = next(item for item in RESOURCES if item["id"] == record["id"])
        expected = jaccard(tags_for(resource), tags_for(PROFILE))
        assert isclose(record["score"], expected)


def test_stage_2_boundaries():
    """Check limits, tag policies, zero weight and independent result records."""
    resources_before = deepcopy(RESOURCES)
    profile_before = deepcopy(PROFILE)
    weights_before = deepcopy(WEIGHTS)

    assert rank_resources(RESOURCES, PROFILE, WEIGHTS, 0) == []
    assert rank_resources([], PROFILE, WEIGHTS, 2) == []
    assert len(rank_resources(RESOURCES, PROFILE, WEIGHTS, len(RESOURCES) + 10)) == len(RESOURCES)

    missing = {"id": "missing"}
    none_tags = {"id": "none", "tags": None}
    repeated = {"id": "repeated", "tags": ["queues", "queues", "stacks"]}
    assert tags_for(missing) == set()
    assert tags_for(none_tags) == set()
    assert tags_for(repeated) == {"queues", "stacks"}

    assert weighted_similarity(set(), set(), {}) == (0, {}, 0)
    assert weighted_similarity({"queues"}, {"queues"}, {"queues": 0})[0] == 0

    top = rank_resources(RESOURCES, PROFILE, WEIGHTS, 2)
    required_fields = {"id", "title", "url", "score", "matched", "contributions", "union_weight"}
    for record in top:
        assert set(record) == required_fields
    top[0]["title"] = "Changed result"
    top[0]["matched"].append("changed")
    top[0]["contributions"]["changed"] = 99

    assert RESOURCES == resources_before
    assert PROFILE == profile_before
    assert WEIGHTS == weights_before


def test_stage_3_controlled_changes():
    """Check separate missing-tag and title-only edits against independent expectations."""
    original = deepcopy(RESOURCES)
    original_top = rank_resources(original, PROFILE, {}, 2)

    missing = deepcopy(RESOURCES)
    for resource in missing:
        if resource["id"] == LIMITATION_ID:
            resource["tags"] = []
    missing_top = rank_resources(missing, PROFILE, {}, 2)
    assert [record["id"] for record in missing_top] == ["LR002", "LR003"]
    assert RESOURCES == original
    assert [record["id"] for record in rank_resources(RESOURCES, PROFILE, {}, 2)] == [
        record["id"] for record in original_top
    ]

    renamed = deepcopy(RESOURCES)
    for resource in renamed:
        if resource["id"] == LIMITATION_ID:
            resource["title"] += " (display title edited)"
    renamed_ranking = rank_resources(renamed, PROFILE, {}, 2)
    assert same_recommendations(original_top, renamed_ranking)
    assert catalog_digest(RESOURCES) != catalog_digest(renamed)

    reordered = deepcopy(RESOURCES)
    reordered.reverse()
    for resource in reordered:
        if "tags" in resource and resource["tags"] is not None:
            resource["tags"].reverse()
    assert catalog_digest(RESOURCES) == catalog_digest(reordered)


def main():
    """Run only the checks completed for the selected instructional stage."""
    if TEST_STAGE not in (1, 2, 3):
        raise ValueError("TEST_STAGE must be 1, 2, or 3")
    test_small_comparison()
    test_stage_1_boundaries()
    if TEST_STAGE >= 2:
        test_stage_2_rankings()
        test_stage_2_boundaries()
    if TEST_STAGE >= 3:
        test_stage_3_controlled_changes()
    print("Selected-stage checks passed; complete all three stages before submission.")


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Run tests without Python optimization (-O).")
    main()