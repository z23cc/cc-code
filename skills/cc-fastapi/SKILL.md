---
name: cc-fastapi
description: >
  FastAPI patterns — route design, Pydantic models, dependency injection, error handling, auth, pagination.
  TRIGGER: 'fastapi', 'API', 'endpoint', 'route', 'FastAPI', 'API接口'.
  FLOWS INTO: cc-tdd, cc-security-review.
---

# FastAPI Patterns

## Project Structure

```
src/app/
├── main.py              # App factory, lifespan, middleware
├── api/
│   ├── deps.py          # Shared dependencies (get_db, get_current_user)
│   ├── users.py         # /users endpoints
│   └── items.py         # /items endpoints
├── models/
│   ├── user.py          # SQLAlchemy models
│   └── item.py
├── schemas/
│   ├── user.py          # Pydantic request/response schemas
│   └── item.py
├── services/
│   ├── user_service.py  # Business logic
│   └── item_service.py
└── core/
    ├── config.py        # Settings (pydantic-settings)
    ├── security.py      # JWT, password hashing
    └── exceptions.py    # Custom error handlers
```

## Pydantic Schemas (Request/Response)

```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# Base → Create → Update → Response pattern
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# Paginated response
class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
```

## CRUD Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await user_exists(db, data.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user_in_db(db, data)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
```

## Dependency Injection

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return user
```

## Pagination

```python
async def paginate(
    db: AsyncSession,
    query,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = await db.scalars(query.offset((page - 1) * per_page).limit(per_page))
    return PaginatedResponse(
        items=list(items),
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )
```

## Error Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, status_code: int, detail: str, **context):
        self.status_code = status_code
        self.detail = detail
        self.context = context

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": type(exc).__name__},
    )

# Standard error response format
# 400: {"detail": "Validation error", "errors": [...]}
# 401: {"detail": "Not authenticated"}
# 403: {"detail": "Not authorized"}
# 404: {"detail": "Resource not found"}
# 409: {"detail": "Conflict — resource already exists"}
# 422: Auto-generated by FastAPI for validation errors
# 500: {"detail": "Internal server error"} (never expose stack traces)
```

## Middleware

```python
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Never ["*"] in prod
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest):
    ...
```

## Related Skills

- **cc-async-patterns** — asyncio patterns used throughout FastAPI
- **cc-database** — SQLAlchemy async session, models, queries
- **cc-security-review** — auth checklist, CORS, rate limiting
- **cc-logging** — request/response logging middleware
- **cc-clean-architecture** — layer design (domain/use_cases/adapters) for FastAPI projects
- **cc-prompt-engineering** — integrating LLM calls into API endpoints
- **cc-task-queues** — Celery for background jobs behind API endpoints
- **cc-python-testing** — testing FastAPI with `httpx.AsyncClient`

## E2E Example: Adding an Endpoint

```python
# 1. Schema (schemas/user.py)
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: str
    email: str

# 2. Route (api/users.py)
@router.post("/users", status_code=201, response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.create(data.email, data.password)
    return UserResponse(id=user.id, email=user.email)

# 3. Test (tests/test_users.py)
async def test_create_user(client: AsyncClient):
    resp = await client.post("/users", json={"email": "a@b.com", "password": "12345678"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@b.com"

async def test_create_user_invalid(client: AsyncClient):
    resp = await client.post("/users", json={"email": "bad", "password": "short"})
    assert resp.status_code == 422
```

## Quality Metrics

| Metric | Target | Check |
|--------|--------|-------|
| Response time | < 200ms (p95) | Load test |
| Validation coverage | All inputs validated via Pydantic | No raw dict access |
| Error format | Consistent JSON structure | Custom exception handlers |
| Auth on all endpoints | 0 unprotected mutation routes | Security review |
