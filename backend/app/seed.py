"""
Database seeder — populates the database with realistic sample data.

Seeds:
- 4 services (Physiotherapy, Wound Dressing, IV Therapy, General Checkup)
- 5 caregivers with service qualifications
- 3 patients

All IDs are deterministic UUIDs for consistent testing and documentation.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.caregiver import Caregiver
from app.models.patient import Patient
from app.models.caregiver_service import CaregiverService


SVC_PHYSIOTHERAPY = "svc-physio-0001-0001-000000000001"
SVC_WOUND_DRESSING = "svc-wound-0002-0002-000000000002"
SVC_IV_THERAPY = "svc-ivthr-0003-0003-000000000003"
SVC_GENERAL_CHECKUP = "svc-genchk-004-0004-000000000004"

CG_ALICE = "cg-alice-0001-0001-000000000001"
CG_BOB = "cg-bob00-0002-0002-000000000002"
CG_CAROL = "cg-carol-0003-0003-000000000003"
CG_DAVID = "cg-david-0004-0004-000000000004"
CG_EVE = "cg-eve00-0005-0005-000000000005"

PT_JOHN = "pt-john0-0001-0001-000000000001"
PT_JANE = "pt-jane0-0002-0002-000000000002"
PT_MIKE = "pt-mike0-0003-0003-000000000003"


async def seed_database(session: AsyncSession) -> None:
    """
    Seed the database with sample data if it's empty.

    Idempotent — checks if services table has data before seeding.
    """
    result = await session.execute(select(Service).limit(1))
    if result.scalar_one_or_none() is not None:
        return  # Already seeded

    print("🌱 Seeding database with sample data...")

    services = [
        Service(
            id=SVC_PHYSIOTHERAPY,
            name="Physiotherapy",
            duration_minutes=60,
            price=1500.00,
            description="At-home physiotherapy session including assessment and exercises",
        ),
        Service(
            id=SVC_WOUND_DRESSING,
            name="Wound Dressing",
            duration_minutes=30,
            price=500.00,
            description="Professional wound cleaning, dressing, and care",
        ),
        Service(
            id=SVC_IV_THERAPY,
            name="IV Therapy",
            duration_minutes=45,
            price=2000.00,
            description="Intravenous fluid or medication administration",
        ),
        Service(
            id=SVC_GENERAL_CHECKUP,
            name="General Checkup",
            duration_minutes=30,
            price=800.00,
            description="Routine health checkup including vitals and basic assessment",
        ),
    ]
    session.add_all(services)

    caregivers = [
        Caregiver(id=CG_ALICE, name="Alice Sharma", phone="+91-9876543210"),
        Caregiver(id=CG_BOB, name="Bob Patel", phone="+91-9876543211"),
        Caregiver(id=CG_CAROL, name="Carol Mehta", phone="+91-9876543212"),
        Caregiver(id=CG_DAVID, name="David Kumar", phone="+91-9876543213"),
        Caregiver(id=CG_EVE, name="Eve Singh", phone="+91-9876543214"),
    ]
    session.add_all(caregivers)

    patients = [
        Patient(id=PT_JOHN, name="John Doe", phone="+91-9123456780"),
        Patient(id=PT_JANE, name="Jane Smith", phone="+91-9123456781"),
        Patient(id=PT_MIKE, name="Mike Wilson", phone="+91-9123456782"),
    ]
    session.add_all(patients)

    qualifications = [
        CaregiverService(caregiver_id=CG_ALICE, service_id=SVC_PHYSIOTHERAPY),
        CaregiverService(caregiver_id=CG_ALICE, service_id=SVC_GENERAL_CHECKUP),
        CaregiverService(caregiver_id=CG_BOB, service_id=SVC_WOUND_DRESSING),
        CaregiverService(caregiver_id=CG_BOB, service_id=SVC_IV_THERAPY),
        CaregiverService(caregiver_id=CG_BOB, service_id=SVC_GENERAL_CHECKUP),
        CaregiverService(caregiver_id=CG_CAROL, service_id=SVC_PHYSIOTHERAPY),
        CaregiverService(caregiver_id=CG_CAROL, service_id=SVC_WOUND_DRESSING),
        CaregiverService(caregiver_id=CG_DAVID, service_id=SVC_IV_THERAPY),
        CaregiverService(caregiver_id=CG_DAVID, service_id=SVC_GENERAL_CHECKUP),
        CaregiverService(caregiver_id=CG_EVE, service_id=SVC_PHYSIOTHERAPY),
        CaregiverService(caregiver_id=CG_EVE, service_id=SVC_WOUND_DRESSING),
        CaregiverService(caregiver_id=CG_EVE, service_id=SVC_IV_THERAPY),
    ]
    session.add_all(qualifications)

    await session.commit()
    print("✅ Database seeded successfully!")
    print(f"   → {len(services)} services")
    print(f"   → {len(caregivers)} caregivers")
    print(f"   → {len(patients)} patients")
    print(f"   → {len(qualifications)} caregiver-service qualifications")
