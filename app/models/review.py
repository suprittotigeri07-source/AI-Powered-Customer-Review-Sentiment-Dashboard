from datetime import datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    product: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    review_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED", index=True)
    flagged: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="reviews")
    sentiment = relationship("SentimentResult", back_populates="review", uselist=False, cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="review", cascade="all, delete-orphan")
