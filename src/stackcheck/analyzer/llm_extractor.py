"""
Optional LLM-Assisted Job Description Extractor.
Uses Gemini or OpenAI API if configured, with graceful fallback.
"""

import os
import json
import logging
from typing import List, Tuple, Optional
import httpx
from stackcheck.models import ExtractedSkill, TechCategory
from stackcheck.config import GEMINI_API_KEY, OPENAI_API_KEY
from stackcheck.analyzer.taxonomy import CANONICAL_TAXONOMY

logger = logging.getLogger(__name__)


LLM_PROMPT_TEMPLATE = """
You are an expert tech recruiter and data analyst. Analyze this job posting:
Title: {title}
Company: {company}
Description:
{description}

Extract all explicitly mentioned technical skills, tools, frameworks, and programming languages.
For each skill, determine:
1. Canonical Name (e.g., "PostgreSQL", "React", "Power BI", "Snowflake", "Python")
2. Category (one of: "Programming Languages", "BI & Visualization", "Data Engineering & Platforms", "Databases & Storage", "Cloud & DevOps", "AI / ML & Advanced Analytics", "Frameworks & Libraries", "Concepts & Methodologies", "Other Tools & Tech")
3. Source Section ("requirements", "responsibilities", or "general")
4. Priority Weight: 1.8 for top 3 mandatory requirements, 1.3 for other requirements, 1.2 for day-to-day responsibilities, 1.0 for nice-to-haves/general.

Return JSON in this format ONLY:
{{
  "skills": [
    {{
      "name": "Python",
      "canonical_name": "Python",
      "category": "Programming Languages",
      "source_section": "requirements",
      "priority_weight": 1.8,
      "context_snippet": "Minimum 3 years Python programming..."
    }}
  ],
  "requirements_bullets": ["..."],
  "task_bullets": ["..."]
}}
"""


class LLMExtractor:
    """LLM parser for nuanced job posting extraction."""

    def __init__(self):
        self.gemini_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.is_configured = bool(self.gemini_key or self.openai_key)

    def extract(self, title: str, company: str, description: str) -> Optional[Tuple[List[ExtractedSkill], List[str], List[str]]]:
        """Call Gemini or OpenAI API to extract structured skills from job text."""
        if not self.is_configured or not description:
            return None

        prompt = LLM_PROMPT_TEMPLATE.format(
            title=title,
            company=company,
            description=description[:3000]  # Cap length for speed
        )

        try:
            if self.gemini_key:
                return self._call_gemini(prompt)
            elif self.openai_key:
                return self._call_openai(prompt)
        except Exception as e:
            logger.warning(f"LLM extraction error: {e}, falling back to rule engine.")
            return None

        return None

    def _call_gemini(self, prompt: str) -> Optional[Tuple[List[ExtractedSkill], List[str], List[str]]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_json_response(text)
        return None

    def _call_openai(self, prompt: str) -> Optional[Tuple[List[ExtractedSkill], List[str], List[str]]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                return self._parse_json_response(text)
        return None

    def _parse_json_response(self, raw_json_str: str) -> Tuple[List[ExtractedSkill], List[str], List[str]]:
        data = json.loads(raw_json_str)
        skills = []
        for item in data.get("skills", []):
            cat_name = item.get("category", "Other Tools & Tech")
            category = TechCategory.OTHER
            for c in TechCategory:
                if c.value.lower() == cat_name.lower():
                    category = c
                    break
            skills.append(ExtractedSkill(
                name=item.get("name", "Unknown"),
                canonical_name=item.get("canonical_name", item.get("name", "Unknown")),
                category=category,
                source_section=item.get("source_section", "general"),
                priority_weight=float(item.get("priority_weight", 1.0)),
                context_snippet=item.get("context_snippet")
            ))
        return skills, data.get("requirements_bullets", []), data.get("task_bullets", [])
