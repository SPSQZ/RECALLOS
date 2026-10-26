from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

database_url = "sqlite:///./recallos.db"
engine = create_engine(
    database_url,connect_args={"check_same_thread":False}
)

sessionlocal = sessionmaker(
    autoflush=False,
    bind= engine,
    expire_on_commit=False
)

Base = declarative_base()