from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BottleReturn(Base):
    __tablename__ = "bottle_returns"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_bottle_returns_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    admin_id: Mapped[int] = mapped_column(
        ForeignKey("admins.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    returned_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    customer = relationship("Customer", back_populates="bottle_returns")
    admin = relationship("Admin", back_populates="bottle_returns")

    def __repr__(self):
        return f"<BottleReturn {self.id}: {self.quantity} bottles>"
