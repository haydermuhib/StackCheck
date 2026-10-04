"""
Analytics and Metrics Aggregator:
- Skill frequency & rank
- Section-weighted priority score
- Geographic & work-mode segmentation
- Co-occurrence matrix
- Salary correlation
"""

import statistics
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from itertools import combinations
from stackcheck.models import JobPost, AggregatedStats, SkillCoOccurrence, GeoTechBreakdown, Region, WorkplaceType, TechCategory
from stackcheck.analyzer.currency import currency_manager


class MetricsEngine:
    """Computes multidimensional analytics on processed job postings."""

    @staticmethod
    def aggregate(jobs: List[JobPost], query_keywords: str = "All") -> AggregatedStats:
        total_jobs = len(jobs)
        if total_jobs == 0:
            return AggregatedStats(
                query_keywords=query_keywords,
                total_jobs=0,
                unique_companies=0,
                workplace_distribution={},
                experience_distribution={},
                category_breakdown={},
                top_skills_overall=[],
                weighted_top_skills=[],
                co_occurrences=[],
                geo_breakdown={},
                salary_by_top_tech={}
            )

        unique_companies = len({j.company.lower().strip() for j in jobs if j.company})
        workplace_dist: Dict[str, int] = Counter([j.workplace_type.value for j in jobs])
        experience_dist: Dict[str, int] = Counter([j.experience_level.value for j in jobs])

        # Raw skill counts and weighted scores
        skill_counts: Dict[str, int] = Counter()
        skill_weights: Dict[str, float] = defaultdict(float)
        skill_categories: Dict[str, str] = {}
        category_skills: Dict[str, Counter] = defaultdict(Counter)

        # Co-occurrence pairs
        co_occurrence_counter: Counter = Counter()

        # Geographic partitions
        geo_jobs: Dict[Region, List[JobPost]] = defaultdict(list)

        # Salary tracking by tech
        salary_tech_map: Dict[str, List[float]] = defaultdict(list)

        for job in jobs:
            geo_jobs[job.region].append(job)
            
            # Extract unique skills in this job to avoid duplicate counts within a single job
            job_skills_seen = set()
            job_skill_names = []

            for s in job.extracted_skills:
                canon = s.canonical_name
                skill_categories[canon] = s.category.value
                
                if canon not in job_skills_seen:
                    skill_counts[canon] += 1
                    category_skills[s.category.value][canon] += 1
                    job_skills_seen.add(canon)
                    job_skill_names.append(canon)

                skill_weights[canon] += s.priority_weight

                # Salary tracking if salary available
                if job.salary and (job.salary.min_amount or job.salary.max_amount):
                    avg_sal = job.salary.min_amount or job.salary.max_amount or 0
                    if job.salary.min_amount and job.salary.max_amount:
                        avg_sal = (job.salary.min_amount + job.salary.max_amount) / 2.0
                    usd_val = currency_manager.convert_to_usd(
                        amount=avg_sal,
                        currency=job.salary.currency,
                        country=job.country or job.location,
                        period=job.salary.period
                    )
                    if 5000 <= usd_val <= 750000:
                        salary_tech_map[canon].append(usd_val)

            # Calculate pairwise co-occurrences for this job
            sorted_skills = sorted(list(job_skills_seen))
            for pair in combinations(sorted_skills, 2):
                co_occurrence_counter[pair] += 1

        # 1. Top Skills Overall
        top_skills_overall = []
        for skill, count in skill_counts.most_common(30):
            top_skills_overall.append({
                "skill": skill,
                "category": skill_categories.get(skill, "Other"),
                "count": count,
                "percentage": round((count / total_jobs) * 100, 1),
                "weighted_score": round(skill_weights[skill], 1)
            })

        # 2. Weighted Top Skills (Ranked by Requirement priority)
        weighted_top_skills = sorted([
            {
                "skill": skill,
                "category": skill_categories.get(skill, "Other"),
                "count": skill_counts[skill],
                "percentage": round((skill_counts[skill] / total_jobs) * 100, 1),
                "weighted_score": round(weight, 1)
            }
            for skill, weight in skill_weights.items()
        ], key=lambda x: x["weighted_score"], reverse=True)[:30]

        # 3. Category Breakdown
        category_breakdown: Dict[str, List[Dict[str, Any]]] = {}
        for cat_name, counter in category_skills.items():
            category_breakdown[cat_name] = [
                {
                    "skill": skill,
                    "count": count,
                    "percentage": round((count / total_jobs) * 100, 1),
                    "weighted_score": round(skill_weights[skill], 1)
                }
                for skill, count in counter.most_common(12)
            ]

        # 4. Co-occurrences (Top 25 synergistic pairs)
        co_occurrences: List[SkillCoOccurrence] = []
        for (a, b), count in co_occurrence_counter.most_common(25):
            pct = round((count / total_jobs) * 100, 1)
            co_occurrences.append(SkillCoOccurrence(
                skill_a=a,
                skill_b=b,
                count=count,
                percentage=pct
            ))

        # 5. Geographic Segmentation
        geo_breakdown: Dict[str, GeoTechBreakdown] = {}
        for region, reg_jobs in geo_jobs.items():
            reg_total = len(reg_jobs)
            reg_counts: Counter = Counter()
            reg_workplace: Counter = Counter([j.workplace_type.value for j in reg_jobs])
            
            for j in reg_jobs:
                seen = {s.canonical_name for s in j.extracted_skills}
                for s in seen:
                    reg_counts[s] += 1

            top_reg_skills = [
                {
                    "skill": s,
                    "count": cnt,
                    "percentage": round((cnt / reg_total) * 100, 1)
                }
                for s, cnt in reg_counts.most_common(8)
            ]
            geo_breakdown[region.value] = GeoTechBreakdown(
                region=region,
                total_jobs=reg_total,
                top_skills=top_reg_skills,
                workplace_distribution=dict(reg_workplace)
            )

        # 6. Salary by Tech Stack (Top technologies with at least 1 salary sample)
        salary_by_top_tech: Dict[str, Dict[str, float]] = {}
        for skill, salaries in salary_tech_map.items():
            if len(salaries) >= 1:
                avg_val = sum(salaries) / len(salaries)
                min_val = min(salaries)
                max_val = max(salaries)
                salary_by_top_tech[skill] = {
                    "avg": round(avg_val, 0),
                    "min": round(min_val, 0),
                    "max": round(max_val, 0),
                    "samples": len(salaries)
                }

        # 7. Job Market Metrics: Transparency & Country Scatter Records
        country_salary_data = []
        salaries_all = []
        salaries_by_exp: Dict[str, List[float]] = defaultdict(list)
        skills_by_exp: Dict[str, Counter] = defaultdict(Counter)
        salaries_by_workplace: Dict[str, List[float]] = defaultdict(list)
        company_jobs_counter: Counter = Counter()
        company_skills_map: Dict[str, Counter] = defaultdict(Counter)
        skills_per_job_list = []

        for job in jobs:
            comp_clean = job.company.strip() if job.company else "Unknown"
            if comp_clean and comp_clean != "Unknown":
                company_jobs_counter[comp_clean] += 1

            job_unique_skills = {s.canonical_name for s in job.extracted_skills}
            skills_per_job_list.append(len(job_unique_skills))

            for s in job_unique_skills:
                skills_by_exp[job.experience_level.value][s] += 1
                if comp_clean and comp_clean != "Unknown":
                    company_skills_map[comp_clean][s] += 1

            if job.salary and (job.salary.min_amount or job.salary.max_amount):
                raw_val = job.salary.min_amount or job.salary.max_amount or 0
                if job.salary.min_amount and job.salary.max_amount:
                    raw_val = (job.salary.min_amount + job.salary.max_amount) / 2.0
                
                usd_val = currency_manager.convert_to_usd(
                    amount=raw_val,
                    currency=job.salary.currency,
                    country=job.country or job.location,
                    period=job.salary.period
                )

                if 5000 <= usd_val <= 750000:  # Sensible global annual salary bounds in USD
                    norm_val = round(usd_val, 0)
                    salaries_all.append(norm_val)
                    salaries_by_exp[job.experience_level.value].append(norm_val)
                    salaries_by_workplace[job.workplace_type.value].append(norm_val)

                    c_name = job.country or (job.region.value if job.region != Region.OTHER else "Global Remote")
                    country_salary_data.append({
                        "country": c_name,
                        "salary": norm_val,
                        "salary_k": round(norm_val / 1000.0, 1),
                        "experience": job.experience_level.value.capitalize(),
                        "workplace": job.workplace_type.value.capitalize(),
                        "title": job.title,
                        "company": comp_clean
                    })

        salary_transparency_pct = round((len(salaries_all) / total_jobs) * 100, 1)

        # 8. Experience Seniority Salary & Skill Tiering
        experience_salary_stats: Dict[str, Dict[str, float]] = {}
        for exp_key, s_list in salaries_by_exp.items():
            if s_list:
                experience_salary_stats[exp_key] = {
                    "min": round(min(s_list), 0),
                    "median": round(statistics.median(s_list), 0),
                    "max": round(max(s_list), 0),
                    "avg": round(sum(s_list) / len(s_list), 0),
                    "count": len(s_list)
                }

        experience_skills_breakdown: Dict[str, List[Dict[str, Any]]] = {}
        for exp_key, c_counter in skills_by_exp.items():
            exp_total = experience_dist.get(exp_key, 1) or 1
            experience_skills_breakdown[exp_key] = [
                {
                    "skill": s,
                    "count": cnt,
                    "percentage": round((cnt / exp_total) * 100, 1)
                }
                for s, cnt in c_counter.most_common(6)
            ]

        # 9. Workplace Salary Differentials (Remote vs Onsite Premium)
        workplace_salary_stats: Dict[str, Dict[str, float]] = {}
        for wp_key, s_list in salaries_by_workplace.items():
            if s_list:
                workplace_salary_stats[wp_key] = {
                    "min": round(min(s_list), 0),
                    "median": round(statistics.median(s_list), 0),
                    "max": round(max(s_list), 0),
                    "count": len(s_list)
                }

        # 10. Top Hiring Companies
        top_hiring_companies = []
        for comp, cnt in company_jobs_counter.most_common(10):
            top_hiring_companies.append({
                "company": comp,
                "job_count": cnt,
                "percentage": round((cnt / total_jobs) * 100, 1),
                "top_skills": [s for s, _ in company_skills_map[comp].most_common(4)]
            })

        # 11. Stack Density (Skills required per job)
        stack_density_stats = {
            "avg_skills_per_job": round(sum(skills_per_job_list) / total_jobs, 1) if skills_per_job_list else 0.0,
            "median_skills": statistics.median(skills_per_job_list) if skills_per_job_list else 0,
            "max_skills": max(skills_per_job_list) if skills_per_job_list else 0,
            "distribution": dict(Counter(skills_per_job_list))
        }

        return AggregatedStats(
            query_keywords=query_keywords,
            total_jobs=total_jobs,
            unique_companies=unique_companies,
            workplace_distribution=dict(workplace_dist),
            experience_distribution=dict(experience_dist),
            category_breakdown=category_breakdown,
            top_skills_overall=top_skills_overall,
            weighted_top_skills=weighted_top_skills,
            co_occurrences=co_occurrences,
            geo_breakdown=geo_breakdown,
            salary_by_top_tech=salary_by_top_tech,
            salary_transparency_pct=salary_transparency_pct,
            country_salary_data=country_salary_data,
            experience_salary_stats=experience_salary_stats,
            experience_skills_breakdown=experience_skills_breakdown,
            top_hiring_companies=top_hiring_companies,
            stack_density_stats=stack_density_stats,
            workplace_salary_stats=workplace_salary_stats
        )

    @staticmethod
    def to_jobs_dataframe(jobs: List[JobPost]):
        """Convert a list of JobPost instances into a tabular Pandas DataFrame."""
        import pandas as pd
        rows = []
        for j in jobs:
            skills_str = ", ".join([s.canonical_name for s in j.extracted_skills])
            sal_str = "Not Disclosed"
            sal_usd = None
            if j.salary:
                raw_amt = j.salary.max_amount or j.salary.min_amount or 0
                usd_amt = currency_manager.convert_to_usd(
                    raw_amt,
                    currency=j.salary.currency,
                    country=j.country or j.location,
                    period=j.salary.period
                )
                if usd_amt > 0:
                    sal_usd = round(usd_amt, 0)
                if (j.salary.currency or "USD").upper() != "USD" and usd_amt > 0:
                    sal_str = f"{j.salary.formatted} (≈ ${usd_amt:,.0f} USD/yr)"
                else:
                    sal_str = j.salary.formatted

            rows.append({
                "Job Title": j.title,
                "Company": j.company,
                "Location": j.location,
                "Country": j.country or "Global",
                "Region": j.region.value,
                "Workplace": j.workplace_type.value.capitalize(),
                "Experience": j.experience_level.value.capitalize(),
                "Salary": sal_str,
                "Salary (USD/yr)": sal_usd,
                "Skills Count": len(j.extracted_skills),
                "Extracted Skills": skills_str,
                "Apply URL": j.link or j.apply_url or j.url or ""
            })
        return pd.DataFrame(rows)

    @staticmethod
    def to_skills_dataframe(stats: AggregatedStats):
        """Convert aggregated skill rankings into a Pandas DataFrame."""
        import pandas as pd
        if not stats.top_skills_overall:
            return pd.DataFrame()
        df = pd.DataFrame(stats.top_skills_overall)
        df.columns = ["Skill", "Category", "Postings Count", "Market Demand %", "Weighted Score"]
        return df

