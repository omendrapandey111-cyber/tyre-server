"""office and place relation added

Revision ID: 4f05f92d4e62
Revises: 
Create Date: 2026-04-02 11:47:19.851039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f05f92d4e62'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""

    # ✅ Step 1: Create PLACES first (NO FK yet)
    op.create_table(
        'places',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('short_name', sa.String(), nullable=True),
        sa.Column('controlling_office_name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # ✅ Step 2: Create OFFICES (can reference places now)
    op.create_table(
        'offices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('gstin', sa.String(), nullable=True),
        sa.Column('address_line1', sa.String(), nullable=True),
        sa.Column('address_line2', sa.String(), nullable=True),
        sa.Column('place_name', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gstin'),
        sa.UniqueConstraint('name'),

        # ✅ FK to places
        sa.ForeignKeyConstraint(['place_name'], ['places.name']),
    )

    op.create_index(op.f('ix_offices_id'), 'offices', ['id'], unique=False)

    # ✅ Step 3: Add FK from places → offices (AFTER both exist)
    op.create_foreign_key(
        'fk_places_office_name',
        'places',
        'offices',
        ['controlling_office_name'],
        ['name']
    )

    # existing FK
    op.create_foreign_key(
        None,
        'new_grn',
        'offices',
        ['office_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(None, 'new_grn', type_='foreignkey')

    op.drop_constraint('fk_places_office_name', 'places', type_='foreignkey')

    op.drop_index(op.f('ix_offices_id'), table_name='offices')

    op.drop_table('offices')
    op.drop_table('places')
