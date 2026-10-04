# Graph Report - StackCheck  (2026-10-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 338 nodes · 785 edges · 13 communities (9 shown, 4 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 123 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `80ae786a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- JobPost
- HiringCafeClient
- WorkplaceType
- web/app.py
- JobRepository
- main
- UpdateChecker
- CommunitySyncClient
- install.sh
- stackcheck

## God Nodes (most connected - your core abstractions)
1. `JobRepository` - 39 edges
2. `JobPost` - 26 edges
3. `main()` - 26 edges
4. `MetricsEngine` - 23 edges
5. `WorkplaceType` - 21 edges
6. `AggregatedStats` - 19 edges
7. `HiringCafeClient` - 19 edges
8. `ExtractedSkill` - 19 edges
9. `JobNormalizer` - 19 edges
10. `Region` - 19 edges

## Surprising Connections (you probably didn't know these)
- `test_charts_generation()` --uses--> `MetricsEngine`  [INFERRED]
  tests/test_web.py → src/stackcheck/analyzer/metrics.py
- `test_duplicate_detection_and_apply_urls()` --uses--> `JobPost`  [INFERRED]
  tests/test_storage.py → src/stackcheck/models.py
- `test_project_isolation_and_crud()` --uses--> `JobPost`  [INFERRED]
  tests/test_storage.py → src/stackcheck/models.py
- `test_repository_save_and_retrieve()` --uses--> `JobPost`  [INFERRED]
  tests/test_storage.py → src/stackcheck/models.py
- `create_sample_jobs()` --uses--> `JobPost`  [INFERRED]
  tests/test_web.py → src/stackcheck/models.py

## Import Cycles
- None detected.

## Communities (13 total, 4 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.06
Nodes (19): list_projects(), main(), projects(), status(), stop(), web(), cleanup_instance_files(), get_running_instance() (+11 more)

### Community 1 - "JobPost"
Cohesion: 0.09
Nodes (15): MetricsEngine, analyze(), create_project(), delete_project(), export(), search(), AggregatedStats, GeoTechBreakdown (+7 more)

### Community 2 - "HiringCafeClient"
Cohesion: 0.07
Nodes (11): LLMExtractor, compile_pattern(), extract_bullet_points(), RuleExtractor, segment_job_description(), HiringCafeClient, ExtractedSkill, test_rule_extractor_positional_weighting() (+3 more)

### Community 4 - "WorkplaceType"
Cohesion: 0.11
Nodes (10): JobNormalizer, ExperienceLevel, Region, SalaryInfo, TechCategory, WorkplaceType, test_job_normalizer(), test_location_normalization() (+2 more)

### Community 5 - "web/app.py"
Cohesion: 0.08
Nodes (5): build(), get_streamlit_static_dir(), find_free_port(), _resolve_stackcheck_dir(), test_find_free_port()

### Community 6 - "JobRepository"
Cohesion: 0.08
Nodes (6): Project, SearchQuery, DatabaseManager, JobRepository, test_duplicate_detection_and_apply_urls(), test_project_isolation_and_crud()

### Community 7 - "main"
Cohesion: 0.13
Nodes (7): main(), plot_category_breakdown(), plot_co_occurrence_heatmap(), plot_distributions(), plot_salary_by_tech(), plot_top_skills(), test_charts_generation()

### Community 8 - "UpdateChecker"
Cohesion: 0.17
Nodes (3): update(), UpdateChecker, test_updater_check_offline_or_invalid()

### Community 10 - "install.sh"
Cohesion: 0.43
Nodes (6): download_with_progress(), install.sh script, step_error(), step_header(), step_item(), step_warn()

## Knowledge Gaps
- **1 isolated node(s):** `stackcheck`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 151 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JobRepository` connect `JobRepository` to `cli.py`, `JobPost`, `HiringCafeClient`, `models.py`, `WorkplaceType`, `web/app.py`, `CommunitySyncClient`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `main()` connect `main` to `cli.py`, `JobPost`, `WorkplaceType`, `web/app.py`, `JobRepository`, `UpdateChecker`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `JobPost` connect `JobPost` to `HiringCafeClient`, `models.py`, `WorkplaceType`, `JobRepository`, `main`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `JobRepository` (e.g. with `analyze()` and `create_project()`) actually correct?**
  _`JobRepository` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `JobPost` (e.g. with `MetricsEngine` and `HiringCafeClient`) actually correct?**
  _`JobPost` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `main()` (e.g. with `MetricsEngine` and `JobNormalizer`) actually correct?**
  _`main()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `MetricsEngine` (e.g. with `AggregatedStats` and `GeoTechBreakdown`) actually correct?**
  _`MetricsEngine` has 15 INFERRED edges - model-reasoned connections that need verification._