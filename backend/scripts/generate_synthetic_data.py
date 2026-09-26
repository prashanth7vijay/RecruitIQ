"""
Synthetic data generator for the Phase 2 database benchmark.

Not committed to git as generated data (there is none to commit — this
only writes to whatever Postgres DATABASE_URL points at). Re-run it
any time you want a fresh dataset at a different scale:

    python scripts/generate_synthetic_data.py --candidates 100000
    python scripts/generate_synthetic_data.py --candidates 10000 --reset

Shape is a funnel, not uniform random tables — a real recruiting
org's data looks like this too: far more candidates than interviews,
far more interviews than offers.

    candidates / profiles  : --candidates (default 100,000), 1:1
    jobs                    : 100, across 6 departments
    applications            : 1 per candidate, against a random job
    application_stage_history: ~40% of applications have 1-3 moves
    interviews               : ~5% of applications
    offers                   : ~3% of applications
    audit_logs                : ~10,000, spread across entity types

Uses bulk INSERT (SQLAlchemy Core, batched) rather than one-row-at-a-
time ORM object creation — at 100K+ rows the difference is roughly an
order of magnitude in wall-clock time, and this script's own runtime
isn't the thing being benchmarked.
"""

import argparse
import os
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

BATCH_SIZE = 5000

SKILL_POOL = [
    ["python", "sql"], ["python", "sql", "docker"], ["python", "sql", "docker", "aws"],
    ["java", "spring"], ["javascript", "react"], ["javascript", "react", "node"],
    ["go", "kubernetes"], ["ruby", "rails"], ["sql", "docker"], ["python", "aws"],
]
FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Priya", "Wei", "Fatima"]
JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Backend Engineer", "Frontend Engineer",
    "Data Analyst", "Product Manager", "DevOps Engineer", "QA Engineer", "Engineering Manager",
]


def _now():
    return datetime.now(timezone.utc)


def _rand_past(days_back):
    return _now() - timedelta(days=random.uniform(0, days_back), hours=random.uniform(0, 24))


