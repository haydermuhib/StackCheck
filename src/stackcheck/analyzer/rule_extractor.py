"""
Section-aware Rule-based Skill Extractor with Priority Weighting and Disambiguation.
"""

import re
from typing import List, Tuple, Dict, Any
from stackcheck.models import ExtractedSkill, TechCategory
from stackcheck.analyzer.taxonomy import CANONICAL_TAXONOMY


# Regex patterns for identifying sections
REQUIREMENTS_HEADERS = [
    r"(?:what\s+we(?:'re|\s+are)\s+looking\s+for)",
    r"(?:requirements?)",
    r"(?:qualifications?)",
    r"(?:must\s+haves?)",
    r"(?:what\s+you(?:'ll|\s+will)\s+bring)",
    r"(?:basic\s+qualifications?)",
    r"(?:minimum\s+qualifications?)",
    r"(?:required\s+skills?)",
    r"(?:who\s+you\s+are)",
]

RESPONSIBILITIES_HEADERS = [
    r"(?:what\s+you(?:'ll|\s+will)\s+be\s+doing)",
    r"(?:responsibilities?)",
    r"(?:day\s+to\s+day)",
    r"(?:key\s+responsibilities?)",
    r"(?:duties)",
    r"(?:your\s+role)",
    r"(?:about\s+the\s+role)",
    r"(?:what\s+you(?:'ll|\s+will)\s+do)",
]

REQUIREMENTS_REGEX = re.compile(r"^\s*(?:#+\s*|\*\*\s*|[•\-*]\s*)?(" + "|".join(REQUIREMENTS_HEADERS) + r")[:\*\s]*$", re.IGNORECASE | re.MULTILINE)
RESPONSIBILITIES_REGEX = re.compile(r"^\s*(?:#+\s*|\*\*\s*|[•\-*]\s*)?(" + "|".join(RESPONSIBILITIES_HEADERS) + r")[:\*\s]*$", re.IGNORECASE | re.MULTILINE)


def extract_bullet_points(text: str) -> List[str]:
    """Extract individual bullet items or discrete lines from text."""
    lines = text.split("\n")
    bullets = []
    for line in lines:
        cleaned = line.strip()
        # Match standard markdown / unicode bullets or numbered lists
        m = re.match(r"^(?:[•\-*+>]|\d+[\.\)])\s*(.+)$", cleaned)
        if m:
            bullet_text = m.group(1).strip()
            if len(bullet_text) > 4:
                bullets.append(bullet_text)
        elif len(cleaned) > 20 and not cleaned.endswith(":"):
            bullets.append(cleaned)
    return bullets


def segment_job_description(description: str) -> Dict[str, Any]:
    """
    Split a job description into structured sections:
    - requirements
    - responsibilities
    - general
    """
    lines = description.split("\n")
    current_section = "general"
    
    sections = {
        "requirements_text": [],
        "responsibilities_text": [],
        "general_text": [],
        "requirements_bullets": [],
        "task_bullets": [],
    }
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        if REQUIREMENTS_REGEX.search(stripped):
            current_section = "requirements"
            continue
        elif RESPONSIBILITIES_REGEX.search(stripped):
            current_section = "responsibilities"
            continue
            
        if current_section == "requirements":
            sections["requirements_text"].append(stripped)
        elif current_section == "responsibilities":
            sections["responsibilities_text"].append(stripped)
        else:
            sections["general_text"].append(stripped)
            
    req_full = "\n".join(sections["requirements_text"])
    resp_full = "\n".join(sections["responsibilities_text"])
    
    sections["requirements_bullets"] = extract_bullet_points(req_full) if req_full else extract_bullet_points(description)
    sections["task_bullets"] = extract_bullet_points(resp_full)
    
    return sections


