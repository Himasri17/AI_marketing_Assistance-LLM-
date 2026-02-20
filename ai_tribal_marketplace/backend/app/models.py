from sqlalchemy import Column, Integer, String, Text
from .database import Base


class Product(Base):
    __tablename__ = "products"

    id        = Column(Integer, primary_key=True, index=True)

    # ── NEW columns (add to your existing model) ──────────────────────────
    art_name  = Column(String(255), nullable=True)   # e.g. "Warli Wedding Dance"
    art_style = Column(String(255), nullable=True)   # e.g. "Warli"
    region    = Column(String(255), nullable=True)   # e.g. "Maharashtra"
    question  = Column(Text,        nullable=True)   # scholar question (NULL for creator)
    # ──────────────────────────────────────────────────────────────────────

    # existing columns
    english = Column(Text, nullable=False, unique=True)
    hindi   = Column(Text, nullable=True)
    marathi = Column(Text, nullable=True)
    bengali = Column(Text, nullable=True)
    tamil   = Column(Text, nullable=True)
    telugu  = Column(Text, nullable=True)


# ============================================================
# MIGRATION (Alembic)
# ============================================================
# If you use Alembic run:
#
#   alembic revision --autogenerate -m "add art_name art_style region question"
#   alembic upgrade head
#
# If you use raw SQL, add columns manually:
#
#   ALTER TABLE products ADD COLUMN art_name  VARCHAR(255);
#   ALTER TABLE products ADD COLUMN art_style VARCHAR(255);
#   ALTER TABLE products ADD COLUMN region    VARCHAR(255);
#   ALTER TABLE products ADD COLUMN question  TEXT;
#
# ============================================================