"""Optional AL09 starter: compare topics, rank resources, then check metadata."""

import hashlib
from resource_support import tags_for, validate_weights, require_limit, canonical_bytes
from app_runner import run

STAGE = 1  # Nov 23: 1; Nov 24: 2; Nov 30: 3 after completing that stage.


# STAGE 1 - MONDAY, NOVEMBER 23: What do the represented topics share?
def shared_count(left, right):
    """Return the number of distinct tags shared by two collections."""
    return len(set(left) & set(right))


def jaccard(left, right):
    """Return shared-tag count divided by union size, or zero for an empty union."""
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    if not union:
        return 0
    return len(left_set & right_set) / len(union)


# STAGE 2 - TUESDAY, NOVEMBER 24: Which references fit, and why?
def weighted_similarity(tags, profile, weights):
    """Return score, matching-tag contributions and total union weight."""
    validate_weights(weights)
    tag_set = set(tags)
    profile_set = set(profile)
    union = tag_set | profile_set
    matched = tag_set & profile_set
    contributions = {tag: weights.get(tag, 1) for tag in matched}
    matched_weight = sum(contributions.values())
    union_weight = sum(weights.get(tag, 1) for tag in union)
    score = 0 if union_weight == 0 else matched_weight / union_weight
    return score, contributions, union_weight


def ranking_key(result):
    """Provide descending-score and ascending-ID ordering for an exact tie."""
    return (-result["score"], result["id"])


def rank_resources(resources, profile, weights, k):
    """Return up to k new result records after scoring and ordering all candidates."""
    require_limit(k)
    validate_weights(weights)
    profile_tags = set(profile)
    results = []
    for resource in resources:
        resource_tags = tags_for(resource)
        score, contributions, union_weight = weighted_similarity(resource_tags, profile_tags, weights)
        matched = sorted(resource_tags & profile_tags)
        results.append({
            "id": resource["id"],
            "title": resource["title"],
            "url": resource["url"],
            "score": score,
            "matched": matched,
            "contributions": contributions,
            "union_weight": union_weight,
        })
    results.sort(key=ranking_key)
    return results[:k]


# STAGE 3 - MONDAY, NOVEMBER 30: Did the represented metadata change?
# No class Thursday, November 26; continue the same project after the holiday.
def catalog_digest(resources):
    """Return a SHA-256 hexadecimal fingerprint of the declared metadata snapshot."""
    return hashlib.sha256(canonical_bytes(resources)).hexdigest()


def main():
    """Use the supplied presentation to run only the selected completed stages."""
    if STAGE == 1:
        run(1, shared_count, jaccard)
    elif STAGE == 2:
        run(2, shared_count, jaccard, rank_resources)
    else:
        run(STAGE, shared_count, jaccard, rank_resources, catalog_digest)


if __name__ == "__main__":
    main()