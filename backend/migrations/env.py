import sys
from os.path import abspath, dirname
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Ajout du chemin racine pour permettre les imports de 'app'
sys.path.insert(0, abspath(dirname(dirname(__file__))))

# 2. Import de tes composants Harmony
from app.core.config import settings
from app.core.database import Base
# Import des modèles pour que Base.metadata soit peuplé
from app.shared.models import ( 
    User, CrewProfile, EmployerProfile, UserDocument, Yacht, CrewAssignment,
    TestCatalogue, Question, TestResult,
    Campaign, CampaignCandidate,
    DailyPulse,
    Survey, SurveyResponse, RecruitmentEvent, ModelVersion
    )

# Objet de configuration Alembic
config = context.config

# 3. Injection dynamique de l'URL (Sync au lieu de Async)
# Alembic a besoin de postgresql:// et non postgresql+asyncpg://
sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Définition de la cible des métadonnées
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Mode offline : génère des scripts SQL sans connexion directe."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Mode online : exécute les migrations sur la base de données."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
