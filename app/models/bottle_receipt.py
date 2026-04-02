from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BottleReceipt(Base):
    __tablename__ = "bottle_receipts"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_bottle_receipts_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(
        ForeignKey("admins.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    admin = relationship("Admin", back_populates="bottle_receipts")

    def __repr__(self):
        return f"<BottleReceipt {self.id}: {self.quantity} bottles>"
