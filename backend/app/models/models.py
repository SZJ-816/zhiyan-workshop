"""禅道系统数据模型 - 用户/部门/产品/需求/项目/任务/Bug"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum as SAEnum, Boolean, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PM = "pm"  # 项目经理
    DEV = "dev"  # 开发
    QA = "qa"  # 测试
    PO = "po"  # 产品负责人

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"
    CLOSED = "closed"
    PAUSED = "paused"

class TaskPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BugSeverity(str, enum.Enum):
    FATAL = "fatal"
    SERIOUS = "serious"
    NORMAL = "normal"
    MINOR = "minor"
    SUGGESTION = "suggestion"

class BugStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CLOSED = "closed"

class StoryStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEVELOPING = "developing"
    TESTING = "testing"
    DONE = "done"
    CLOSED = "closed"

class ProjectStatus(str, enum.Enum):
    WAITING = "waiting"
    DOING = "doing"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    DONE = "done"

class Department(Base):
    __tablename__ = "zt_department"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(60), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("zt_department.id"), nullable=True, default=None)
    sort = Column(Integer, default=0)
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "zt_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(30), nullable=False, unique=True, index=True)
    realname = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="dev")
    email = Column(String(100))
    phone = Column(String(20))
    department_id = Column(Integer, ForeignKey("zt_department.id"), default=0)
    avatar_color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    department = relationship("Department", back_populates="users")
    tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")
    bugs = relationship("Bug", back_populates="assignee", foreign_keys="Bug.assigned_to")

class Product(Base):
    __tablename__ = "zt_product"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    status = Column(String(20), default="active")
    created_by = Column(Integer, ForeignKey("zt_user.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    stories = relationship("Story", back_populates="product")
    bugs = relationship("Bug", back_populates="product")

class Story(Base):
    __tablename__ = "zt_story"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    product_id = Column(Integer, ForeignKey("zt_product.id"), nullable=False)
    status = Column(String(20), default="draft")
    priority = Column(Integer, default=3)
    estimate = Column(Float, default=0)
    created_by = Column(Integer, ForeignKey("zt_user.id"))
    assigned_to = Column(Integer, ForeignKey("zt_user.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    product = relationship("Product", back_populates="stories")

class Project(Base):
    __tablename__ = "zt_project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default="waiting")
    pm_id = Column(Integer, ForeignKey("zt_user.id"))
    product_id = Column(Integer, ForeignKey("zt_product.id"))
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "zt_task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("zt_project.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("zt_user.id"))
    status = Column(String(20), default="todo")
    priority = Column(String(10), default="medium")
    estimate = Column(Float, default=0)  # 预估工时(小时)
    consumed = Column(Float, default=0)  # 已耗工时
    start_date = Column(Date)
    deadline = Column(Date)
    finished_date = Column(DateTime)
    story_id = Column(Integer, ForeignKey("zt_story.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])

class Bug(Base):
    __tablename__ = "zt_bug"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(Text)
    product_id = Column(Integer, ForeignKey("zt_product.id"))
    project_id = Column(Integer, ForeignKey("zt_project.id"))
    severity = Column(String(20), default="normal")
    priority = Column(Integer, default=3)
    status = Column(String(20), default="active")
    assigned_to = Column(Integer, ForeignKey("zt_user.id"))
    created_by = Column(Integer, ForeignKey("zt_user.id"))
    resolved_build = Column(String(50))
    resolution = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    product = relationship("Product", back_populates="bugs")
    assignee = relationship("User", back_populates="bugs", foreign_keys=[assigned_to])

class Activity(Base):
    __tablename__ = "zt_activity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("zt_user.id"))
    action = Column(String(50), nullable=False)
    object_type = Column(String(30))
    object_id = Column(Integer)
    object_name = Column(String(255))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