def _batched_insert(table, rows, label):
    total = len(rows)
    for i in range(0, total, BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        db.session.execute(table.insert(), chunk)
        db.session.commit()
        print(f"  {label}: {min(i + BATCH_SIZE, total)}/{total}", end="\r")
    print(f"  {label}: {total}/{total} done")


def generate(candidate_count: int, reset: bool, slug: str = "bench-100k", name: str = "Benchmark 100K Co"):
    from app.models.company import Company
    from app.models.role import Role
    from app.models.user import User
    from app.models.department import Department
    from app.models.pipeline import PipelineTemplate, PipelineStage
    from app.models.job import Job
    from app.models.candidate import Candidate, CandidateProfile
    from app.models.application import Application, ApplicationStageHistory
    from app.models.interview import Interview
    from app.models.offer import Offer
    from app.models.audit_log import AuditLog
    from app.services.auth_service import _hash_password

    existing = db.session.query(Company).filter_by(slug=slug).first()
    if existing is not None:
        if not reset:
            print(f"Company '{slug}' already exists (id={existing.id}). Pass --reset to wipe and regenerate.")
            return existing.id
        print("Deleting existing benchmark data...")
        company_id = existing.id
        db.session.execute(AuditLog.__table__.delete().where(AuditLog.company_id == company_id))
        db.session.execute(Interview.__table__.delete().where(Interview.company_id == company_id))
        db.session.execute(Offer.__table__.delete().where(Offer.company_id == company_id))
        app_ids_subq = db.session.query(Application.id).filter(Application.company_id == company_id).subquery()
        db.session.execute(
            ApplicationStageHistory.__table__.delete().where(
                ApplicationStageHistory.application_id.in_(db.session.query(app_ids_subq.c.id))
            )
        )
        db.session.execute(Application.__table__.delete().where(Application.company_id == company_id))
        db.session.execute(CandidateProfile.__table__.delete().where(CandidateProfile.company_id == company_id))
        db.session.execute(Job.__table__.delete().where(Job.company_id == company_id))
        db.session.execute(
            PipelineStage.__table__.delete().where(
                PipelineStage.pipeline_template_id.in_(
                    db.session.query(PipelineTemplate.id).filter(PipelineTemplate.company_id == company_id)
                )
            )
        )
        db.session.execute(PipelineTemplate.__table__.delete().where(PipelineTemplate.company_id == company_id))
        db.session.execute(Department.__table__.delete().where(Department.company_id == company_id))
        db.session.commit()

    company = db.session.query(Company).filter_by(slug=slug).first()
    if company is None:
        company = Company(name=name, slug=slug)
        db.session.add(company)
        db.session.commit()
    company_id = company.id

    role = db.session.query(Role).filter_by(company_id=company_id, name="bench-role").first()
    if role is None:
        role = Role(company_id=company_id, name="bench-role")
        db.session.add(role)
        db.session.commit()

    user = db.session.query(User).filter_by(company_id=company_id, email="bench@example.com").first()
    if user is None:
        user = User(
            company_id=company_id, role_id=role.id, email="bench@example.com",
            password_hash=_hash_password("not-used"), first_name="Bench", last_name="User", status="active",
        )
        db.session.add(user)
        db.session.commit()

    print(f"Company: {company.slug} ({company_id})")

    # --- departments ---
    dept_rows = [{"id": uuid.uuid4(), "company_id": company_id, "name": f"Dept {i}"} for i in range(6)]
    db.session.execute(Department.__table__.insert(), dept_rows)
    db.session.commit()
    dept_ids = [d["id"] for d in dept_rows]

    # --- pipeline templates + stages (one shared template, reused by every job) ---
    template_id = uuid.uuid4()
    db.session.execute(
        PipelineTemplate.__table__.insert(),
        [{"id": template_id, "company_id": company_id, "name": "Standard", "is_default": True}],
    )
    stage_defs = [
        ("Applied", 0, "screening"), ("Phone Screen", 1, "screening"), ("Interview", 2, "interview"),
        ("Offer", 3, "offer"), ("Hired", 4, "terminal"),
    ]
    stage_rows = [
        {"id": uuid.uuid4(), "pipeline_template_id": template_id, "name": n, "stage_order": o, "stage_type": t}
        for n, o, t in stage_defs
    ]
    db.session.execute(PipelineStage.__table__.insert(), stage_rows)
    db.session.commit()
    stage_ids = [s["id"] for s in stage_rows]
    screening_stage_id = stage_ids[0]

    # --- jobs ---
    job_count = 100
    job_rows = [
        {
            "id": uuid.uuid4(), "company_id": company_id, "title": random.choice(JOB_TITLES),
            "department_id": random.choice(dept_ids), "pipeline_template_id": template_id,
            "required_skills": random.choice(SKILL_POOL), "status": random.choice(["published", "published", "closed"]),
            "created_by": user.id, "updated_at": _rand_past(60),
        }
        for _ in range(job_count)
    ]
    db.session.execute(Job.__table__.insert(), job_rows)
    db.session.commit()
    job_ids = [j["id"] for j in job_rows]
    print(f"  jobs: {job_count}/{job_count} done")

    # --- candidates + profiles ---
    t0 = time.monotonic()
    candidate_rows, profile_rows = [], []
    for i in range(candidate_count):
        cid = uuid.uuid4()
        candidate_rows.append(
            {
                "id": cid, "email": f"bench-{i}-{uuid.uuid4().hex[:10]}@example.com",
                "first_name": random.choice(FIRST_NAMES), "last_name": f"Candidate{i}",
            }
        )
        profile_rows.append(
            {
                "id": uuid.uuid4(), "company_id": company_id, "candidate_id": cid,
                "skills": random.choice(SKILL_POOL), "experience_years": random.randint(0, 15),
            }
        )
    _batched_insert(Candidate.__table__, candidate_rows, "candidates")
    _batched_insert(CandidateProfile.__table__, profile_rows, "candidate_profiles")
    print(f"  ({round(time.monotonic() - t0, 1)}s)")

    # --- applications: 1 per candidate ---
    application_rows = []
    for c, p in zip(candidate_rows, profile_rows):
        application_rows.append(
            {
                "id": uuid.uuid4(), "company_id": company_id, "job_id": random.choice(job_ids),
                "candidate_id": c["id"], "candidate_profile_id": p["id"],
                "current_stage_id": random.choice(stage_ids), "status": random.choices(
                    ["active", "rejected", "withdrawn", "hired"], weights=[60, 30, 5, 5]
                )[0],
                "applied_at": _rand_past(180),
            }
        )
    _batched_insert(Application.__table__, application_rows, "applications")

    # --- stage history: ~40% of applications get 1-3 moves ---
    history_rows = []
    for a in application_rows:
        if random.random() < 0.4:
            for _ in range(random.randint(1, 3)):
                history_rows.append(
                    {
                        "id": uuid.uuid4(), "application_id": a["id"],
                        "to_stage_id": random.choice(stage_ids), "created_at": _rand_past(120),
                    }
                )
    _batched_insert(ApplicationStageHistory.__table__, history_rows, "application_stage_history")

    # --- interviews: ~5% of applications ---
    interview_rows = [
        {
            "id": uuid.uuid4(), "company_id": company_id, "application_id": a["id"],
            "pipeline_stage_id": random.choice(stage_ids), "round_name": "Technical Screen",
            "status": random.choice(["scheduled", "completed", "cancelled"]), "created_by": user.id,
        }
        for a in application_rows if random.random() < 0.05
    ]
    _batched_insert(Interview.__table__, interview_rows, "interviews")

    # --- offers: ~3% of applications ---
    offer_rows = []
    for a in application_rows:
        if random.random() < 0.03:
            status = random.choices(["sent", "accepted", "rejected", "expired"], weights=[20, 40, 30, 10])[0]
            offer_rows.append(
                {
                    "id": uuid.uuid4(), "company_id": company_id, "application_id": a["id"],
                    "salary_offered": random.randint(60000, 220000), "status": status,
                    "created_by": user.id,
                    "sent_at": _rand_past(90),
                    "responded_at": _rand_past(60) if status in ("accepted", "rejected") else None,
                }
            )
    _batched_insert(Offer.__table__, offer_rows, "offers")

    # --- audit logs ---
    audit_rows = [
        {
            "id": uuid.uuid4(), "company_id": company_id, "actor_id": user.id, "actor_type": "user",
            "entity_type": random.choice(["application", "job", "offer", "candidate"]),
            "entity_id": uuid.uuid4(), "action": random.choice(["created", "updated", "status_changed"]),
        }
        for _ in range(10000)
    ]
    _batched_insert(AuditLog.__table__, audit_rows, "audit_logs")

    print("\nDone. Summary:")
    print(f"  candidates:                {len(candidate_rows)}")
    print(f"  applications:              {len(application_rows)}")
    print(f"  application_stage_history: {len(history_rows)}")
    print(f"  interviews:                {len(interview_rows)}")
    print(f"  offers:                    {len(offer_rows)}")
    print(f"  audit_logs:                {len(audit_rows)}")
    print(f"  company_id:                {company_id}")
    return company_id


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic RecruitIQ data for DB benchmarking")
    parser.add_argument("--candidates", type=int, default=100_000)
    parser.add_argument("--reset", action="store_true", help="Delete and regenerate if the benchmark company already exists")
    parser.add_argument("--slug", default="bench-100k")
    parser.add_argument("--name", default="Benchmark 100K Co")
    args = parser.parse_args()

    flask_app = create_app("development")
    with flask_app.app_context():
        generate(args.candidates, args.reset, slug=args.slug, name=args.name)


if __name__ == "__main__":
    main()
