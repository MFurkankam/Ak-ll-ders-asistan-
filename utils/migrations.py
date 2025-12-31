from alembic.config import Config
from alembic import command
import os


def upgrade_head():
    # programmatically run `alembic upgrade head`
    cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    # Ensure SQLAlchemy URL uses env DATABASE_URL if set
    if os.getenv('DATABASE_URL'):
        cfg.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))
    command.upgrade(cfg, 'head')


def downgrade_base():
    cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    command.downgrade(cfg, 'base')
