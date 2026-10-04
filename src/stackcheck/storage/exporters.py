"""
Exporters for saving analysis reports to JSON, CSV, and Markdown formats.
"""

import json
import csv
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from stackcheck.models import AggregatedStats, JobPost
from stackcheck.config import EXPORTS_DIR


class ReportExporter:
    """Generates structured export files for jobs and aggregated market statistics."""

    @staticmethod
    def export_json(stats: AggregatedStats, jobs: List[JobPost], filename: str = "stackcheck_report.json") -> Path:
        out_path = EXPORTS_DIR / filename
        data = {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "query": stats.query_keywords,
                "total_jobs": stats.total_jobs,
                "unique_companies": stats.unique_companies
            },
            "stats": stats.model_dump(),
            "jobs": [j.model_dump() for j in jobs]
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return out_path

    @staticmethod
    def export_csv(jobs: List[JobPost], filename: str = "stackcheck_jobs.csv") -> Path:
        out_path = EXPORTS_DIR / filename
        fieldnames = [
            "id", "title", "company", "location", "country", "region", 
            "workplace_type", "experience_level", "salary_formatted", 
            "extracted_skills", "url", "scraped_at"
        ]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for j in jobs:
                skills_str = ", ".join([s.canonical_name for s in j.extracted_skills])
                writer.writerow({
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "country": j.country or "",
                    "region": j.region.value,
                    "workplace_type": j.workplace_type.value,
                    "experience_level": j.experience_level.value,
                    "salary_formatted": j.salary.formatted if j.salary else "N/A",
                    "extracted_skills": skills_str,
                    "url": j.url,
                    "scraped_at": j.scraped_at.isoformat()
                })
        return out_path

    @staticmethod
    def export_markdown(stats: AggregatedStats, filename: str = "stackcheck_summary.md") -> Path:
        out_path = EXPORTS_DIR / filename
        
        md_lines = [
            f"# 📊 StackCheck Market Intelligence Report: {stats.query_keywords}",
            f"*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "## 📌 Executive Summary",
            f"- **Total Clean Postings Analyzed:** {stats.total_jobs}",
            f"- **Unique Companies:** {stats.unique_companies}",
            f"- **Salary Transparency Rate:** {stats.salary_transparency_pct}% of postings disclose salary",
            f"- **Avg Tech Stack Breadth:** {stats.stack_density_stats.get('avg_skills_per_job', 0.0)} skills / posting",
            f"- **Workplace Split:** Remote: {stats.workplace_distribution.get('remote', 0)} | Hybrid: {stats.workplace_distribution.get('hybrid', 0)} | Onsite: {stats.workplace_distribution.get('onsite', 0)}",
            "",
            "---",
            "",
            "## 🏆 Top Overall Tech Skills",
            "| Rank | Technology | Category | Demand (% of Jobs) | Weighted Score |",
            "|---|---|---|---|---|"
        ]

        for idx, item in enumerate(stats.top_skills_overall[:15], 1):
            md_lines.append(f"| {idx} | **{item['skill']}** | {item['category']} | {item['percentage']}% ({item['count']}) | {item['weighted_score']} |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 🔗 Top Skill Co-Occurrences & Synergies",
            "| Primary Skill | Paired Skill | Shared Job Count | Synergy (%) |",
            "|---|---|---|---|"
        ])

        for pair in stats.co_occurrences[:10]:
            md_lines.append(f"| **{pair.skill_a}** | **{pair.skill_b}** | {pair.count} | {pair.percentage}% |")

        # Seniority compensation table
        if stats.experience_salary_stats:
            md_lines.extend([
                "",
                "---",
                "",
                "## 💵 Compensation Benchmarks by Seniority Tier",
                "| Experience Tier | Median Annual Salary | Salary Range | Sample Size |",
                "|---|---|---|---|"
            ])
            order = ["entry", "mid", "senior", "lead", "executive"]
            sorted_tiers = sorted(
                stats.experience_salary_stats.keys(),
                key=lambda x: order.index(x.lower()) if x.lower() in order else 99
            )
            for tier in sorted_tiers:
                t_data = stats.experience_salary_stats[tier]
                md_lines.append(f"| **{tier.capitalize()}** | ${t_data['median']:,.0f} | ${t_data['min']:,.0f} - ${t_data['max']:,.0f} | {int(t_data['count'])} |")

        # Top hiring companies table
        if stats.top_hiring_companies:
            md_lines.extend([
                "",
                "---",
                "",
                "## 🏢 Top Actively Hiring Employers",
                "| Company | Open Positions | Market Share (%) | Key Tech Stack |",
                "|---|---|---|---|"
            ])
            for comp in stats.top_hiring_companies[:10]:
                tech_tags = ", ".join(comp.get("top_skills", [])[:4])
                md_lines.append(f"| **{comp['company']}** | {comp['job_count']} | {comp['percentage']}% | {tech_tags or 'N/A'} |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 🌍 Geographic & Regional Breakdown",
            "| Region | Analyzed Postings | Top Demanded Technologies |",
            "|---|---|---|"
        ])

        for reg_name, geo_data in stats.geo_breakdown.items():
            top_3 = ", ".join([f"{s['skill']} ({s['percentage']}%)" for s in geo_data.top_skills[:4]])
            md_lines.append(f"| **{reg_name}** | {geo_data.total_jobs} | {top_3 or 'N/A'} |")

        md_lines.append("\n*Report compiled with StackCheck Intelligence Engine.*")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        return out_path
