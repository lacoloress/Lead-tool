"""Leads service for CRUD operations with CSV storage."""

import uuid
from datetime import datetime
from pathlib import Path

import polars as pl

from lead_tool.config import settings
from lead_tool.models import Analysis, Lead
from lead_tool.services.analyzer import CompanyAnalyzer


class LeadsService:
    """Service for managing leads with CSV persistence."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.data_dir
        self.leads_file = self.data_dir / "leads.csv"
        self.analyzer = CompanyAnalyzer()
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_leads(self) -> pl.DataFrame:
        """Load leads from CSV file."""
        if not self.leads_file.exists():
            return pl.DataFrame(schema=self._get_schema())
        return pl.read_csv(self.leads_file)

    def _save_leads(self, df: pl.DataFrame) -> None:
        """Save leads to CSV file."""
        df.write_csv(self.leads_file)

    def _get_schema(self) -> dict:
        """Get the DataFrame schema for leads."""
        return {
            "id": pl.Utf8,
            "name": pl.Utf8,
            "email": pl.Utf8,
            "company": pl.Utf8,
            "position": pl.Utf8,
            "linkedin_url": pl.Utf8,
            "company_website": pl.Utf8,
            "location": pl.Utf8,
            "phone": pl.Utf8,
            "score": pl.Int32,
            "tier": pl.Utf8,
            "category": pl.Utf8,
            "insights": pl.Utf8,  # JSON string
            "qualified": pl.Boolean,
            "source": pl.Utf8,
            "email_verified": pl.Boolean,
            "created_at": pl.Utf8,
        }

    def get_all(self) -> list[Lead]:
        """Get all leads."""
        df = self._load_leads()
        return self._df_to_leads(df)

    def get_by_id(self, lead_id: str) -> Lead | None:
        """Get a lead by ID."""
        df = self._load_leads()
        filtered = df.filter(pl.col("id") == lead_id)
        if filtered.is_empty():
            return None
        leads = self._df_to_leads(filtered)
        return leads[0] if leads else None

    def add(self, lead: Lead) -> Lead:
        """Add a new lead."""
        df = self._load_leads()
        new_row = self._lead_to_row(lead)
        new_df = pl.concat([df, pl.DataFrame([new_row])])
        self._save_leads(new_df)
        return lead

    def add_many(self, leads: list[Lead]) -> list[Lead]:
        """Add multiple leads."""
        if not leads:
            return []
        df = self._load_leads()
        rows = [self._lead_to_row(lead) for lead in leads]
        new_df = pl.concat([df, pl.DataFrame(rows)])
        self._save_leads(new_df)
        return leads

    def delete(self, lead_id: str) -> bool:
        """Delete a lead by ID."""
        df = self._load_leads()
        new_df = df.filter(pl.col("id") != lead_id)
        if len(new_df) == len(df):
            return False
        self._save_leads(new_df)
        return True

    def clear(self) -> int:
        """Clear all leads. Returns count of deleted leads."""
        df = self._load_leads()
        count = len(df)
        self._save_leads(pl.DataFrame(schema=self._get_schema()))
        return count

    def import_csv(self, file_path: Path) -> list[Lead]:
        """Import leads from an uploaded CSV file."""
        import_df = pl.read_csv(file_path)

        leads: list[Lead] = []
        for row in import_df.iter_rows(named=True):
            analysis = self.analyzer.analyze(
                industry=row.get("industry", ""),
                size=row.get("company_size", ""),
                revenue=row.get("revenue", ""),
            )
            lead = Lead(
                id=str(uuid.uuid4()),
                name=row.get("name", ""),
                email=row.get("email", ""),
                company=row.get("company", ""),
                position=row.get("position", ""),
                linkedin_url=row.get("linkedin_url", ""),
                company_website=row.get("company_website", ""),
                location=row.get("location", ""),
                phone=row.get("phone", ""),
                analysis=analysis,
                source="csv_upload",
                email_verified=False,
                created_at=datetime.utcnow(),
            )
            leads.append(lead)

        return self.add_many(leads)

    def export_csv(self, output_path: Path) -> Path:
        """Export leads to a CSV file."""
        df = self._load_leads()
        df.write_csv(output_path)
        return output_path

    def _lead_to_row(self, lead: Lead) -> dict:
        """Convert a Lead to a row dict."""
        import json

        return {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "position": lead.position,
            "linkedin_url": lead.linkedin_url,
            "company_website": lead.company_website,
            "location": lead.location,
            "phone": lead.phone,
            "score": lead.analysis.score,
            "tier": lead.analysis.tier.value,
            "category": lead.analysis.category.value,
            "insights": json.dumps(lead.analysis.insights),
            "qualified": lead.analysis.qualified,
            "source": lead.source,
            "email_verified": lead.email_verified,
            "created_at": lead.created_at.isoformat(),
        }

    def _df_to_leads(self, df: pl.DataFrame) -> list[Lead]:
        """Convert DataFrame rows to Lead objects."""
        import json

        from lead_tool.models import Category, Tier

        leads: list[Lead] = []
        for row in df.iter_rows(named=True):
            analysis = Analysis(
                score=row["score"],
                tier=Tier(row["tier"]),
                category=Category(row["category"]),
                insights=json.loads(row["insights"]) if row["insights"] else [],
                qualified=row["qualified"],
            )
            lead = Lead(
                id=row["id"],
                name=row["name"],
                email=row["email"] or "",
                company=row["company"] or "",
                position=row["position"] or "",
                linkedin_url=row["linkedin_url"] or "",
                company_website=row["company_website"] or "",
                location=row["location"] or "",
                phone=row["phone"] or "",
                analysis=analysis,
                source=row["source"],
                email_verified=row["email_verified"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            leads.append(lead)
        return leads
