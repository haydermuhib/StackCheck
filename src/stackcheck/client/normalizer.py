"""
Job Normalizer & Data Cleaning Pipeline:
- Deduplication by title + company + text fingerprint
- Spam / placeholder / irrelevant post filtering
- Region & Workplace type classification
- Salary extraction and range normalization
"""

import re
import hashlib
import difflib
from typing import Optional, Tuple, Dict, Any, List
from stackcheck.models import Region, WorkplaceType, ExperienceLevel, SalaryInfo
from stackcheck.analyzer.taxonomy import COUNTRY_TO_REGION


CANONICAL_LOCATIONS: Dict[str, str] = {
    # USA synonyms and common typos
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states": "United States",
    "united state": "United States",
    "united states of america": "United States",
    "america": "United States",
    "amercia": "United States",
    "us of a": "United States",
    
    # UK synonyms
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "england": "United Kingdom",
    "engalnd": "United Kingdom",
    "scotland": "United Kingdom",
    "london": "United Kingdom",

    # Pakistan synonyms
    "pk": "Pakistan",
    "pak": "Pakistan",
    "pakistan": "Pakistan",
    "pakisatn": "Pakistan",
    "karachi": "Pakistan",
    "lahore": "Pakistan",
    "islamabad": "Pakistan",
    "rawalpindi": "Pakistan",
    "faisalabad": "Pakistan",
    "peshawar": "Pakistan",
    
    # India synonyms
    "in": "India",
    "india": "India",
    "indai": "India",
    "bharat": "India",
    "bengaluru": "India",
    "bangalore": "India",
    "hyderabad": "India",
    "delhi": "India",
    "mumbai": "India",
    "pune": "India",
    "chennai": "India",
    "noida": "India",
    "gurgaon": "India",

    # New Zealand
    "nz": "New Zealand",
    "new zealand": "New Zealand",
    "newzealand": "New Zealand",
    "auckland": "New Zealand",
    "wellington": "New Zealand",
    "christchurch": "New Zealand",

    # Brazil
    "br": "Brazil",
    "brazil": "Brazil",
    "brasil": "Brazil",
    "sao paulo": "Brazil",
    "rio de janeiro": "Brazil",

    # Singapore
    "sg": "Singapore",
    "singapore": "Singapore",
    "singapur": "Singapore",

    # Malaysia
    "my": "Malaysia",
    "malaysia": "Malaysia",
    "kuala lumpur": "Malaysia",

    # Japan
    "jp": "Japan",
    "japan": "Japan",
    "tokyo": "Japan",
    "osaka": "Japan",

    # South Korea
    "kr": "South Korea",
    "south korea": "South Korea",
    "korea": "South Korea",
    "seoul": "South Korea",
    
    # Germany synonyms
    "germany": "Germany",
    "germnay": "Germany",
    "deutschland": "Germany",
    "berlin": "Germany",
    "munich": "Germany",
    
    # Canada
    "canada": "Canada",
    "candad": "Canada",
    "toronto": "Canada",
    "vancouver": "Canada",
    
    # Australia
    "australia": "Australia",
    "austrlia": "Australia",
    "sydney": "Australia",
    "melbourne": "Australia",

    # UAE / Middle East
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "dubai": "United Arab Emirates",
    "abu dhabi": "United Arab Emirates",
    "saudi arabia": "Saudi Arabia",
    "riyadh": "Saudi Arabia",

    # Netherlands / France / Europe
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    "amsterdam": "Netherlands",
    "france": "France",
    "paris": "France",
    "europe": "Europe",
    "eu": "Europe",
    
    # Remote
    "remote": "Remote",
    "wfh": "Remote",
    "anywhere": "Remote",
    "global": "Remote",
}

SUGGESTED_ROLES = [
    # Data & Business Intelligence
    "Data Analyst",
    "Data Scientist",
    "Data Engineer",
    "Analytics Engineer",
    "Business Intelligence Developer",
    "Product Analyst",
    "Database Administrator",

    # AI & Machine Learning
    "Machine Learning Engineer",
    "AI Engineer",
    "LLM Engineer",
    "Computer Vision Engineer",
    "NLP Engineer",
    "Research Scientist",

    # Software Engineering & Development
    "Full Stack Engineer",
    "Backend Engineer",
    "Frontend Developer",
    "Software Engineer",
    "Solutions Architect",
    "Mobile Developer",
    "iOS Developer",
    "Android Developer",
    "Game Developer",
    "Embedded Systems Engineer",

    # Cloud, DevOps & Infrastructure
    "DevOps Engineer",
    "Site Reliability Engineer",
    "Cloud Architect",
    "Cloud Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",

    # Cybersecurity
    "Cybersecurity Engineer",
    "Security Analyst",
    "Information Security Architect",

    # QA & Technical Leadership
    "QA Automation Engineer",
    "Technical Product Manager",
    "Engineering Manager",
]

