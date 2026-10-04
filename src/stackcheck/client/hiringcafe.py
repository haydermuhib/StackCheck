"""
HiringCafe Live Client:
Scrapes real job postings directly from HiringCafe using browser-impersonated HTTP sessions.
Zero fake/mock data — reports real errors on network issues.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from curl_cffi import requests
import json
import re
import urllib.parse

from stackcheck.models import JobPost, SearchQuery, WorkplaceType, ExperienceLevel, Region, SalaryInfo
from stackcheck.client.normalizer import JobNormalizer
from stackcheck.analyzer.rule_extractor import RuleExtractor
from stackcheck.analyzer.llm_extractor import LLMExtractor
from stackcheck.config import HIRINGCAFE_BASE_URL, DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

COUNTRY_TO_ISO2: Dict[str, str] = {
    "united states": "US",
    "usa": "US",
    "us": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "pakistan": "PK",
    "pk": "PK",
    "india": "IN",
    "in": "IN",
    "germany": "DE",
    "canada": "CA",
    "australia": "AU",
    "new zealand": "NZ",
    "singapore": "SG",
    "malaysia": "MY",
    "japan": "JP",
    "south korea": "KR",
    "brazil": "BR",
    "netherlands": "NL",
    "united arab emirates": "AE",
    "uae": "AE",
    "saudi arabia": "SA",
    "france": "FR",
    "spain": "ES",
    "italy": "IT",
    "poland": "PL",
    "switzerland": "CH",
    "sweden": "SE",
    "ireland": "IE",
    "philippines": "PH",
    "vietnam": "VN",
    "mexico": "MX",
}


class HiringCafeClient:
    """Live HTTP Client for scraping and querying real job listings from HiringCafe."""

    def __init__(self, use_llm_if_available: bool = False):
        self.rule_extractor = RuleExtractor()
        self.llm_extractor = LLMExtractor() if use_llm_if_available else None
        self.last_error: Optional[str] = None
        self.session = requests.Session(impersonate="chrome120")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://hiringcafe.com/",
        })

    def search_jobs(self, query: SearchQuery, progress_callback=None) -> List[JobPost]:
        """
        Execute live job search against HiringCafe and parse results.
        Returns ONLY genuine, real job postings. If network fails, returns empty list with explicit error message.
        """
        self.last_error = None
        raw_items, error_msg = self._fetch_live_jobs(query, progress_callback)
        if error_msg:
            self.last_error = error_msg
            if progress_callback:
                progress_callback(0, 1, error_msg)
            logger.error(f"HiringCafe Search Error: {error_msg}")
            return []

        if not raw_items:
            if progress_callback:
                progress_callback(0, 1, f"No jobs found on HiringCafe matching '{query.keywords}'.")
            return []

        seen_fingerprints = set()
        clean_jobs: List[JobPost] = []

        total = len(raw_items)
        for idx, item in enumerate(raw_items):
            if progress_callback:
                progress_callback(idx + 1, total, f"Cleaning & analyzing real job {idx+1}/{total}...")

            v5 = item.get("v5_processed_job_data") or {}
            info = item.get("job_information") or {}

            title = info.get("title") or v5.get("core_job_title") or item.get("job_title") or "Job Opportunity"
            company = v5.get("company_name") or info.get("company_name") or item.get("company_name") or "Company"
            
            # Extract requirements and description
            req_summary = v5.get("requirements_summary") or ""
            role_activities = v5.get("role_activities") or ""
            tech_tools = v5.get("technical_tools") or []
            
            # Reconstruct structured description from real v5 fields
            desc_parts = []
            if req_summary:
                desc_parts.append(f"What we are looking for:\n{req_summary}")
            if role_activities:
                desc_parts.append(f"What you will be doing:\n{role_activities}")
            if tech_tools:
                tools_str = ", ".join(tech_tools) if isinstance(tech_tools, list) else str(tech_tools)
                desc_parts.append(f"Required Technical Tools: {tools_str}")
                
            raw_desc = info.get("description") or "\n\n".join(desc_parts) or title
            location_raw = v5.get("formatted_workplace_location") or info.get("location") or item.get("formatted_workplace_location") or ""
            url = item.get("apply_url") or info.get("apply_url") or item.get("job_url")
            if not url and item.get("id"):
                url = f"https://hiringcafe.com/jobs/{item.get('id')}"
            elif not url:
                url = "https://hiringcafe.com"

            # Step 1: Filter by keyword relevance if doing broad fetch
            kw_lower = query.keywords.lower().strip()
            text_to_check = f"{title} {raw_desc} {' '.join(tech_tools if isinstance(tech_tools, list) else [])}".lower()
            if kw_lower and kw_lower != "all" and not any(word in text_to_check for word in kw_lower.split()):
                continue

            # Step 2: Spam & Quality Filter
            if JobNormalizer.is_spam_or_irrelevant(title, raw_desc):
                continue

            # Step 3: Deduplication (Preserve distinct job openings, even within the same company)
            job_uid = item.get("id") or item.get("objectID") or item.get("canonical_job_id")
            fp = str(job_uid) if job_uid else JobNormalizer.compute_fingerprint(title, company, f"{location_raw} {raw_desc}")
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)

            # Step 4: Location, Region, & Workplace Classification
            workplace_str = v5.get("workplace_type") or info.get("workplace_type") or item.get("workplace_type")
            workplace = JobNormalizer.parse_workplace_type(location_raw, workplace_str)
            region, country = JobNormalizer.parse_region_and_country(location_raw)

            if query.location:
                norm_query_loc = JobNormalizer.normalize_location_query(query.location).lower()
                if norm_query_loc not in ["", "all", "global", "any", "worldwide", "global / any location"]:
                    if norm_query_loc in ["remote", "remote worldwide"]:
                        if workplace != WorkplaceType.REMOTE and "remote" not in location_raw.lower():
                            continue
                    else:
                        loc_check = f"{location_raw} {region.value} {country or ''}".lower()
                        if norm_query_loc not in loc_check and (not country or country.lower() != norm_query_loc):
                            continue

            if query.workplace_type and query.workplace_type != WorkplaceType.UNKNOWN:
                if workplace != query.workplace_type:
                    continue

            # Step 5: Experience Level
            seniority = v5.get("seniority_level")
            exp_level = JobNormalizer.parse_experience_level(title, f"{seniority or ''} {raw_desc}")
            if query.experience_level and query.experience_level != ExperienceLevel.ANY:
                if exp_level != query.experience_level:
                    continue

            # Step 6: Salary Extraction
            min_sal = v5.get("yearly_min_compensation") or v5.get("hourly_min_compensation")
            max_sal = v5.get("yearly_max_compensation") or v5.get("hourly_max_compensation")
            curr = v5.get("listed_compensation_currency") or "USD"
            period = v5.get("listed_compensation_frequency") or "yearly"
            
            salary = None
            if min_sal or max_sal:
                salary = SalaryInfo(
                    min_amount=float(min_sal) if min_sal else None,
                    max_amount=float(max_sal) if max_sal else None,
                    currency=curr,
                    period=period.lower()
                )
            else:
                salary = JobNormalizer.parse_salary(None, raw_desc)

            # Step 7: Section-aware Tech Stack & Bullet Extraction
            skills = []
            req_bullets = []
            task_bullets = []

            # Try LLM if configured and selected
            if self.llm_extractor and self.llm_extractor.is_configured:
                llm_res = self.llm_extractor.extract(title, company, raw_desc)
                if llm_res:
                    skills, req_bullets, task_bullets = llm_res

            # Default Rule Extractor
            if not skills:
                skills, req_bullets, task_bullets = self.rule_extractor.process_job_description(raw_desc)
                # If tech_tools list is explicitly provided by HiringCafe, also match them
                if isinstance(tech_tools, list) and tech_tools:
                    tools_text = "\n".join([f"• {t}" for t in tech_tools])
                    tool_skills = self.rule_extractor.extract_from_text(tools_text, section="requirements", base_weight=1.5)
                    seen_names = {s.canonical_name for s in skills}
                    for ts in tool_skills:
                        if ts.canonical_name not in seen_names:
                            skills.append(ts)

            job_post = JobPost(
                id=fp,
                project_id=getattr(query, "project_id", "default") or "default",
                title=title,
                company=company,
                location=location_raw or "Unspecified Location",
                country=country,
                region=region,
                workplace_type=workplace,
                experience_level=exp_level,
                salary=salary,
                description=raw_desc,
                url=url,
                apply_url=url,
                requirements_bullets=req_bullets,
                task_bullets=task_bullets,
                extracted_skills=skills,
                raw_json=item
            )
            clean_jobs.append(job_post)
            if query.limit > 0 and len(clean_jobs) >= query.limit:
                break

        return clean_jobs

    def _fetch_live_jobs(self, query: SearchQuery, progress_callback=None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch genuine live job postings from HiringCafe with targeted filters and multi-page pagination."""
        if progress_callback:
            progress_callback(10, 100, "Connecting to HiringCafe live job index...")

        # Build structured search state for HiringCafe
        search_state: Dict[str, Any] = {}
        kw = query.keywords.strip() if query.keywords and query.keywords.lower() != "all" else ""
        if kw:
            search_state["searchQuery"] = kw

        loc = query.location.strip() if query.location else ""
        norm_loc = JobNormalizer.normalize_location_query(loc) if loc else ""
        if norm_loc and norm_loc.lower() not in ["", "all", "global", "any", "worldwide", "remote", "remote worldwide", "global / any location"]:
            iso = COUNTRY_TO_ISO2.get(norm_loc.lower(), norm_loc[:2].upper())
            search_state["locations"] = [{
                "formatted_address": norm_loc,
                "types": ["country"],
                "address_components": [{"long_name": norm_loc, "short_name": iso, "types": ["country"]}],
                "options": {"flexible_regions": ["anywhere_in_continent", "anywhere_in_world"]}
            }]
        else:
            # When Worldwide/Global is selected, cover all major continents to unlock the full 28,000+ job index
            continents = ["North America", "Europe", "Asia", "South America", "Africa", "Australia"]
            search_state["locations"] = [
                {
                    "types": ["continent"],
                    "address_components": [{"long_name": c, "short_name": c, "types": ["continent"]}],
                    "formatted_address": c
                }
                for c in continents
            ]

        wp = []
        if query.workplace_type == WorkplaceType.REMOTE or (loc and loc.lower() in ["remote", "remote worldwide"]):
            wp.append("Remote")
        elif query.workplace_type == WorkplaceType.HYBRID:
            wp.append("Hybrid")
        elif query.workplace_type == WorkplaceType.ONSITE:
            wp.append("Onsite")
        if wp:
            search_state["workplaceTypes"] = wp

        # Calculate pages needed to satisfy limit (each page returns ~60-90 jobs)
        # When query.limit == 0 (Fetch All mode), paginate up to safety ceiling of 40 pages (~2,500 jobs)
        if query.limit == 0:
            target_pages = 40
        else:
            target_pages = min(max(1, (query.limit + 40) // 40), 30)
        
        all_hits: List[Dict[str, Any]] = []
        seen_hit_ids = set()
        last_error = None

        encoded_state = urllib.parse.quote(json.dumps(search_state))

        for page_idx in range(target_pages):
            if progress_callback:
                page_label = f"Scraping page {page_idx + 1}/{target_pages} ({len(all_hits)} postings collected)..." if query.limit > 0 else f"Deep scraping page {page_idx + 1} ({len(all_hits)} postings collected so far)..."
                progress_callback(
                    page_idx + 1, 
                    target_pages + 1, 
                    page_label
                )

            page_url = f"https://hiringcafe.com/classic?searchState={encoded_state}&page={page_idx}"
            try:
                resp = self.session.get(page_url, timeout=12.0)
                if resp.status_code == 200:
                    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text)
                    if m:
                        data = json.loads(m.group(1))
                        hits = data.get("props", {}).get("pageProps", {}).get("ssrHits", [])
                        if isinstance(hits, list) and len(hits) > 0:
                            new_in_page = 0
                            for h in hits:
                                hid = h.get("id") or h.get("objectID") or h.get("canonical_job_id")
                                if hid and hid in seen_hit_ids:
                                    continue
                                if hid:
                                    seen_hit_ids.add(hid)
                                all_hits.append(h)
                                new_in_page += 1

                            # Circuit breaker: If a page returns 0 new hits, end of results has been reached
                            if new_in_page == 0 and page_idx > 0:
                                break

                            # If a specific limit is set (> 0), stop once candidate pool is sufficient
                            if query.limit > 0 and len(all_hits) >= query.limit * 2:
                                break
                            continue
                        elif page_idx > 0:
                            # Reached last page
                            break
                elif resp.status_code == 403:
                    last_error = "❌ HiringCafe blocked request with HTTP 403 (Cloudflare Bot Challenge)."
                else:
                    last_error = f"❌ HiringCafe returned HTTP {resp.status_code}."
            except Exception as e:
                err_str = str(e)
                if "could not resolve host" in err_str.lower() or "connection" in err_str.lower() or "name resolution" in err_str.lower():
                    last_error = f"❌ No Internet Connection: Unable to resolve or connect to hiringcafe.com ({err_str})"
                elif "timeout" in err_str.lower():
                    last_error = "❌ Request Timeout: HiringCafe server took too long to respond."
                else:
                    last_error = f"❌ HiringCafe Fetch Error: {err_str}"

        if all_hits:
            return all_hits, None

        # Fallback to single /search?q= if classic yielded nothing
        if kw:
            try:
                fallback_url = f"https://hiringcafe.com/search?q={urllib.parse.quote(kw)}"
                resp = self.session.get(fallback_url, timeout=12.0)
                if resp.status_code == 200:
                    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text)
                    if m:
                        data = json.loads(m.group(1))
                        hits = data.get("props", {}).get("pageProps", {}).get("ssrHits", [])
                        if isinstance(hits, list) and len(hits) > 0:
                            return hits, None
            except Exception:
                pass

        if last_error:
            return [], last_error
        return [], f"No jobs found on HiringCafe matching '{query.keywords}'."
