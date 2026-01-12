"""Pydantic models for Lead Tool."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Industry(str, Enum):
    """Supported industry values."""

    INFORMATION_TECHNOLOGY = "information_technology"
    COMPUTER_SOFTWARE = "computer_software"
    INTERNET = "internet"
    MARKETING_ADVERTISING = "marketing_advertising"
    MANAGEMENT_CONSULTING = "management_consulting"
    FINANCIAL_SERVICES = "financial_services"
    CONSUMER_SERVICES = "consumer_services"
    HEALTHCARE = "healthcare"
    HEALTH_WELLNESS_FITNESS = "health_wellness_fitness"
    REAL_ESTATE = "real_estate"
    RESTAURANTS = "restaurants"
    RETAIL = "retail"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    MEDIA_PRODUCTION = "media_production"
    DESIGN = "design"
    PROFESSIONAL_TRAINING = "professional_training"
    TRANSPORTATION = "transportation"
    MANUFACTURING = "manufacturing"
    BIOTECHNOLOGY = "biotechnology"
    PHARMACEUTICALS = "pharmaceuticals"
    MEDICAL_DEVICES = "medical_devices"
    E_LEARNING = "e_learning"
    RESEARCH = "research"
    HIGHER_EDUCATION = "higher_education"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    LEGAL_SERVICES = "legal_services"
    ACCOUNTING = "accounting"
    ARCHITECTURE_PLANNING = "architecture_planning"
    CONSTRUCTION = "construction"
    ENGINEERING = "engineering"
    AUTOMOTIVE = "automotive"
    TELECOMMUNICATIONS = "telecommunications"
    INSURANCE = "insurance"
    HOSPITALITY = "hospitality"
    EVENTS_SERVICES = "events_services"


class CompanySize(str, Enum):
    """Company size ranges."""

    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_500 = "201-500"
    SIZE_501_1000 = "501-1000"
    SIZE_1001_5000 = "1001-5000"
    SIZE_5001_10000 = "5001-10000"
    SIZE_10001_PLUS = "10001+"


class FundingStage(str, Enum):
    """Funding stage values."""

    SEED = "seed"
    ANGEL = "angel"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D = "series_d"
    SERIES_E = "series_e"
    SERIES_F = "series_f"
    VENTURE = "venture"
    PRIVATE_EQUITY = "private_equity"


class Tier(str, Enum):
    """Company tier classification."""

    ENTERPRISE = "Enterprise"
    SCALE_UP = "Scale-up"
    STARTUP = "Startup"
    SMALL = "Small"


class Category(str, Enum):
    """Lead category classification."""

    HIGH_VALUE = "High Value"
    MEDIUM_VALUE = "Medium Value"
    STARTUP = "Startup"
    SMALL_BUSINESS = "Small Business"


class Analysis(BaseModel):
    """Lead analysis result."""

    score: int = Field(ge=0, le=100, description="Score from 0-100")
    tier: Tier
    category: Category
    insights: list[str] = Field(default_factory=list)
    qualified: bool = Field(description="True if score >= 50")


class Lead(BaseModel):
    """Lead data model."""

    id: str
    name: str
    email: str = ""
    company: str = ""
    position: str = ""
    linkedin_url: str = ""
    company_website: str = ""
    location: str = ""
    phone: str = ""
    analysis: Analysis
    source: Literal["search", "csv_upload"]
    email_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchParams(BaseModel):
    """Lead search parameters."""

    job_titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    industries: list[Industry] = Field(default_factory=list)
    company_sizes: list[CompanySize] = Field(default_factory=list)
    funding_stages: list[FundingStage] = Field(default_factory=list)
    number_of_leads: int = Field(default=100, ge=1, le=5000)


class ErrorDetail(BaseModel):
    """Error detail for API responses."""

    msg: str
    code: Literal[
        "VALIDATION_ERROR",
        "SCRAPER_ERROR",
        "FILE_ERROR",
        "NOT_FOUND",
        "INTERNAL_ERROR",
    ]


class ApiResponse[T](BaseModel):
    """Standard API response wrapper."""

    status: bool
    data: T | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: ErrorDetail | None = None
