"""
Persona Generation Module
Provides seeded fake data generation for industry-specific customer personas.
Uses Faker with instance seeding for deterministic, session-consistent data.
"""

from datetime import date, timedelta
from faker import Faker
from pydantic import BaseModel


# =============================================================================
# Banking Models
# =============================================================================

class Transaction(BaseModel):
    """A single banking transaction."""
    date: str
    description: str
    amount: float
    category: str  # "debit" or "credit"


class BankingPersona(BaseModel):
    """Banking customer persona with account and transaction data."""
    name: str
    member_since: str
    checking_balance: float
    savings_balance: float
    account_number_last4: str
    credit_score: int
    credit_limit: float
    recent_transactions: list[Transaction]


# =============================================================================
# Insurance Models
# =============================================================================

class Policy(BaseModel):
    """An insurance policy."""
    type: str  # "auto", "home", "life", "umbrella"
    coverage: float
    premium: float
    deductible: float
    policy_number: str
    renewal_date: str


class Claim(BaseModel):
    """An insurance claim."""
    claim_id: str
    date: str
    type: str
    amount: float
    status: str  # "pending", "approved", "denied", "in_review"


class InsurancePersona(BaseModel):
    """Insurance customer persona with policies and claims."""
    name: str
    member_since: str
    active_policies: list[Policy]
    claims_history: list[Claim]
    total_coverage: float
    monthly_premium: float
    risk_score: str  # "low", "medium", "high"


# =============================================================================
# Healthcare Models
# =============================================================================

class Appointment(BaseModel):
    """A healthcare appointment."""
    date: str
    time: str
    provider: str
    specialty: str
    location: str


class Prescription(BaseModel):
    """An active prescription."""
    medication: str
    dosage: str
    frequency: str
    refills_remaining: int


class HealthcarePersona(BaseModel):
    """Healthcare patient persona with appointments and prescriptions."""
    name: str
    member_id: str
    date_of_birth: str
    primary_care_provider: str
    plan_name: str
    deductible: float
    deductible_met: float
    out_of_pocket_max: float
    out_of_pocket_spent: float
    upcoming_appointments: list[Appointment]
    active_prescriptions: list[Prescription]


# =============================================================================
# Generator Functions
# =============================================================================

def generate_banking_persona(seed: int) -> BankingPersona:
    """Generate a deterministic banking persona from seed."""
    fake = Faker()
    fake.seed_instance(seed)

    # Generate 5-10 recent transactions
    num_transactions = fake.pyint(min_value=5, max_value=10)
    transactions = []
    for _ in range(num_transactions):
        is_debit = fake.pybool()
        transactions.append(Transaction(
            date=fake.date_between(start_date="-30d", end_date="today").isoformat(),
            description=fake.company() if is_debit else fake.bs().title(),
            amount=round(fake.pyfloat(min_value=5, max_value=500), 2) if is_debit else round(fake.pyfloat(min_value=100, max_value=3000), 2),
            category="debit" if is_debit else "credit"
        ))

    # Sort transactions by date (most recent first)
    transactions.sort(key=lambda t: t.date, reverse=True)

    return BankingPersona(
        name="Marco Casalaina",
        member_since=str(fake.date_between(start_date="-15y", end_date="-1y").year),
        checking_balance=round(fake.pyfloat(min_value=500, max_value=15000), 2),
        savings_balance=round(fake.pyfloat(min_value=1000, max_value=50000), 2),
        account_number_last4=fake.numerify("####"),
        credit_score=fake.pyint(min_value=620, max_value=820),
        credit_limit=round(fake.pyfloat(min_value=2000, max_value=25000), 2),
        recent_transactions=transactions
    )


