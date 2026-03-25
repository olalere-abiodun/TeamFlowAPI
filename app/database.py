import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

sys.path.append(str(Path(__file__).resolve().parent.parent))

load_dotenv()



SQLALCHEMY_DATABASE_URL = os.environ.get('DB_URL')
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("No Database found")


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()