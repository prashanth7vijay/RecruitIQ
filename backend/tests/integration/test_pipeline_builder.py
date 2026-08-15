from app.models.role import Permission


def _grant(db_session, role, code):
    perm = db_session.query(Permission).filter_by(code=code).first()
    if perm is None:
        perm = Permission(code=code)
        db_session.add(perm)
        db_session.flush()
    if perm not in role.permissions:
        role.permissions.append(perm)
    db_session.commit()


SAMPLE_STAGES = [
    {"name": "Screen", "stage_order": 0, "stage_type": "screening"},
    {"name": "Onsite", "stage_order": 1, "stage_type": "interview"},
]


def test_recruiter_with_only_job_create_cannot_design_pipeline(auth_client, db_session, test_user):
    # job.create alone used to be enough to create a pipeline template —
    # this is the exact gap the Pipeline Builder module closes.
    _grant(db_session, test_user.role, "job.create")

    response = auth_client.post(
        "/api/v1/pipeline-templates", json={"name": "Engineering", "stages": SAMPLE_STAGES}
    )
    assert response.status_code == 403


def test_recruiter_can_still_read_pipeline_templates(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "pipeline.manage")
    create_resp = auth_client.post(
        "/api/v1/pipeline-templates", json={"name": "Engineering", "stages": SAMPLE_STAGES}
    )
    template_id = create_resp.get_json()["data"]["id"]

    # A plain recruiter role (no pipeline.manage) should still be able to
    # read templates — they need to pick one when creating a job, just
    # never design one.
    from app.models.role import Role

    plain_role = Role(company_id=None, name="plain_recruiter_test", is_system_role=True)
    db_session.add(plain_role)
    db_session.commit()
    test_user.role_id = plain_role.id
    db_session.commit()

    list_resp = auth_client.get("/api/v1/pipeline-templates")
    assert list_resp.status_code == 200
    get_resp = auth_client.get(f"/api/v1/pipeline-templates/{template_id}")
    assert get_resp.status_code == 200


def test_admin_full_pipeline_crud(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "pipeline.manage")

    create_resp = auth_client.post(
        "/api/v1/pipeline-templates", json={"name": "Engineering", "stages": SAMPLE_STAGES}
    )
    assert create_resp.status_code == 201
    template_id = create_resp.get_json()["data"]["id"]

    rename_resp = auth_client.patch(f"/api/v1/pipeline-templates/{template_id}", json={"name": "Eng Hiring"})
    assert rename_resp.status_code == 200
    assert rename_resp.get_json()["data"]["name"] == "Eng Hiring"

    replace_stages_resp = auth_client.patch(
        f"/api/v1/pipeline-templates/{template_id}",
        json={"stages": [{"name": "Phone Screen", "stage_order": 0, "stage_type": "screening"}]},
    )
    assert replace_stages_resp.status_code == 200
    stages = replace_stages_resp.get_json()["data"]["stages"]
    assert len(stages) == 1
    assert stages[0]["name"] == "Phone Screen"

    delete_resp = auth_client.delete(f"/api/v1/pipeline-templates/{template_id}")
    assert delete_resp.status_code == 200

    missing_resp = auth_client.get(f"/api/v1/pipeline-templates/{template_id}")
    assert missing_resp.status_code == 404


def test_only_one_default_pipeline_template_at_a_time(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "pipeline.manage")

    first_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "Engineering", "stages": SAMPLE_STAGES, "is_default": True},
    )
    first_id = first_resp.get_json()["data"]["id"]
    assert first_resp.get_json()["data"]["is_default"] is True

    second_resp = auth_client.post(
        "/api/v1/pipeline-templates",
        json={"name": "Sales", "stages": SAMPLE_STAGES, "is_default": True},
    )
    assert second_resp.get_json()["data"]["is_default"] is True

    # Setting the second as default should have cleared the first.
    first_get = auth_client.get(f"/api/v1/pipeline-templates/{first_id}")
    assert first_get.get_json()["data"]["is_default"] is False


def test_cannot_delete_pipeline_template_still_used_by_a_job(auth_client, db_session, test_user):
    _grant(db_session, test_user.role, "pipeline.manage")
    _grant(db_session, test_user.role, "job.create")

    template_resp = auth_client.post(
        "/api/v1/pipeline-templates", json={"name": "Engineering", "stages": SAMPLE_STAGES}
    )
    template_id = template_resp.get_json()["data"]["id"]

    job_resp = auth_client.post(
        "/api/v1/jobs",
        json={"title": "Backend Engineer", "description": "x", "pipeline_template_id": template_id},
    )
    assert job_resp.status_code == 201

    delete_resp = auth_client.delete(f"/api/v1/pipeline-templates/{template_id}")
    assert delete_resp.status_code == 409


def test_cannot_edit_or_delete_another_tenants_pipeline_template(auth_client, db_session, test_user, test_company):
    _grant(db_session, test_user.role, "pipeline.manage")

    from app.models.company import Company
    from app.models.pipeline import PipelineTemplate

    other_company = Company(name="Other Co", slug="other-co-pipeline-test")
    db_session.add(other_company)
    db_session.commit()
    foreign_template = PipelineTemplate(company_id=other_company.id, name="Foreign Pipeline")
    db_session.add(foreign_template)
    db_session.commit()

    patch_resp = auth_client.patch(
        f"/api/v1/pipeline-templates/{foreign_template.id}", json={"name": "Hijacked"}
    )
    assert patch_resp.status_code == 404

    delete_resp = auth_client.delete(f"/api/v1/pipeline-templates/{foreign_template.id}")
    assert delete_resp.status_code == 404
