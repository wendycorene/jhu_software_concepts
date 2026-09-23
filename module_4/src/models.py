"""SQLAlchemy 2.x mapping of the same table populated by load_data.py."""
from sqlalchemy import Column, Integer, Text, Date, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import sqlalchemy_url

class Base(DeclarativeBase):
    pass

class Applicant(Base):
    __tablename__ = 'applicants'
    p_id = Column(Integer, primary_key=True)
    program = Column(Text)
    comments = Column(Text)
    date_added = Column(Date)
    url = Column(Text, unique=True)
    status = Column(Text)
    term = Column(Text)
    us_or_international = Column(Text)
    gpa = Column(Float)
    gre = Column(Float)
    gre_v = Column(Float)
    gre_aw = Column(Float)
    degree = Column(Text)
    llm_generated_program = Column(Text)
    llm_generated_university = Column(Text)

engine = create_engine(sqlalchemy_url(), pool_pre_ping=True)
Session = sessionmaker(bind=engine)
