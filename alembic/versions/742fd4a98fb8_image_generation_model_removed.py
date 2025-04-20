"""Image - Generation model removed

Revision ID: 742fd4a98fb8
Revises: bc7bff98247f
Create Date: 2025-04-20 15:13:43.991260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '742fd4a98fb8'
down_revision: Union[str, None] = 'bc7bff98247f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
