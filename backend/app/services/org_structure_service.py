from app.exceptions.base import ConflictError
from app.models.department import Department, Team, Location


class OrgStructureService:
    def __init__(self, department_repo, team_repo, location_repo=None):
        self.department_repo = department_repo
        self.team_repo = team_repo
        self.location_repo = location_repo


    def create_department(self, tenant_id, name, parent_id=None):
        if self.department_repo.name_taken(tenant_id, name):
            raise ConflictError(f"A department named '{name}' already exists")
        if parent_id is not None:
            # Confirms the parent exists AND belongs to this tenant —
            # get_or_404 enforces both via the tenant-scoped query.
            self.department_repo.get_or_404(parent_id, tenant_id)

        department = Department(company_id=tenant_id, name=name, parent_id=parent_id)
        self.department_repo.add(department)
        self.department_repo.commit()
        return department

    def list_departments(self, tenant_id):
        return self.department_repo.list(tenant_id).all()

    def get_department(self, tenant_id, department_id):
        return self.department_repo.get_or_404(department_id, tenant_id)

    def rename_department(self, tenant_id, department_id, new_name):
        department = self.department_repo.get_or_404(department_id, tenant_id)
        if self.department_repo.name_taken(tenant_id, new_name, exclude_id=department.id):
            raise ConflictError(f"A department named '{new_name}' already exists")
        department.name = new_name
        self.department_repo.commit()
        return department

    def delete_department(self, tenant_id, department_id):
        department = self.department_repo.get_or_404(department_id, tenant_id)
        self.department_repo.delete(department)
        self.department_repo.commit()

    # --- Teams ---------------------------------------------------------

    def create_team(self, tenant_id, name, department_id=None):
        if department_id is not None:
            self.department_repo.get_or_404(department_id, tenant_id)

        team = Team(company_id=tenant_id, name=name, department_id=department_id)
        self.team_repo.add(team)
        self.team_repo.commit()
        return team

    def list_teams(self, tenant_id, department_id=None):
        query = self.team_repo.list(tenant_id)
        if department_id is not None:
            query = query.filter(Team.department_id == department_id)
        return query.all()

    def get_team(self, tenant_id, team_id):
        return self.team_repo.get_or_404(team_id, tenant_id)

    def rename_team(self, tenant_id, team_id, new_name):
        team = self.team_repo.get_or_404(team_id, tenant_id)
        team.name = new_name
        self.team_repo.commit()
        return team

    def move_team(self, tenant_id, team_id, department_id):
        team = self.team_repo.get_or_404(team_id, tenant_id)
        if department_id is not None:
            self.department_repo.get_or_404(department_id, tenant_id)
        team.department_id = department_id
        self.team_repo.commit()
        return team

    def delete_team(self, tenant_id, team_id):
        team = self.team_repo.get_or_404(team_id, tenant_id)
        self.team_repo.delete(team)
        self.team_repo.commit()

    # --- Locations -------------------------------------------------

    def create_location(self, tenant_id, name, city=None, country=None, is_remote=False):
        if self.location_repo.name_taken(tenant_id, name):
            raise ConflictError(f"A location named '{name}' already exists")
        location = Location(
            company_id=tenant_id, name=name, city=city, country=country, is_remote=is_remote
        )
        self.location_repo.add(location)
        self.location_repo.commit()
        return location

    def list_locations(self, tenant_id):
        return self.location_repo.list(tenant_id).all()

    def get_location(self, tenant_id, location_id):
        return self.location_repo.get_or_404(location_id, tenant_id)

    def update_location(self, tenant_id, location_id, **fields):
        location = self.location_repo.get_or_404(location_id, tenant_id)
        if fields.get("name") is not None and self.location_repo.name_taken(
            tenant_id, fields["name"], exclude_id=location.id
        ):
            raise ConflictError(f"A location named '{fields['name']}' already exists")
        for key, value in fields.items():
            if value is not None:
                setattr(location, key, value)
        self.location_repo.commit()
        return location

    def delete_location(self, tenant_id, location_id):
        location = self.location_repo.get_or_404(location_id, tenant_id)
        self.location_repo.delete(location)
        self.location_repo.commit()
