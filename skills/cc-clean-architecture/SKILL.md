---
name: cc-clean-architecture
description: >
  Clean Architecture principles — dependency direction, entity design, use case
  isolation, boundary definition. Use when designing systems, reviewing structure,
  or refactoring toward better separation of concerns.
  TRIGGER: 'architecture', 'layer design', 'structure this', 'boundary', '架构设计', '分层'.
---

# Clean Architecture — Python Edition

Based on Robert C. Martin's principles, adapted for Python projects.

## The Dependency Rule

```
Outer layers depend on inner layers. Never the reverse.

┌─────────────────────────────────────┐
│  Frameworks & Drivers               │ ← FastAPI, SQLAlchemy, Redis
│  ┌─────────────────────────────┐    │
│  │  Interface Adapters          │   │ ← Controllers, Repositories, Presenters
│  │  ┌─────────────────────┐    │   │
│  │  │  Use Cases           │   │   │ ← Application business rules
│  │  │  ┌─────────────┐    │   │   │
│  │  │  │  Entities     │   │   │   │ ← Enterprise business rules
│  │  │  └─────────────┘    │   │   │
│  │  └─────────────────────┘    │   │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

**Rule: Source code dependencies point INWARD only.**

## Python Project Layout

```
src/myapp/
├── domain/                  # Entities (innermost — no imports from outer layers)
│   ├── models.py            # Pure business objects (dataclasses, no ORM)
│   ├── value_objects.py     # Email, Money, UserId
│   └── exceptions.py        # Domain exceptions
├── use_cases/               # Application business rules
│   ├── create_user.py       # One file per use case
│   ├── process_payment.py
│   └── ports.py             # Abstract interfaces (Protocol classes)
├── adapters/                # Interface adapters
│   ├── repositories/        # DB implementations of ports
│   │   └── sqlalchemy_user_repo.py
│   ├── api/                 # FastAPI routes (thin controllers)
│   │   └── user_routes.py
│   └── external/            # Third-party service clients
│       └── stripe_client.py
└── infrastructure/          # Frameworks & drivers
    ├── database.py          # SQLAlchemy engine, session
    ├── config.py            # pydantic-settings
    └── container.py         # Dependency injection setup
```

## Top 10 Rules

### 1. Dependencies Point Inward Only
```python
# domain/models.py — NEVER imports from adapters or infrastructure
@dataclass
class User:
    id: str
    email: str
    name: str
```

### 2. Entities Are Pure Business Logic
```python
# domain/models.py — no ORM, no framework, no I/O
@dataclass
class Order:
    items: list[OrderItem]
    status: OrderStatus

    def total(self) -> Decimal:
        return sum(item.subtotal() for item in self.items)

    def can_cancel(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED)
```

### 3. Use Cases Define Ports (Interfaces)
```python
# use_cases/ports.py
from typing import Protocol

class UserRepository(Protocol):
    async def get(self, user_id: str) -> User | None: ...
    async def save(self, user: User) -> None: ...

class PaymentGateway(Protocol):
    async def charge(self, amount: Decimal, token: str) -> PaymentResult: ...
```

### 4. Use Cases Orchestrate, Don't Implement
```python
# use_cases/create_user.py
class CreateUser:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher):
        self.repo = repo
        self.hasher = hasher

    async def execute(self, email: str, password: str) -> User:
        if await self.repo.get_by_email(email):
            raise UserAlreadyExists(email)
        user = User(id=generate_id(), email=email, password_hash=self.hasher.hash(password))
        await self.repo.save(user)
        return user
```

### 5. Controllers Are Thin
```python
# adapters/api/user_routes.py
@router.post("/users", status_code=201)
async def create_user(data: UserCreateRequest, use_case: CreateUser = Depends()):
    user = await use_case.execute(data.email, data.password)
    return UserResponse.from_domain(user)
```

### 6. Cross Boundaries with Simple Data
```python
# Use dataclasses/Pydantic at boundaries, not domain objects
class UserResponse(BaseModel):
    id: str
    email: str

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email)
```

### 7. Defer Framework Decisions
Database, web framework, cache — these are details. The domain doesn't know about them.

### 8. Test Without Infrastructure
```python
# Test use case with fake repository (no DB needed)
class FakeUserRepo:
    def __init__(self): self.users = {}
    async def save(self, user): self.users[user.id] = user
    async def get(self, id): return self.users.get(id)

async def test_create_user():
    repo = FakeUserRepo()
    use_case = CreateUser(repo, FakeHasher())
    user = await use_case.execute("test@example.com", "password")
    assert user.email == "test@example.com"
```

### 9. No Circular Dependencies
If A depends on B and B depends on A → introduce an interface.

### 10. Screaming Architecture
Directory structure should scream the domain (`orders/`, `users/`, `payments/`), not the framework (`controllers/`, `models/`, `views/`).

## When to Apply Full Clean Architecture

| Project Size | Recommendation |
|-------------|---------------|
| Script/CLI tool | Skip — overkill |
| Small API (< 10 endpoints) | Partial — separate domain from adapters |
| Medium service | Yes — full layer separation |
| Large system / microservices | Essential |

## Violation Detection Checklist

Run these to find architecture violations:

```bash
# Domain importing from adapters/infrastructure (VIOLATION)
grep -rn "from.*adapters\|from.*infrastructure\|import.*fastapi\|import.*sqlalchemy" src/domain/

# Use cases importing from infrastructure (VIOLATION)
grep -rn "from.*infrastructure\|import.*sqlalchemy\|import.*redis" src/use_cases/

# Circular dependencies
grep -rn "from.*domain" src/adapters/ | grep -v "models\|exceptions\|value_objects"

# Controllers doing business logic (VIOLATION — should be thin)
# Look for files > 50 lines in api/
wc -l src/adapters/api/*.py | sort -rn | head -5
```

**Clean result:** zero matches on violations, all API files < 50 lines.

## Testing Strategy Per Layer

| Layer | Test Type | Dependencies | Speed |
|-------|-----------|-------------|-------|
| **Domain** | Unit | None (pure logic) | < 1ms |
| **Use Cases** | Unit | Fake repos (in-memory) | < 5ms |
| **Adapters** | Integration | Real DB / test containers | < 500ms |
| **Infrastructure** | E2E | Full stack | < 2s |

## Related Skills

- **cc-fastapi** — adapter layer patterns (routes, deps, middleware)
- **cc-database** — repository implementations
- **cc-python-patterns** — Python idioms within each layer
- **cc-error-handling** — domain exceptions vs adapter exceptions
- **cc-research** — use to map architecture before refactoring
