from app.exceptions.base import NotFoundError
from app.models.company import Company


class CompanyRepository:
    def __init__(self, session):
        self.session = session

    def get_or_404(self, company_id):
        company = self.session.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise NotFoundError("Company not found")
        return company

    def get_by_slug(self, slug):
        return self.session.query(Company).filter(Company.slug == slug).first()

    def add(self, obj):
        self.session.add(obj)
        return obj

    def commit(self):
        self.session.commit()