def generate_insurance_persona(seed: int) -> InsurancePersona:
    """Generate a deterministic insurance persona from seed."""
    fake = Faker()
    fake.seed_instance(seed)

    # Generate 1-3 policies
    policy_types = ["Auto", "Home", "Life", "Umbrella"]
    num_policies = fake.pyint(min_value=1, max_value=3)
    selected_types = fake.random_elements(elements=policy_types, length=num_policies, unique=True)

    policies = []
    total_coverage = 0
    total_premium = 0

    for policy_type in selected_types:
        if policy_type == "Auto":
            coverage = fake.pyint(min_value=25000, max_value=100000)
            premium = round(fake.pyfloat(min_value=80, max_value=250), 2)
            deductible = fake.random_element([250, 500, 1000])
        elif policy_type == "Home":
            coverage = fake.pyint(min_value=200000, max_value=750000)
            premium = round(fake.pyfloat(min_value=100, max_value=400), 2)
            deductible = fake.random_element([500, 1000, 2500])
        elif policy_type == "Life":
            coverage = fake.pyint(min_value=100000, max_value=1000000)
            premium = round(fake.pyfloat(min_value=30, max_value=150), 2)
            deductible = 0
        else:  # Umbrella
            coverage = fake.pyint(min_value=1000000, max_value=5000000)
            premium = round(fake.pyfloat(min_value=20, max_value=80), 2)
            deductible = 0

        total_coverage += coverage
        total_premium += premium

        policies.append(Policy(
            type=policy_type,
            coverage=float(coverage),
            premium=premium,
            deductible=float(deductible),
            policy_number=fake.bothify("POL-####-????").upper(),
            renewal_date=fake.date_between(start_date="+30d", end_date="+365d").isoformat()
        ))

    # Generate 0-2 claims history
    num_claims = fake.pyint(min_value=0, max_value=2)
    claims = []
    claim_types = ["Collision", "Property Damage", "Medical", "Theft", "Weather"]
    claim_statuses = ["approved", "pending", "in_review", "denied"]

    for _ in range(num_claims):
        claims.append(Claim(
            claim_id=fake.bothify("CLM-########").upper(),
            date=fake.date_between(start_date="-2y", end_date="-30d").isoformat(),
            type=fake.random_element(claim_types),
            amount=round(fake.pyfloat(min_value=500, max_value=15000), 2),
            status=fake.random_element(claim_statuses)
        ))

    # Determine risk score based on claims
    if num_claims == 0:
        risk_score = "low"
    elif num_claims == 1:
        risk_score = fake.random_element(["low", "medium"])
    else:
        risk_score = fake.random_element(["medium", "high"])

    return InsurancePersona(
        name="Marco Casalaina",
        member_since=str(fake.date_between(start_date="-20y", end_date="-1y").year),
        active_policies=policies,
        claims_history=claims,
        total_coverage=float(total_coverage),
        monthly_premium=round(total_premium, 2),
        risk_score=risk_score
    )


