# Phase 5: Persona - Research

**Researched:** 2026-01-18
**Domain:** Fake data generation, seeded personas, session state management
**Confidence:** HIGH

## Summary

This phase requires generating consistent, industry-appropriate fake customer personas that persist within a WebSocket session. The user switches to a mode (banking, insurance, healthcare), and a persona is generated with realistic data that the AI references naturally throughout the conversation.

The established approach uses Python's **Faker** library with **seed-based deterministic generation**. Faker is the de facto standard for fake data in Python with 40+ million monthly downloads, comprehensive built-in providers (person, bank, credit card, address, job, company), and robust seeding support. The seeding mechanism ensures the same seed produces identical personas across requests within a session.

**Primary recommendation:** Use Faker with `seed_instance()` for per-session deterministic persona generation. Define Pydantic models for industry-specific persona schemas. Generate persona on mode switch, store in session state, include in AI system prompt.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Faker | ^40.1.2 | Fake data generation | Industry standard, 40M+ monthly downloads, built-in providers for names/addresses/bank/credit cards, robust seeding |
| Pydantic | ^2.0 | Persona schema validation | Already in use via FastAPI, type-safe models, serialization |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | - | Seed generation from session ID | Convert session UUID to integer seed |
| random (stdlib) | - | Additional randomization | Custom ranges, weighted choices |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Faker | Mimesis | 12x faster, but smaller community, less comprehensive providers, recent breaking changes (v19 dropped builtin providers) |
| Faker | Polyfactory | Better Pydantic integration, but has known seeding bugs with `seed_random`, more complex setup |
| Custom generation | Faker providers | Less code to maintain, battle-tested edge cases |

**Installation:**
```bash
pip install faker>=40.0.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── main.py              # WebSocket endpoint (existing)
├── modes.py             # Mode definitions (existing)
├── chat.py              # Chat handler (existing)
├── persona.py           # NEW: Persona generation and schemas
└── session.py           # NEW: Session state management
```

### Pattern 1: Seeded Persona Generation
**What:** Generate deterministic persona from session seed on mode switch
**When to use:** Every mode switch event
**Example:**
```python
# Source: Faker documentation (https://faker.readthedocs.io/)
from faker import Faker
from pydantic import BaseModel

class BankingPersona(BaseModel):
    name: str
    account_number: str
    checking_balance: float
    savings_balance: float
    credit_score: int
    recent_transactions: list[dict]

def generate_banking_persona(seed: int) -> BankingPersona:
    """Generate consistent banking persona from seed."""
    fake = Faker()
    fake.seed_instance(seed)  # Instance-specific seeding

    # Same seed = same data every time
    return BankingPersona(
        name=fake.name(),
        account_number=fake.bban(),
        checking_balance=round(fake.pyfloat(min_value=500, max_value=50000), 2),
        savings_balance=round(fake.pyfloat(min_value=1000, max_value=100000), 2),
        credit_score=fake.pyint(min_value=580, max_value=850),
        recent_transactions=generate_transactions(fake, count=10)
    )
```

### Pattern 2: Session-Scoped State
**What:** Store persona in per-connection state dictionary
**When to use:** All WebSocket connections requiring persona persistence
**Example:**
```python
# Source: FastAPI WebSocket patterns
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SessionState:
    session_id: str
    seed: int
    current_mode: str = "banking"
    persona: Optional[dict] = None

# Per-connection state storage
_sessions: dict[str, SessionState] = {}

async def websocket_endpoint(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    seed = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
    _sessions[session_id] = SessionState(session_id=session_id, seed=seed)

    try:
        # ... handle messages
        pass
    finally:
        del _sessions[session_id]  # Cleanup on disconnect
```

### Pattern 3: Mode-Specific Persona Factory
**What:** Factory pattern dispatching to industry-specific generators
**When to use:** Mode switch events
**Example:**
```python
PERSONA_GENERATORS = {
    "banking": generate_banking_persona,
    "insurance": generate_insurance_persona,
    "healthcare": generate_healthcare_persona,
}

def generate_persona(mode_id: str, seed: int) -> dict:
    """Generate industry-appropriate persona for mode."""
    generator = PERSONA_GENERATORS.get(mode_id)
    if generator:
        persona = generator(seed)
        return persona.model_dump()
    return {}
```