def compile_pattern(keyword: str) -> re.Pattern:
    """Compile regex pattern ensuring exact word boundaries and disambiguation."""
    kw = keyword.strip()
    # Special character handling (C++, C#, .NET, etc.)
    if kw in ("c++", "cpp"):
        return re.compile(r"(?:\bcpp\b|\bc\+\+(?![a-z]))", re.IGNORECASE)
    elif kw in ("c#", "csharp"):
        return re.compile(r"(?:\bcsharp\b|\bc#(?![a-z]))", re.IGNORECASE)
    elif kw in ("r", "r language", "r programming"):
        return re.compile(r"(?:\bR\s+(?:language|programming|scripting|studio|package)|\b(?:R|Python)[,\/]\s*(?:Python|R)\b|\bexperienc(?:e|ed)\s+with\s+R\b|\busing\s+R\b)", re.IGNORECASE)
    elif kw in ("go", "golang"):
        return re.compile(r"(?:\bgolang\b|\bgo\s+(?:language|developer|engineer|code)\b)", re.IGNORECASE)
    elif kw in ("dbt", "data build tool"):
        return re.compile(r"(?:\bdbt\b|\bdata\s+build\s+tool\b)", re.IGNORECASE)
    elif kw in ("k8s", "kubernetes"):
        return re.compile(r"(?:\bk8s\b|\bkubernetes\b)", re.IGNORECASE)
    elif kw in ("sql", "structured query language"):
        return re.compile(r"(?:\bsql\b|\bstructured\s+query\s+language\b)", re.IGNORECASE)
    elif kw == "aws":
        return re.compile(r"(?:\baws\b|\bamazon\s+web\s+services\b)", re.IGNORECASE)
    elif kw == "gcp":
        return re.compile(r"(?:\bgcp\b|\bgoogle\s+cloud(?:\s+platform)?\b)", re.IGNORECASE)
    else:
        escaped = re.escape(kw)
        return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


class RuleExtractor:
    """Rule-based extractor combining section weights and boundary regexes."""
    
    def __init__(self):
        # Precompile patterns for all taxonomy items
        self.compiled_rules: List[Tuple[str, TechCategory, List[re.Pattern]]] = []
        for canonical_name, (category, aliases) in CANONICAL_TAXONOMY.items():
            patterns = [compile_pattern(alias) for alias in aliases]
            self.compiled_rules.append((canonical_name, category, patterns))

    def extract_from_text(self, text: str, section: str = "general", base_weight: float = 1.0) -> List[ExtractedSkill]:
        """Extract skills from a specific text chunk with given section weighting."""
        found_skills: Dict[str, ExtractedSkill] = {}
        
        for canonical_name, category, patterns in self.compiled_rules:
            for pat in patterns:
                match = pat.search(text)
                if match:
                    # Calculate snippet context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    snippet = text[start:end].replace("\n", " ").strip()
                    
                    if canonical_name not in found_skills or found_skills[canonical_name].priority_weight < base_weight:
                        found_skills[canonical_name] = ExtractedSkill(
                            name=canonical_name,
                            canonical_name=canonical_name,
                            category=category,
                            source_section=section,
                            priority_weight=base_weight,
                            context_snippet=f"...{snippet}..."
                        )
                    break
        return list(found_skills.values())

    def process_job_description(self, description: str) -> Tuple[List[ExtractedSkill], List[str], List[str]]:
        """
        Processes a full job description:
        1. Segments into Requirements, Responsibilities, and General.
        2. Applies positional weights to top requirements bullets (higher bullet = higher weight multiplier).
        3. Returns combined deduplicated skills and extracted section bullets.
        """
        segmented = segment_job_description(description)
        skills_map: Dict[str, ExtractedSkill] = {}
        
        # 1. Process Requirements bullets with positional decay weight (1.8 down to 1.0)
        req_bullets = segmented["requirements_bullets"]
        total_reqs = max(len(req_bullets), 1)
        for idx, bullet in enumerate(req_bullets):
            # First 3 bullets get highest priority boost (1.8, 1.5, 1.3)
            if idx == 0:
                weight = 1.8
            elif idx == 1:
                weight = 1.5
            elif idx == 2:
                weight = 1.3
            else:
                weight = max(1.0, 1.2 - (idx / total_reqs) * 0.2)
                
            skills = self.extract_from_text(bullet, section="requirements", base_weight=weight)
            for s in skills:
                if s.canonical_name not in skills_map or skills_map[s.canonical_name].priority_weight < s.priority_weight:
                    skills_map[s.canonical_name] = s

        # 2. Process Responsibilities/Task bullets (weight = 1.2)
        task_bullets = segmented["task_bullets"]
        for bullet in task_bullets:
            skills = self.extract_from_text(bullet, section="responsibilities", base_weight=1.2)
            for s in skills:
                if s.canonical_name not in skills_map or skills_map[s.canonical_name].priority_weight < s.priority_weight:
                    skills_map[s.canonical_name] = s

        # 3. Process remaining general text (weight = 1.0)
        general_text = "\n".join(segmented["general_text"])
        if general_text:
            skills = self.extract_from_text(general_text, section="general", base_weight=1.0)
            for s in skills:
                if s.canonical_name not in skills_map:
                    skills_map[s.canonical_name] = s
                    
        # If no requirements were cleanly sectioned, run over entire description
        if not skills_map and description:
            skills = self.extract_from_text(description, section="general", base_weight=1.0)
            for s in skills:
                skills_map[s.canonical_name] = s

        return list(skills_map.values()), req_bullets, task_bullets