def generate_healthcare_persona(seed: int) -> HealthcarePersona:
    """Generate a deterministic healthcare persona from seed."""
    fake = Faker()
    fake.seed_instance(seed)

    # Generate 0-2 upcoming appointments
    num_appointments = fake.pyint(min_value=0, max_value=2)
    specialties = ["Primary Care", "Cardiology", "Dermatology", "Orthopedics", "Ophthalmology", "Dentistry"]
    appointments = []

    for _ in range(num_appointments):
        specialty = fake.random_element(specialties)
        appointments.append(Appointment(
            date=fake.date_between(start_date="+1d", end_date="+90d").isoformat(),
            time=fake.random_element(["9:00 AM", "10:30 AM", "1:00 PM", "2:30 PM", "4:00 PM"]),
            provider=f"Dr. {fake.last_name()}",
            specialty=specialty,
            location=f"{fake.city()} Medical Center"
        ))

    # Sort appointments by date
    appointments.sort(key=lambda a: a.date)

    # Generate 1-3 active prescriptions
    num_prescriptions = fake.pyint(min_value=1, max_value=3)
    medications = [
        ("Lisinopril", "10mg", "Once daily"),
        ("Metformin", "500mg", "Twice daily"),
        ("Atorvastatin", "20mg", "Once daily at bedtime"),
        ("Omeprazole", "20mg", "Once daily before breakfast"),
        ("Amlodipine", "5mg", "Once daily"),
        ("Levothyroxine", "50mcg", "Once daily on empty stomach"),
        ("Sertraline", "50mg", "Once daily"),
        ("Gabapentin", "300mg", "Three times daily"),
    ]
    selected_meds = fake.random_elements(elements=medications, length=num_prescriptions, unique=True)

    prescriptions = []
    for med_name, dosage, frequency in selected_meds:
        prescriptions.append(Prescription(
            medication=med_name,
            dosage=dosage,
            frequency=frequency,
            refills_remaining=fake.pyint(min_value=0, max_value=5)
        ))

    # Plan and deductible info
    plan_names = ["Gold PPO", "Silver HMO", "Bronze HDHP", "Platinum PPO"]
    deductible = fake.random_element([500, 1000, 1500, 2500, 3000, 5000])
    deductible_met = round(fake.pyfloat(min_value=0, max_value=deductible), 2)
    out_of_pocket_max = fake.random_element([3000, 5000, 6500, 8000])
    out_of_pocket_spent = round(fake.pyfloat(min_value=0, max_value=out_of_pocket_max * 0.6), 2)

    return HealthcarePersona(
        name="Marco Casalaina",
        member_id=fake.bothify("MBR-#########").upper(),
        date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=75).isoformat(),
        primary_care_provider=f"Dr. {fake.last_name()}",
        plan_name=fake.random_element(plan_names),
        deductible=float(deductible),
        deductible_met=deductible_met,
        out_of_pocket_max=float(out_of_pocket_max),
        out_of_pocket_spent=out_of_pocket_spent,
        upcoming_appointments=appointments,
        active_prescriptions=prescriptions
    )


# =============================================================================
# Generic Persona Generator
# =============================================================================

def generate_generic_persona(mode_id: str, mode_name: str, seed: int) -> dict:
    """
    Generate a generic persona for dynamically generated industries.
    Uses mode name to customize the context but follows a generic structure.

    Args:
        mode_id: The mode identifier (e.g., "pet_store")
        mode_name: Display name of the mode (e.g., "Pet Store")
        seed: Deterministic seed for reproducible generation

    Returns:
        Dictionary with generic customer profile data
    """
    fake = Faker()
    fake.seed_instance(seed)

    # Generate a generic customer profile
    name = fake.name()
    member_since = fake.date_between(start_date='-5y', end_date='-1y').strftime('%B %Y')

    # Generate some generic metrics that work for any business
    # Use seed for consistency
    account_value = round(fake.pyfloat(min_value=1000, max_value=50000), 2)
    transactions_this_month = fake.random_int(min=5, max=30)
    loyalty_points = fake.random_int(min=100, max=10000)

    return {
        "name": name,
        "customer_since": member_since,
        "account_value": account_value,
        "recent_activity_count": transactions_this_month,
        "loyalty_points": loyalty_points,
        "status": fake.random_element(["Bronze", "Silver", "Gold", "Platinum"]),
        "context_hint": f"This is a {mode_name} customer dashboard."
    }


# =============================================================================
# Factory Function
# =============================================================================

PERSONA_GENERATORS = {
    "banking": generate_banking_persona,
    "insurance": generate_insurance_persona,
    "healthcare": generate_healthcare_persona,
}


def generate_persona(mode_id: str, seed: int) -> dict:
    """
    Generate industry-appropriate persona for mode.

    Args:
        mode_id: The mode identifier ("banking", "insurance", "healthcare", or any dynamic mode)
        seed: Deterministic seed for reproducible generation

    Returns:
        Dictionary representation of the persona
    """
    generator = PERSONA_GENERATORS.get(mode_id.lower())
    if generator:
        persona = generator(seed)
        return persona.model_dump()
    # Fallback to generic persona for dynamically generated modes
    return generate_generic_persona(mode_id, mode_id.replace('_', ' ').title(), seed)
