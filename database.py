import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, func

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

# Neon.tech havolasidagi "postgres://" ni asyncpg uchun moslash
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="candidate")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

class Vacancy(Base):
    __tablename__ = "vacancies"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    company_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(100))
    requirements: Mapped[str] = mapped_column(Text)
    salary: Mapped[str] = mapped_column(String(50))
    region: Mapped[str] = mapped_column(String(50))
    work_format: Mapped[str] = mapped_column(String(20), default="offline")
    contact: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(100))
    experience: Mapped[str] = mapped_column(Text)
    education: Mapped[str] = mapped_column(Text)
    about: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
      
