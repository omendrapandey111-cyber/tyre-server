import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

#Postgres database
POSTGRES_URL = os.getenv("POSTGRES_URL")
if not POSTGRES_URL:
    raise ValueError("POSTGRES_URL environment variable is not set")

engine_main = create_engine(POSTGRES_URL, pool_pre_ping=True)
SessionLocalMain = sessionmaker(bind=engine_main, autoflush=False, autocommit=False)

#tyre database
TYRE_DATABASE_URL = os.getenv("TYRE_DATABASE_URL")
if not TYRE_DATABASE_URL:
    raise ValueError("TYRE_DATABASE_URL environment variable is not set")

engine_tyre = create_engine(TYRE_DATABASE_URL, pool_pre_ping=True)
SessionLocalTyre = sessionmaker(bind=engine_tyre, autoflush=False, autocommit=False)

Base = declarative_base()