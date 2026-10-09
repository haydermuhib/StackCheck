"""
Data models for StackCheck
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone

from stackcheck.analyzer.currency import currency_manager


class WorkplaceType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    ANY = "any"


class TechCategory(str, Enum):
    PROGRAMMING_LANGUAGES = "Programming Languages"
    BI_DATA_TOOLS = "BI & Visualization"
    DATA_ENGINEERING = "Data Engineering & Platforms"
    DATABASES_STORAGE = "Databases & Storage"
    CLOUD_DEVOPS = "Cloud & DevOps"
    AI_ML = "AI / ML & Advanced Analytics"
    FRAMEWORKS_LIBS = "Frameworks & Libraries"
    CORE_CONCEPTS = "Concepts & Methodologies"
    OTHER = "Other Tools & Tech"


class Region(str, Enum):
    USA = "USA"
    EUROPE = "Europe"
    INDIA = "India"
    PAKISTAN = "Pakistan"
    APAC = "APAC"
    LATAM = "Latin America"
    MIDDLE_EAST = "Middle East"
    GLOBAL_REMOTE = "Global Remote"
    OTHER = "Other"


class SalaryInfo(BaseModel):
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "USD"
    period: str = "yearly"  # yearly, hourly, monthly

    @property
    def formatted(self) -> str:
        symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "PHP": "₱",
            "CAD": "CA$", "AUD": "A$", "JPY": "¥", "BRL": "R$", "PKR": "Rs ",
            "CRC": "₡", "MXN": "Mex$", "PLN": "zł", "SGD": "S$", "NZD": "NZ$",
            "CHF": "CHF "
        }
        sym = symbols.get((self.currency or "USD").upper(), f"{self.currency} ")
        if self.min_amount and self.max_amount:
            return f"{sym}{self.min_amount:,.0f} - {sym}{self.max_amount:,.0f} / {self.period}"
        elif self.min_amount:
            return f"From {sym}{self.min_amount:,.0f} / {self.period}"
        elif self.max_amount:
            return f"Up to {sym}{self.max_amount:,.0f} / {self.period}"
        return "Not specified"


class ExtractedSkill(BaseModel):
    name: str = ""
    canonical_name: str
    category: TechCategory
    source_section: str = "general"  # requirements, responsibilities, general
    priority_weight: float = 1.0  # Top requirements bullet points receive higher weight multipliers
    context_snippet: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_jobs: int = 0
    total_searches: int = 0
    last_keywords: Optional[str] = None
    last_location: Optional[str] = None
    last_workplace: Optional[str] = None
    last_experience: Optional[str] = None
    last_limit: Optional[int] = None


class JobPost(BaseModel):
    id: str
    project_id: str = "default"
    search_run_id: Optional[str] = None
    title: str
    company: str
    location: str
    country: Optional[str] = None
    region: Region = Region.OTHER
    workplace_type: WorkplaceType = WorkplaceType.UNKNOWN
    experience_level: ExperienceLevel = ExperienceLevel.ANY
    salary: Optional[SalaryInfo] = None
    description: str = ""
    url: str = ""
    apply_url: Optional[str] = None
    source: str = "hiringcafe"
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requirements_bullets: List[str] = Field(default_factory=list)
    task_bullets: List[str] = Field(default_factory=list)
    extracted_skills: List[ExtractedSkill] = Field(default_factory=list)
    raw_json: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def sync_apply_url(self) -> "JobPost":
        if not self.apply_url and self.url:
            self.apply_url = self.url
        elif not self.url and self.apply_url:
            self.url = self.apply_url
        return self

    @property
    def link(self) -> str:
        return self.apply_url or self.url or ""

    @property
    def salary_usd_estimate(self) -> float:
        """Estimated annual compensation normalized to USD."""
        if not self.salary:
            return 0.0
        amt = self.salary.max_amount or self.salary.min_amount or 0.0
        return currency_manager.convert_to_usd(
            amt,
            currency=self.salary.currency,
            country=self.country or self.location,
            period=self.salary.period
        )



class SearchQuery(BaseModel):
    keywords: str = "Data Analyst"
    location: str = ""
    region: Optional[Region] = None
    workplace_type: Optional[WorkplaceType] = None
    experience_level: Optional[ExperienceLevel] = None
    limit: int = 50
    project_id: str = "default"


class SkillCoOccurrence(BaseModel):
    skill_a: str
    skill_b: str
    count: int
    percentage: float


class GeoTechBreakdown(BaseModel):
    region: Region
    total_jobs: int
    top_skills: List[Dict[str, Any]]
    workplace_distribution: Dict[str, int]


class AggregatedStats(BaseModel):
    query_keywords: str
    total_jobs: int
    unique_companies: int
    workplace_distribution: Dict[str, int]
    experience_distribution: Dict[str, int]
    category_breakdown: Dict[str, List[Dict[str, Any]]]
    top_skills_overall: List[Dict[str, Any]]
    weighted_top_skills: List[Dict[str, Any]]  # Weighted by section priority (Requirements vs General)
    co_occurrences: List[SkillCoOccurrence]
    geo_breakdown: Dict[str, GeoTechBreakdown]
    salary_by_top_tech: Dict[str, Dict[str, float]]
    # New job market analytical dimensions
    salary_transparency_pct: float = 0.0
    country_salary_data: List[Dict[str, Any]] = Field(default_factory=list)
    experience_salary_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    experience_skills_breakdown: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    top_hiring_companies: List[Dict[str, Any]] = Field(default_factory=list)
    stack_density_stats: Dict[str, Any] = Field(default_factory=dict)
    workplace_salary_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict)
