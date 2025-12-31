"""initial create tables
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use SQLModel metadata creation to ensure consistency
    from utils.db import engine
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)


def downgrade():
    from utils.db import engine
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
