from app.services.ai.match_score_service import compute_skill_overlap_score


def test_full_overlap_scores_100():
    assert compute_skill_overlap_score(["python", "sql"], ["python", "sql", "docker"]) == 100.0


def test_no_overlap_scores_zero():
    assert compute_skill_overlap_score(["python", "sql"], ["java", "go"]) == 0.0


def test_partial_overlap():
    assert compute_skill_overlap_score(["python", "sql", "docker", "aws"], ["python", "sql"]) == 50.0


def test_case_insensitive_matching():
    assert compute_skill_overlap_score(["Python", "SQL"], ["python", "sql"]) == 100.0


def test_no_required_skills_scores_zero_not_error():
    assert compute_skill_overlap_score([], ["python"]) == 0.0


def test_no_candidate_skills_scores_zero():
    assert compute_skill_overlap_score(["python", "sql"], []) == 0.0
