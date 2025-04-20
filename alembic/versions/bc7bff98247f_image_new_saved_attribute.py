"""Image - New saved attribute 

Revision ID: bc7bff98247f
Revises: 8031042b2442
Create Date: 2025-04-20 15:09:19.883020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc7bff98247f'
down_revision: Union[str, None] = '8031042b2442'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
