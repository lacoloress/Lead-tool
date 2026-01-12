"""Apify scraper service for LinkedIn lead generation."""

import uuid
from datetime import datetime, timezone
from typing import Any

from apify_client import ApifyClient

from lead_tool.config import settings
from lead_tool.models import Lead, SearchParams
from lead_tool.services.analyzer import CompanyAnalyzer


class ScraperService:
    """Service for scraping leads from LinkedIn via Apify."""

    def __init__(self) -> None:
        self.client = ApifyClient(settings.apify_api_token)
        self.actor_id = settings.apify_actor_id
        self.analyzer = CompanyAnalyzer()

    def search(self, params: SearchParams) -> list[Lead]:
        """
        Search for leads using the configured Apify actor.

        Args:
            params: Search parameters including job titles, locations, etc.

        Returns:
            List of Lead objects with analysis scores.
        """
        # Build actor input based on search params
        actor_input = self._build_actor_input(params)

        # Run the actor and wait for completion
        run = self.client.actor(self.actor_id).call(run_input=actor_input)

        if run is None:
            return []

        # Fetch results from the dataset
        dataset = self.client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        # Convert raw results to Lead objects
        return self._items_to_leads(items)

    def _build_actor_input(self, params: SearchParams) -> dict[str, Any]:
        """
        Build the actor input dictionary from search parameters.

        This method should be customized based on the specific Apify actor being used.
        Common LinkedIn scraper actors expect parameters like:
        - searchUrl or queries
        - maxResults / resultsLimit
        - filters for location, industry, etc.
        """
        return {
            "searchQueries": params.job_titles,
            "locations": params.locations,
            "industries": [i.value for i in params.industries],
            "companySizes": [s.value for s in params.company_sizes],
            "maxResults": params.number_of_leads,
        }

    def _items_to_leads(self, items: list[dict[str, Any]]) -> list[Lead]:
        """
        Convert raw Apify results to Lead objects.

        This method maps the actor's output fields to Lead model fields.
        Field names should be adjusted based on the specific actor's output schema.
        """
        leads: list[Lead] = []

        for item in items:
            # Extract fields with fallbacks for common field name variations
            name = (
                item.get("fullName")
                or item.get("name")
                or item.get("firstName", "") + " " + item.get("lastName", "")
            ).strip()

            if not name:
                continue

            # Analyze the lead based on available company data
            analysis = self.analyzer.analyze(
                industry=item.get("industry", "") or item.get("companyIndustry", ""),
                size=item.get("companySize", "") or item.get("employeeCount", ""),
                revenue=item.get("revenue", "") or item.get("companyRevenue", ""),
            )

            lead = Lead(
                id=str(uuid.uuid4()),
                name=name,
                email=item.get("email", "") or "",
                company=item.get("company", "") or item.get("companyName", "") or "",
                position=item.get("position", "") or item.get("title", "") or item.get("headline", "") or "",
                linkedin_url=item.get("linkedinUrl", "") or item.get("profileUrl", "") or item.get("url", "") or "",
                company_website=item.get("companyWebsite", "") or item.get("website", "") or "",
                location=item.get("location", "") or item.get("city", "") or "",
                phone=item.get("phone", "") or item.get("phoneNumber", "") or "",
                analysis=analysis,
                source="search",
                email_verified=False,
                created_at=datetime.now(timezone.utc),
            )
            leads.append(lead)

        return leads
