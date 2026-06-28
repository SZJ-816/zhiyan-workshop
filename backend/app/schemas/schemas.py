"""API请求/响应模型"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

# ===== Auth =====
class LoginRequest(BaseModel):
    account: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# ===== User =====
class UserOut(BaseModel):
    id: int
    account: str
    realname: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: int
    avatar_color: str
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class UserCreate(BaseModel):
    account: str
    realname: str
    password: str
    role: str = "dev"
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: int = 0

class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: int
    sort: int
    class Config: from_attributes = True

class DepartmentCreate(BaseModel):
    name: str
    parent_id: int = 0

# ===== Product =====
class ProductOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class ProductCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

# ===== Story =====
class StoryOut(BaseModel):
    id: int
    title: str
    status: str
    priority: int
    estimate: float
    product_id: int
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class StoryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    product_id: int
    priority: int = 3
    estimate: float = 0
    assigned_to: Optional[int] = None

# ===== Project =====
class ProjectOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    pm_id: Optional[int] = None
    progress: float
    product_id: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pm_id: Optional[int] = None
    product_id: Optional[int] = None

# ===== Task =====
class TaskOut(BaseModel):
    id: int
    name: str
    project_id: int
    assigned_to: Optional[int] = None
    status: str
    priority: str
    estimate: float
    consumed: float
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    finished_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None  # 由 URL 路径 /api/projects/{project_id}/tasks 传入
    assigned_to: Optional[int] = None
    priority: str = "medium"
    estimate: float = 0
    deadline: Optional[date] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    consumed: Optional[float] = None
    description: Optional[str] = None

# ===== Bug =====
class BugOut(BaseModel):
    id: int
    title: str
    severity: str
    priority: int
    status: str
    product_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class BugCreate(BaseModel):
    title: str
    description: Optional[str] = None
    steps: Optional[str] = None
    product_id: Optional[int] = None
    project_id: Optional[int] = None
    severity: str = "normal"
    priority: int = 3
    assigned_to: Optional[int] = None

# ===== Activity =====
class ActivityOut(BaseModel):
    id: int
    user_id: int
    action: str
    object_type: Optional[str] = None
    object_name: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

# ===== Dashboard Stats =====
class DashboardStats(BaseModel):
    total_projects: int = 0
    total_tasks: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    total_bugs: int = 0
    active_bugs: int = 0
    resolved_bugs: int = 0
    total_stories: int = 0
    active_stories: int = 0
    total_users: int = 0
    project_progress: List[dict] = []
    task_distribution: dict = {}
    bug_severity: dict = {}
    weekly_completed: List[dict] = []

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
