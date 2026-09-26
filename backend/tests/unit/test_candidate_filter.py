from types import SimpleNamespace

from app.services.ai.candidate_filter import evaluate_candidate


def _job(required_skills=None, experience_min=None, experience_max=None):
    return SimpleNamespace(
        required_skills=required_skills or [],
        experience_min=experience_min,
        experience_max=experience_max,
    )


def _profile(skills=None, experience_years=None):
    return SimpleNamespace(skills=skills or [], experience_years=experience_years)


def test_candidate_with_skill_overlap_passes():
    result = evaluate_candidate(_job(["python", "sql"]), _profile(["python"]))
    assert result.passed is True
    assert result.reason is None


def test_candidate_with_zero_overlap_is_filtered_out():
    result = evaluate_candidate(_job(["python", "sql"]), _profile(["java", "go"]))
    assert result.passed is False
    assert result.reason == "no_required_skill_overlap"


def test_job_with_no_required_skills_never_filters_on_skills():
    result = evaluate_candidate(_job([]), _profile(["anything"]))
    assert result.passed is True


def test_candidate_within_experience_band_passes():
    result = evaluate_candidate(
        _job(["python"], experience_min=2, experience_max=5), _profile(["python"], experience_years=3)
    )
    assert result.passed is True


def test_candidate_below_experience_band_is_filtered_out():
    result = evaluate_candidate(
        _job(["python"], experience_min=5), _profile(["python"], experience_years=1)
    )
    assert result.passed is False
    assert result.reason == "outside_experience_band"


def test_candidate_above_experience_band_is_filtered_out():
    result = evaluate_candidate(
        _job(["python"], experience_max=3), _profile(["python"], experience_years=10)
    )
    assert result.passed is False
    assert result.reason == "outside_experience_band"


def test_missing_experience_data_never_filters():
    """Missing data isn't a known mismatch — only an explicit,
    verifiable one filters a candidate out."""
    result = evaluate_candidate(
        _job(["python"], experience_min=5, experience_max=10), _profile(["python"], experience_years=None)
    )
    assert result.passed is True


def test_skill_matching_is_case_insensitive():
    result = evaluate_candidate(_job(["Python"]), _profile(["python"]))
    assert result.passed is True