### Pattern 4: AI System Prompt Integration
**What:** Include persona details in system prompt for natural references
**When to use:** Every LLM call after persona generation
**Example:**
```python
def build_system_prompt(mode: Mode, persona: dict) -> str:
    """Build system prompt with persona context."""
    base_prompt = mode.system_prompt

    persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Account: {persona.get('account_number', 'N/A')}
{"- Checking Balance: $" + f"{persona.get('checking_balance'):,.2f}" if 'checking_balance' in persona else ""}
{"- Credit Score: " + str(persona.get('credit_score')) if 'credit_score' in persona else ""}

Reference this customer's information naturally in your responses. Speak as if you know this customer well.
"""
    return f"{base_prompt}\n\n{persona_context}"
```

### Anti-Patterns to Avoid
- **Global Faker instance with class seed:** Using `Faker.seed()` affects all instances globally. Use `fake.seed_instance()` for per-session isolation.
- **Storing persona in module-level variables:** Current `modes.py` uses `_current_mode` globally. For multi-connection support, use per-connection state.
- **Regenerating persona on each request:** Cache persona in session state after mode switch. Only regenerate on explicit mode change.
- **Hardcoded seed values:** Derive seed from session ID for user-specific consistency, not fixed values like `seed=42`.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Name generation | Custom name lists | `fake.name()` | Handles locales, gender balance, edge cases |
| Account numbers | Random digits | `fake.bban()`, `fake.iban()` | Generates valid checksums, proper formats |
| Credit cards | Random 16 digits | `fake.credit_card_number()` | Passes Luhn validation, realistic providers |
| Addresses | String templates | `fake.address()` | Real street patterns, valid zip codes, proper formatting |
| SSN/Tax IDs | Random numbers | `fake.ssn()` | Valid formats, proper locale handling |
| Transaction history | Manual date math | `fake.date_between()` | Handles weekends, business days, realistic patterns |

**Key insight:** Faker's providers handle edge cases you won't think of - localization, validation checksums, realistic distributions, gender-appropriate names. Custom generation looks easy but produces obviously fake data.

## Common Pitfalls

### Pitfall 1: Global Seeding Breaking Multi-Session
**What goes wrong:** Using `Faker.seed(n)` seeds ALL Faker instances globally, causing different sessions to share the same "random" values.
**Why it happens:** The class method `Faker.seed()` sets a shared random state across all instances.
**How to avoid:** Always use `fake.seed_instance(n)` to seed individual Faker instances.
**Warning signs:** Different browser tabs showing same persona, or persona "contamination" between users.

### Pitfall 2: Seed Instability Across Faker Versions
**What goes wrong:** Same seed produces different data after Faker upgrade.
**Why it happens:** Faker explicitly does not guarantee seed stability across versions. Dataset updates change output.
**How to avoid:** Pin Faker to exact version in requirements.txt (`faker==40.1.2`). Accept that persona data is ephemeral (session-only, not persisted).
**Warning signs:** Tests failing after dependency update with "unexpected persona data".

### Pitfall 3: Session State Memory Leaks
**What goes wrong:** `_sessions` dictionary grows unbounded if cleanup fails.
**Why it happens:** WebSocket disconnect exceptions bypass cleanup code.
**How to avoid:** Use `try/finally` pattern to ensure session cleanup on any disconnect.
**Warning signs:** Memory growth over time, stale sessions accumulating.

### Pitfall 4: Unrealistic Financial Values
**What goes wrong:** Generated values look fake (e.g., exactly $10,000.00 balances, perfect round numbers).
**Why it happens:** Using integer ranges or uniform distributions.
**How to avoid:** Use realistic distributions - checking accounts $500-$15,000 weighted toward lower; savings $1,000-$100,000 log-normal; credit scores 580-850 bell curve around 700.
**Warning signs:** Demo feels "off" even if technically working.

### Pitfall 5: Missing Persona Context in Long Conversations
**What goes wrong:** AI "forgets" persona details mid-conversation or gives inconsistent answers.
**Why it happens:** Only including persona in first message, or context window pushes it out.
**How to avoid:** Include persona in system prompt (persistent context). For very long conversations, periodically remind with persona summary.
**Warning signs:** AI gives generic responses instead of persona-specific ones.

## Code Examples

Verified patterns from official sources:

### Seeding a Faker Instance (HIGH confidence)
```python
# Source: https://faker.readthedocs.io/en/master/fakerclass.html
from faker import Faker

# Create instance and seed it (NOT the class method)
fake = Faker()
fake.seed_instance(4321)

# Now deterministic - same calls = same results
print(fake.name())  # 'Margaret Boehm' (always)
print(fake.name())  # 'Tammy Strickland' (always)
```

### Banking Data Generation (HIGH confidence)
```python
# Source: https://faker.readthedocs.io/en/master/providers/faker.providers.bank.html
from faker import Faker

fake = Faker()
fake.seed_instance(12345)

# Bank-specific methods
account = {
    "bban": fake.bban(),           # Basic Bank Account Number
    "iban": fake.iban(),           # International Bank Account Number
    "aba": fake.aba(),             # ABA routing number (US)
    "swift": fake.swift(),         # SWIFT code
    "bank_name": fake.bank(),      # Bank institution name
}
```

### Credit Card Data (HIGH confidence)
```python
# Source: https://faker.readthedocs.io/en/master/providers/faker.providers.credit_card.html
from faker import Faker

fake = Faker()
fake.seed_instance(12345)

card = {
    "number": fake.credit_card_number(),    # Valid Luhn checksum
    "provider": fake.credit_card_provider(), # e.g., "VISA", "Mastercard"
    "expire": fake.credit_card_expire(),    # e.g., "04/28"
    "cvv": fake.credit_card_security_code(), # 3 or 4 digits
}
```

### Profile Generation (HIGH confidence)
```python
# Source: https://faker.readthedocs.io/en/master/providers/faker.providers.profile.html
from faker import Faker

fake = Faker()
fake.seed_instance(12345)

# Complete profile in one call
profile = fake.profile()
# Returns: {
#   'name': str, 'username': str, 'sex': str,
#   'address': str, 'mail': str, 'birthdate': date,
#   'job': str, 'company': str, 'ssn': str,
#   'residence': str, 'current_location': tuple,
#   'blood_group': str, 'website': list
# }

# Or simplified
simple = fake.simple_profile()
# Returns: name, username, sex, address, mail, birthdate
```

### Session ID to Seed Conversion (MEDIUM confidence)
```python
# Pattern: Convert UUID to deterministic integer seed
import hashlib
import uuid

def session_to_seed(session_id: str) -> int:
    """Convert session UUID to integer seed for Faker."""
    # MD5 hash provides good distribution, truncate to int
    hash_hex = hashlib.md5(session_id.encode()).hexdigest()
    return int(hash_hex[:8], 16)  # First 8 hex chars = 32 bits

# Usage
session_id = str(uuid.uuid4())  # e.g., "550e8400-e29b-41d4-a716-446655440000"
seed = session_to_seed(session_id)  # e.g., 1427109888
```

## Industry-Specific Schemas

### Banking Persona (MEDIUM confidence - based on industry patterns)
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    category: str  # "debit" or "credit"
    merchant: Optional[str] = None

class BankingPersona(BaseModel):
    # Identity
    name: str
    member_since: str  # e.g., "2019"

    # Accounts
    checking_balance: float
    savings_balance: float
    account_number: str  # Last 4 only for display

    # Credit
    credit_score: int
    credit_limit: float
    credit_used: float

    # Activity
    recent_transactions: list[Transaction]
    pending_payments: int
    monthly_spending: float
```

### Insurance Persona (MEDIUM confidence - based on industry patterns)
```python
class Policy(BaseModel):
    type: str  # "auto", "home", "life"
    coverage: float
    premium: float
    deductible: float
    policy_number: str
    renewal_date: str

class Claim(BaseModel):
    claim_id: str
    date: str
    type: str
    amount: float
    status: str  # "pending", "approved", "denied"

class InsurancePersona(BaseModel):
    name: str
    member_since: str

    # Policies
    active_policies: list[Policy]
    total_coverage: float
    next_premium_due: str
    monthly_premium: float

    # Claims
    claims_history: list[Claim]
    pending_claims: int

    # Risk profile
    risk_score: str  # "low", "medium", "high"
```

### Healthcare Persona (MEDIUM confidence - based on industry patterns)
```python
class Appointment(BaseModel):
    date: str
    time: str
    provider: str
    specialty: str
    location: str
    reason: str

