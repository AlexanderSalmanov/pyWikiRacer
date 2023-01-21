from sqlalchemy.orm import declarative_base, sessionmaker 
from sqlalchemy import create_engine 
from sqlalchemy_utils import database_exists, create_database 

Base = declarative_base()

def get_engine():
    url = f"postgresql://postgres:postgres@localhost:5433/wikiracedb"   # connecting to a different port to avoid confilicts with local psql
    if not database_exists(url):
        create_database(url)
    engine = create_engine(url, echo=True)
    return engine 

engine = get_engine()

SessionLocal = sessionmaker(bind=engine)