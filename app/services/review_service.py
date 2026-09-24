import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.review import Review
from app.models.user import User
from app.services.project_service import ProjectService


REQUIRED_COLUMNS = {"review"}
OPTIONAL_COLUMNS = {"rating", "date", "product", "category", "source", "customer_id"}


class ReviewService:
    def __init__(self, db: Session, projects: ProjectService):
        self.db = db
        self.projects = projects

    def upload_csv(self, user: User, project_id: int, file: UploadFile) -> dict:
        settings = get_settings()
        project = self.projects.get_owned(user, project_id)
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

        raw = file.file.read()
        if len(raw) > settings.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 10MB limit")

        try:
            frame = pd.read_csv(io.BytesIO(raw))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse CSV file: {exc}") from exc

        frame.columns = [str(col).strip().lower() for col in frame.columns]
        if "review" not in frame.columns and "review_text" in frame.columns:
            frame = frame.rename(columns={"review_text": "review"})
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The uploaded CSV is missing the required '{next(iter(missing))}' column.",
            )

        errors = []
        imported = 0
        for index, row in frame.iterrows():
            text = str(row.get("review") or "").strip()
            row_number = int(index) + 2
            if not text or text.lower() == "nan":
                errors.append({"row": row_number, "field": "review", "message": "Review text is empty"})
                continue

            rating = None
            if "rating" in frame.columns and not pd.isna(row.get("rating")):
                try:
                    rating = float(row.get("rating"))
                    if rating < 1 or rating > 5:
                        errors.append({"row": row_number, "field": "rating", "message": "Rating must be between 1 and 5"})
                        continue
                except (TypeError, ValueError):
                    errors.append({"row": row_number, "field": "rating", "message": "Invalid rating"})
                    continue

            review_date = None
            if "date" in frame.columns and not pd.isna(row.get("date")):
                parsed = pd.to_datetime(row.get("date"), errors="coerce")
                if pd.isna(parsed):
                    errors.append({"row": row_number, "field": "date", "message": "Invalid date"})
                    continue
                review_date = parsed.date()

            review = Review(
                project_id=project.id,
                review_text=text,
                rating=rating,
                source=_optional(row, "source"),
                product=_optional(row, "product"),
                category=_optional(row, "category"),
                customer_id=_optional(row, "customer_id"),
                review_date=review_date,
                status="UPLOADED",
            )
            self.db.add(review)
            imported += 1

        self.db.commit()
        total = len(frame)
        return {
            "total_rows": total,
            "valid_rows": imported,
            "invalid_rows": len(errors),
            "imported_rows": imported,
            "errors": errors[:50],
        }


def _optional(row, key: str) -> str | None:
    value = row.get(key) if key in row.index else None
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text and text.lower() != "nan" else None