class Prescription(BaseModel):
    medication: str
    dosage: str
    frequency: str
    refills_remaining: int
    prescriber: str

class HealthcarePersona(BaseModel):
    name: str
    member_id: str
    date_of_birth: str
    primary_care_provider: str

    # Coverage
    plan_name: str
    deductible: float
    deductible_met: float
    out_of_pocket_max: float
    out_of_pocket_spent: float

    # Care
    upcoming_appointments: list[Appointment]
    active_prescriptions: list[Prescription]

    # Recent
    last_visit: str
    last_claim_amount: float
```

## State of the Art (2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded demo data | Seeded generation | 2020+ | Infinite unique demos, no data maintenance |
| `Faker.seed()` class method | `seed_instance()` per-Faker | Faker 2.0.4 | Required for multi-tenant/multi-session |
| pydantic-factories | polyfactory | 2023 | Broader model support, but seeding bugs remain |
| Global WebSocket state | Per-connection state objects | FastAPI best practices | Essential for production multi-user |

**Deprecated/outdated:**
- `fake.seed(n)` instance method: Raises TypeError in Faker 2.0.4+, use `Faker.seed(n)` or `fake.seed_instance(n)`
- Mimesis builtin providers: Dropped in v19.0.0, must use separate provider packages

**Current best practices:**
- Faker remains the standard for Python fake data (40M+ downloads/month)
- Always use `seed_instance()` not class-level `Faker.seed()` for multi-session apps
- Pydantic V2 models for schema validation and JSON serialization
- Session state as dataclass/TypedDict, not scattered globals

## Open Questions

Things that couldn't be fully resolved:

1. **Avatar/Profile Image Generation**
   - What we know: No built-in Faker provider for avatar URLs
   - What's unclear: Best approach for demo avatar images
   - Recommendation: Use deterministic avatar services like `ui-avatars.com/api/?name=John+Doe&background=random` or `robohash.org/{seed}` keyed on persona name/seed

2. **Realistic Transaction History Dates**
   - What we know: `fake.date_between()` generates random dates in range
   - What's unclear: Best pattern for realistic transaction cadence (more recent = more frequent)
   - Recommendation: Weight transaction dates toward recent using exponential distribution, not uniform

3. **Cross-Mode Persona Persistence**
   - What we know: Requirement says "switch modes, get a new persona"
   - What's unclear: Should same session switching back to banking get same banking persona?
   - Recommendation: Generate new persona on each mode switch (simplest). If persistence needed, key on `(session_id, mode_id)` tuple.

## Sources

### Primary (HIGH confidence)
- Faker documentation: https://faker.readthedocs.io/en/master/
  - fakerclass seeding: https://faker.readthedocs.io/en/master/fakerclass.html
  - Bank provider: https://faker.readthedocs.io/en/master/providers/faker.providers.bank.html
  - Credit card provider: https://faker.readthedocs.io/en/master/providers/faker.providers.credit_card.html
  - Profile provider: https://faker.readthedocs.io/en/master/providers/faker.providers.profile.html
- FastAPI WebSocket documentation: https://fastapi.tiangolo.com/advanced/websockets/

### Secondary (MEDIUM confidence)
- Polyfactory GitHub: https://github.com/litestar-org/polyfactory (seeding behavior issues documented)
- Mimesis comparison: https://mimesis.name/ (performance benchmarks)
- FastAPI session patterns: https://hexshift.medium.com/managing-per-user-websocket-state-in-fastapi-9ceaa2b312ac

### Tertiary (LOW confidence, patterns inferred)
- Synthetic insurance data patterns: https://medium.com/gft-engineering/towards-generating-realistic-synthetic-insurance-data-78bdd717d9a8
- Healthcare synthetic data: Synthea project (https://synthetichealth.github.io/synthea/) - Java-based, not directly usable but good for schema inspiration

## Metadata

**Confidence breakdown:**
- Standard stack (Faker): HIGH - Official documentation verified, 40M+ downloads
- Seeding mechanism: HIGH - Official documentation, tested patterns
- Industry schemas: MEDIUM - Based on common patterns, not verified against production systems
- Session state patterns: MEDIUM - FastAPI community patterns, not official docs

**Research date:** 2026-01-18
**Valid until:** 2026-03-18 (60 days - Faker is stable, patterns unlikely to change)
