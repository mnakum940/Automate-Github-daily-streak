# FastAPI REST API Project Template

## Project Structure
```
{project_name}/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # Pydantic models
│   ├── database.py       # Database connection
│   ├── crud.py           # CRUD operations
│   └── routers/
│       ├── __init__.py
│       └── items.py      # API routes
├── tests/
│   ├── __init__.py
│   └── test_api.py
└── alembic/              # Database migrations
    └── versions/
```

## Technologies
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL/SQLite
- Pydantic
- pytest

## Difficulty
Beginner to Intermediate

## README Template
```markdown
# {project_name}

A RESTful API built with FastAPI for {api_purpose}.

## Features
- ✅ CRUD operations
- ✅ Database integration (SQLAlchemy)
- ✅ Request/response validation (Pydantic)
- ✅ Automatic OpenAPI documentation
- ✅ Authentication (JWT)
- ✅ Unit tests with pytest

## Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL/SQLite
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Testing**: pytest

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:
```
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key-here
```

## Running

```bash
# Development server
uvicorn app.main:app --reload

# Access API documentation
open http://localhost:8000/docs
```

## API Endpoints

### Items
- `GET /items/` - List all items
- `GET /items/{id}` - Get item by ID
- `POST /items/` - Create new item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

## Testing

```bash
pytest tests/ -v
```

## License
MIT License
```

## Code Templates

### requirements.txt
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pytest>=7.4.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

### app/main.py
```python
"""
FastAPI Application - {project_name}
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import items

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="{project_name}",
    description="{api_description}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(items.router, prefix="/api/v1", tags=["items"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to {project_name} API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

### app/database.py
```python
"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency for getting database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/models.py
```python
"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    """Base item schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    is_available: bool = True


class ItemCreate(ItemBase):
    """Schema for creating an item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### app/routers/items.py
```python
"""
Items router - CRUD endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ItemCreate, ItemUpdate, ItemResponse
from app import crud

router = APIRouter()


@router.get("/items", response_model=List[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve list of items.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        db: Database session
        
    Returns:
        List of items
    """
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get item by ID.
    
    Args:
        item_id: Item ID
        db: Database session
        
    Returns:
        Item details
        
    Raises:
        HTTPException: If item not found
    """
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    return item


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """
    Create new item.
    
    Args:
        item: Item data
        db: Database session
        
    Returns:
        Created item
    """
    return crud.create_item(db, item)


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing item.
    
    Args:
        item_id: Item ID
        item: Updated item data
        db: Database session
        
    Returns:
        Updated item
        
    Raises:
        HTTPException: If item not found
    """
    updated_item = crud.update_item(db, item_id, item)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    return updated_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete item.
    
    Args:
        item_id: Item ID
        db: Database session
        
    Raises:
        HTTPException: If item not found
    """
    success = crud.delete_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
```

### tests/test_api.py
```python
"""
API endpoint tests
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_item():
    """Test creating an item."""
    item_data = {
        "name": "Test Item",
        "description": "Test description",
        "price": 9.99,
        "is_available": True
    }
    response = client.post("/api/v1/items", json=item_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"


def test_get_items():
    """Test getting list of items."""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Commit Strategy
1. **Initial commit**: Project structure + FastAPI setup + database config
2. **Implementation commit**: CRUD operations + API endpoints
3. **Testing commit**: Unit tests + documentation + .env.example
