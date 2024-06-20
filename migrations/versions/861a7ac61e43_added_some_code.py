"""Added some code

Revision ID: 861a7ac61e43
Revises: 
Create Date: 2024-06-20 17:51:13.450218

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '861a7ac61e43'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('wastecollection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('waste_type', sa.Integer(), nullable=False))
        batch_op.drop_constraint('wastecollection_ibfk_2', type_='foreignkey')
        batch_op.create_foreign_key(None, 'wastetype', ['waste_type'], ['id'])
        batch_op.drop_column('waste_type_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('wastecollection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('waste_type_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('wastecollection_ibfk_2', 'wastetype', ['waste_type_id'], ['id'])
        batch_op.drop_column('waste_type')

    # ### end Alembic commands ###