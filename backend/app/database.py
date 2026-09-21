import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Carrega as variáveis do arquivo .env para o ambiente
# (não sobrescreve variáveis já definidas, ex.: nos testes)
load_dotenv()

# Recupera a URL da variável de ambiente
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")

connect_args = {}
engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # :memory: precisa de StaticPool para compartilhar o mesmo DB entre conexões
    if ":memory:" in SQLALCHEMY_DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
