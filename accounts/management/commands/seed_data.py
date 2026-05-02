from django.core.management.base import BaseCommand
from accounts.models import User
from applications.models import IPApplication, CoInventor
from services.application_service import submit_application, assign_evaluator
from services.workflow_service import update_application_status
from marketplace.models import MarketplaceItem, InterestRequest

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        def ensure_user(email, full_name, password, role):
            user = User.objects.filter(email=email).first()
            if user:
                return user
            return User.objects.create_user(
                email,
                full_name,
                password,
                role=role,
                is_verified=True,
            )

        # 1. Create Users
        admin_user = User.objects.filter(role="admin").first()
        if not admin_user:
            admin_user = User.objects.create_superuser("admin@psu.edu.ph", "System Admin", "admin123")

        applicant1 = ensure_user("alice@psu.edu.ph", "Alice Inventor", "alice123", "applicant")
        applicant2 = ensure_user("bob@psu.edu.ph", "Bob Researcher", "bob123", "applicant")
        evaluator1 = ensure_user("eval@psu.edu.ph", "Eve Evaluator", "eval123", "evaluator")
        
        self.stdout.write("Created test users.")

        # 2. Create Applications
        
        # A Draft Application
        app1 = IPApplication.objects.create(
            title="Automated Solar Irrigation System",
            description="A novel irrigation system using solar tech.",
            ip_type="Patent",
            created_by=applicant1,
            status="Draft"
        )
        
        # A Submitted Application
        app2 = IPApplication.objects.create(
            title="PSU Mango Harvesting Tool",
            description="Ergonomic harvesting tool.",
            ip_type="Utility Model",
            created_by=applicant2,
            status="Draft"
        )
        submit_application(app2, applicant2)
        
        # An Under Evaluation Application
        app3 = IPApplication.objects.create(
            title="Marine Sensor Casing Design",
            description="Industrial enclosure design for coastal monitoring sensors.",
            ip_type="Industrial Design",
            created_by=applicant1,
            status="Draft"
        )
        submit_application(app3, applicant1)
        assign_evaluator(app3, evaluator1.id, admin_user)
        
        # A Deficient Application
        app4 = IPApplication.objects.create(
            title="Smart Classroom Software",
            description="Automation software for managing classes.",
            ip_type="Copyright",
            created_by=applicant2,
            status="Draft"
        )
        submit_application(app4, applicant2)
        assign_evaluator(app4, evaluator1.id, admin_user)
        update_application_status(app4, evaluator1, "Deficient", "Please provide the source code listings.")

        # A Certified Application (To go to Marketplace)
        app5 = IPApplication.objects.create(
            title="Eco-friendly Bamboo Bicycles",
            description="Lightweight bamboo structured bicycles.",
            ip_type="Patent",
            created_by=applicant1,
            marketplace_consent=True,
            status="Draft"
        )
        submit_application(app5, applicant1)
        assign_evaluator(app5, evaluator1.id, admin_user)
        update_application_status(app5, evaluator1, "Certified", "All documents verified and prior art search completed.")

        self.stdout.write("Created test applications and workflow states.")

        # 3. Add Co-inventors
        CoInventor.objects.create(application=app5, name="Charlie Engineer", email="charlie@psu.edu.ph")

        # 4. Add to Marketplace
        market_item = MarketplaceItem.objects.create(
            application=app5,
            title="Eco-friendly Bamboo Bicycles - Tech Offer",
            abstract="We are looking for manufacturing partners for our lightweight bamboo structured bicycles developed at PSU.",
            is_public=True
        )

        # 5. Create Interest Requests
        InterestRequest.objects.create(
            marketplace_item=market_item,
            requester_name="Green Tech Manufacturing",
            requester_email="contact@greentech.local",
            message="We are highly interested in licensing this technology. Please send us more details regarding the manufacturing process."
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))
