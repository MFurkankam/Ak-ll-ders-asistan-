"""add unique constraint for class code
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0002_add_unique_class_code'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("class") as batch_op:
        batch_op.create_unique_constraint("uq_class_code", ["code"])


def downgrade():
    with op.batch_alter_table("class") as batch_op:
        batch_op.drop_constraint("uq_class_code", type_="unique")