SUGGESTED_LOCATIONS = [
    ("Global / Any Location", ""),
    ("United States (USA)", "United States"),
    ("United Kingdom (UK)", "United Kingdom"),
    ("Pakistan", "Pakistan"),
    ("India", "India"),
    ("Germany (Europe)", "Germany"),
    ("Canada", "Canada"),
    ("Australia", "Australia"),
    ("New Zealand", "New Zealand"),
    ("Singapore", "Singapore"),
    ("Malaysia", "Malaysia"),
    ("Japan", "Japan"),
    ("South Korea", "South Korea"),
    ("Brazil", "Brazil"),
    ("Netherlands", "Netherlands"),
    ("United Arab Emirates (UAE)", "United Arab Emirates"),
    ("Remote Worldwide", "Remote"),
]


class JobNormalizer:
    """Cleans and standardizes raw job data into structured fields."""

    @staticmethod
    def normalize_location_query(location_input: str) -> str:
        """
        Translates synonyms and fuzzy matches (e.g. 'USA', 'US', 'Amercia')
        to canonical names expected by HiringCafe (e.g. 'United States').
        """
        if not location_input:
            return ""
            
        cleaned = location_input.strip().lower()
        
        # 1. Exact match in canonical dictionary
        if cleaned in CANONICAL_LOCATIONS:
            return CANONICAL_LOCATIONS[cleaned]
            
        # 2. Check substring matches
        for synonym, canonical in CANONICAL_LOCATIONS.items():
            if synonym == cleaned or f" {synonym} " in f" {cleaned} ":
                return canonical
                
        # 3. Fuzzy matching for typo tolerance (e.g., "Amercia" -> "united states", "indai" -> "india")
        canonical_targets = list(CANONICAL_LOCATIONS.keys())
        matches = difflib.get_close_matches(cleaned, canonical_targets, n=1, cutoff=0.7)
        if matches:
            return CANONICAL_LOCATIONS[matches[0]]

        return location_input.strip()

    @staticmethod
    def compute_fingerprint(title: str, company: str, description: str) -> str:
        """Create a deterministic hash to eliminate duplicate postings across sources."""
        norm_title = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
        norm_comp = re.sub(r"[^a-zA-Z0-9]", "", company.lower())
        # First 200 chars of description
        norm_desc = re.sub(r"[^a-zA-Z0-9]", "", description[:200].lower())
        content = f"{norm_title}|{norm_comp}|{norm_desc}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @staticmethod
    def is_spam_or_irrelevant(title: str, description: str) -> bool:
        """Filter out obvious scam, commission-only, MLM, or placeholder ads."""
        text = f"{title} {description}".lower()
        
        spam_signals = [
            "earn $500/day from home without skills",
            "mystery shopper",
            "crypto investment scheme",
            "be your own boss unlimited earnings",
            "pay upfront fee",
            "wire transfer required",
            "telegram to apply",
            "whatsapp only for interview"
        ]
        for signal in spam_signals:
            if signal in text:
                return True
                
        # Length check
        if len(description.strip()) < 30:
            return True
            
        return False

    @staticmethod
    def parse_workplace_type(location_str: str, workplace_field: Optional[str] = None) -> WorkplaceType:
        """Determine if job is Remote, Hybrid, or Onsite."""
        text = f"{location_str} {workplace_field or ''}".lower()
        if "remote" in text or "anywhere" in text or "work from home" in text or "wfh" in text:
            if "hybrid" in text:
                return WorkplaceType.HYBRID
            return WorkplaceType.REMOTE
        elif "hybrid" in text:
            return WorkplaceType.HYBRID
        elif location_str:
            return WorkplaceType.ONSITE
        return WorkplaceType.UNKNOWN

    @staticmethod
    def parse_region_and_country(location_str: str) -> Tuple[Region, Optional[str]]:
        """Map raw location strings to standard Region and Country."""
        if not location_str:
            return Region.OTHER, None
            
        loc_lower = location_str.lower().strip()
        
        if "remote" in loc_lower or "anywhere" in loc_lower or "global" in loc_lower:
            return Region.GLOBAL_REMOTE, "Remote"

        # Check against known country mapping
        for country, region_name in COUNTRY_TO_REGION.items():
            if re.search(r"\b" + re.escape(country) + r"\b", loc_lower):
                for r in Region:
                    if r.value == region_name:
                        return r, country.title()

        # US State abbreviations (CA, NY, TX, WA, etc.)
        if re.search(r"\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)\b", loc_lower):
            return Region.USA, "United States"

        # Pakistani tech hubs
        if any(city in loc_lower for city in ["karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "peshawar"]):
            return Region.PAKISTAN, "Pakistan"

        # Indian tech hubs
        if any(city in loc_lower for city in ["bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "chennai"]):
            return Region.INDIA, "India"

        # Middle Eastern tech hubs
        if any(city in loc_lower for city in ["dubai", "abu dhabi", "riyadh", "doha"]):
            return Region.MIDDLE_EAST, "Middle East"

        # European tech hubs
        if any(city in loc_lower for city in ["london", "berlin", "amsterdam", "paris", "dublin", "madrid", "warsaw", "stockholm", "zurich"]):
            return Region.EUROPE, "Europe"

        # APAC tech hubs
        if any(city in loc_lower for city in ["singapore", "tokyo", "seoul", "sydney", "melbourne", "auckland", "kuala lumpur"]):
            return Region.APAC, "APAC"

        return Region.OTHER, None

    @staticmethod
    def parse_experience_level(title: str, description: str) -> ExperienceLevel:
        """Extract experience level (Entry, Mid, Senior, Lead, Executive)."""
        text = f"{title} {description[:400]}".lower()
        
        if any(k in text for k in ["vp", "vice president", "director", "head of", "chief"]):
            return ExperienceLevel.EXECUTIVE
        elif any(k in text for k in ["lead", "principal", "staff", "architect", "manager"]):
            return ExperienceLevel.LEAD
        elif any(k in text for k in ["senior", "sr.", "sr ", "expert"]):
            return ExperienceLevel.SENIOR
        elif any(k in text for k in ["entry", "junior", "jr.", "jr ", "graduate", "associate", "intern", "internship", "trainee"]):
            return ExperienceLevel.ENTRY
        elif any(k in text for k in ["mid-level", "mid level", "intermediate", "ii", "iii"]):
            return ExperienceLevel.MID
            
        return ExperienceLevel.MID  # Default assumption for standard non-specified roles

    @staticmethod
    def parse_salary(salary_raw: Any, text: str = "") -> Optional[SalaryInfo]:
        """Extract and normalize salary data from structured payload or raw text."""
        if isinstance(salary_raw, dict):
            min_sal = salary_raw.get("min") or salary_raw.get("min_amount") or salary_raw.get("minimum")
            max_sal = salary_raw.get("max") or salary_raw.get("max_amount") or salary_raw.get("maximum")
            currency = salary_raw.get("currency", "USD")
            period = salary_raw.get("period", "yearly")
            if min_sal or max_sal:
                return SalaryInfo(
                    min_amount=float(min_sal) if min_sal else None,
                    max_amount=float(max_sal) if max_sal else None,
                    currency=currency,
                    period=period
                )

        # Regex search for salary strings like "$120,000 - $160,000" or "$80k - $110k" or "$50 - $75 / hr"
        m = re.search(r"\$([0-9]{2,3}(?:,[0-9]{3})*|[0-9]{2,3}k)\s*(?:-|to)\s*\$([0-9]{2,3}(?:,[0-9]{3})*|[0-9]{2,3}k)", text, re.IGNORECASE)
        if m:
            def parse_val(v_str: str) -> float:
                v_str = v_str.lower().replace(",", "")
                if "k" in v_str:
                    return float(v_str.replace("k", "")) * 1000
                return float(v_str)

            min_v = parse_val(m.group(1))
            max_v = parse_val(m.group(2))
            period = "yearly" if min_v > 1000 else "hourly"
            return SalaryInfo(min_amount=min_v, max_amount=max_v, currency="USD", period=period)

        return None
