"""
Matplotlib (OOP API) and Seaborn Visualization Engine for StackCheck Web Dashboard.
Produces statistical charts with high-contrast dark theme styling, clean typography,
and accessible data annotations aligned with the application interface.
"""

from typing import List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

from stackcheck.models import AggregatedStats, JobPost


# Dark slate design system tokens (unified single-tone background)
CARD_BG = "#162036"          # Seamless dark slate canvas facecolor
TEXT_TITLE = "#F8FAFC"       # Off-white / slate-50 (maximum crisp contrast)
TEXT_LABEL = "#E2E8F0"       # Slate-200 (axes labels)
TEXT_TICK = "#CBD5E1"        # Slate-300 (tick labels)
TEXT_DATA = "#38BDF8"        # Electric sky blue (bar labels, metrics, high visibility)
TEXT_MUTED = "#94A3B8"       # Slate-400 (secondary captions, whiskers)
GRID_COLOR = "#23334D"       # Subtle slate grid lines
SPINE_COLOR = "#334155"      # Slate axis border
LEGEND_BG = "#1E293B"        # Legend box background
LEGEND_BORDER = "#334155"    # Legend border


def _apply_chart_theme(fig: plt.Figure, ax: plt.Axes, grid_axis: str = "x") -> None:
    """Apply unified dark slate theme with high-contrast text and subtle grid."""
    fig.patch.set_facecolor(CARD_BG)
    ax.set_facecolor(CARD_BG)
    
    # Tick colors and font size
    ax.tick_params(colors=TEXT_TICK, labelsize=9.5)
    
    # Visible axis spines
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    # Subtle grid
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID_COLOR, linestyle="--", linewidth=0.7, alpha=0.6, zorder=0)
    else:
        ax.grid(False)


def plot_top_skills(stats: AggregatedStats, top_n: int = 15, use_weighted: bool = False) -> Optional[plt.Figure]:
    """
    Generate horizontal bar chart of top demanded skills using Matplotlib OOP API.
    Includes high-contrast data labels and category color coding.
    """
    items = stats.weighted_top_skills if use_weighted else stats.top_skills_overall
    if not items:
        return None

    top_items = items[:top_n]
    df = pd.DataFrame(top_items)
    
    # Sort for bottom-up horizontal plotting
    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(5, int(top_n * 0.38))), dpi=150)
    
    # Reversed crest palette ensures top-ranking skills have high visual luminance
    palette = sns.color_palette("crest_r", n_colors=len(df))
    bars = ax.barh(df["skill"], df["percentage"], color=palette, height=0.65, edgecolor="none", zorder=3)

    max_val = df["percentage"].max() if not df.empty else 100

    # Add high-contrast direct percentage annotations on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + max_val * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}%",
            ha="left",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=TEXT_DATA
        )

    metric_name = "Section-Weighted Demand" if use_weighted else "Job Market Demand (% of Postings)"
    ax.set_title(f"Top {len(df)} Demanded Tech Skills ({metric_name})", fontsize=13, fontweight="bold", pad=16, color=TEXT_TITLE)
    ax.set_xlabel("Market Frequency / Requirement Weight (%)", fontsize=10, fontweight="semibold", color=TEXT_LABEL)
    ax.set_ylabel("Technology", fontsize=10, fontweight="semibold", color=TEXT_LABEL)
    
    ax.set_xlim(0, max_val * 1.22)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
    
    _apply_chart_theme(fig, ax, grid_axis="x")
    fig.tight_layout()
    return fig


def plot_co_occurrence_heatmap(stats: AggregatedStats, top_n: int = 10) -> Optional[plt.Figure]:
    """
    Generate a pairwise co-occurrence correlation matrix heatmap using Seaborn.
    Visualizes which tech stacks frequently appear together in the same job postings.
    """
    if not stats.top_skills_overall or not stats.co_occurrences:
        return None

    top_skills = [s["skill"] for s in stats.top_skills_overall[:top_n]]
    matrix_df = pd.DataFrame(0, index=top_skills, columns=top_skills)

    for co in stats.co_occurrences:
        if co.skill_a in top_skills and co.skill_b in top_skills:
            matrix_df.loc[co.skill_a, co.skill_b] = co.count
            matrix_df.loc[co.skill_b, co.skill_a] = co.count

    # Diagonal represents total mentions for skill
    for s in stats.top_skills_overall:
        if s["skill"] in top_skills:
            matrix_df.loc[s["skill"], s["skill"]] = s["count"]

    fig, ax = plt.subplots(figsize=(8.5, 7), dpi=150)
    fig.patch.set_facecolor(CARD_BG)
    ax.set_facecolor(CARD_BG)
    
    sns.heatmap(
        matrix_df,
        annot=True,
        fmt="d",
        cmap="mako",
        linewidths=1.0,
        linecolor=CARD_BG,
        cbar_kws={"label": "Postings Mentioning Both Technologies"},
        annot_kws={"size": 9.5, "weight": "bold"},
        ax=ax,
        square=True
    )

    ax.set_title("Technology Co-Occurrence Matrix", fontsize=13, fontweight="bold", pad=16, color=TEXT_TITLE)
    ax.tick_params(colors=TEXT_TICK, labelsize=9.5)
    
    # Style the colorbar with readable text and ticks
    if ax.collections and ax.collections[0].colorbar:
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(colors=TEXT_TICK, labelsize=8.5)
        cbar.set_label("Postings Mentioning Both Technologies", color=TEXT_LABEL, fontsize=9.5, fontweight="semibold")
        cbar.outline.set_edgecolor(SPINE_COLOR)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9.5, fontweight="semibold", color=TEXT_TICK)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=9.5, fontweight="semibold", color=TEXT_TICK)
    
    fig.tight_layout()
    return fig


def plot_salary_by_tech(
    stats: AggregatedStats, 
    min_samples: int = 3, 
    top_n: int = 12,
    sort_by: str = "avg_salary"
) -> Optional[plt.Figure]:
    """
    Generate grouped salary comparison (Min, Avg, Max) with sample size protection
    and collision-free label layout.
    """
    if not stats.salary_by_top_tech:
        return None

    # Collect candidate records
    all_records = []
    for skill, s_info in stats.salary_by_top_tech.items():
        samples = s_info.get("samples", 0)
        avg_sal = s_info.get("avg", 0)
        if samples > 0 and avg_sal > 0:
            all_records.append({
                "Skill": skill,
                "Min Salary": s_info.get("min", 0),
                "Avg Salary": avg_sal,
                "Max Salary": s_info.get("max", 0),
                "Samples": samples
            })

    if not all_records:
        return None

    # Filter by minimum sample size; gracefully fall back if threshold excludes all data
    data = [r for r in all_records if r["Samples"] >= min_samples]
    if len(data) < 3 and min_samples > 1:
        data = [r for r in all_records if r["Samples"] >= 1]

    if not data:
        return None

    df = pd.DataFrame(data)

    # Sort logic
    if sort_by == "sample_count":
        df = df.sort_values(by=["Samples", "Avg Salary"], ascending=[True, True]).tail(top_n)
    else:
        df = df.sort_values(by=["Avg Salary", "Samples"], ascending=[True, True]).tail(top_n)

    fig, ax = plt.subplots(figsize=(9.8, max(5.0, len(df) * 0.52)), dpi=150)

    y_pos = np.arange(len(df))
    height = 0.48

    # Plot average bar in bright cyan
    bars = ax.barh(y_pos, df["Avg Salary"], height=height, color="#38BDF8", alpha=0.9, label="Average Salary", zorder=3)

    # Add error bar range from Min to Max
    err_min = df["Avg Salary"] - df["Min Salary"]
    err_max = df["Max Salary"] - df["Avg Salary"]
    ax.errorbar(
        df["Avg Salary"],
        y_pos,
        xerr=[err_min, err_max],
        fmt="none",
        ecolor=TEXT_MUTED,
        elinewidth=1.6,
        capsize=4,
        capthick=1.4,
        label="Salary Range (Min - Max)",
        zorder=4
    )

    # Place average salary annotation directly above each bar to prevent whisker collision
    for bar, avg_val in zip(bars, df["Avg Salary"]):
        ax.text(
            avg_val,
            bar.get_y() + height + 0.05,
            f"${avg_val:,.0f} avg",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=TEXT_DATA,
            zorder=5
        )

    # Include sample size in tick labels
    formatted_labels = [f"{row['Skill']}  (n={int(row['Samples'])})" for _, row in df.iterrows()]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(formatted_labels, fontsize=9.5, fontweight="semibold", color=TEXT_TICK)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x*1e-3:,.0f}k"))
    
    max_x_val = max(df["Max Salary"].max(), df["Avg Salary"].max())
    ax.set_xlim(0, max_x_val * 1.10)
    ax.set_ylim(-0.6, len(df) - 0.2)
    
    # Title with generous top padding to prevent legend collision
    ax.set_title("Salary Benchmarks by Technology (USD / Yr)", fontsize=13, fontweight="bold", pad=16, color=TEXT_TITLE)
    ax.set_xlabel("Compensation ($ USD)", fontsize=10, fontweight="semibold", color=TEXT_LABEL)
    
    # Place legend cleanly below x-axis to prevent collision with title or data
    leg = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=False,
        fontsize=8.5
    )
    for t in leg.get_texts():
        t.set_color(TEXT_TICK)
    
    _apply_chart_theme(fig, ax, grid_axis="x")
    fig.tight_layout()
    return fig


def plot_distributions(stats: AggregatedStats) -> Tuple[Optional[plt.Figure], Optional[plt.Figure]]:
    """
    Generate Workplace and Experience level distribution charts.
    """
    fig_wp, fig_exp = None, None

    # 1. Workplace Distribution Pie Chart
    if stats.workplace_distribution:
        fig_wp, ax_wp = plt.subplots(figsize=(5.5, 4), dpi=150)
        fig_wp.patch.set_facecolor(CARD_BG)
        ax_wp.set_facecolor(CARD_BG)
        
        wp_labels = [k.capitalize() for k in stats.workplace_distribution.keys()]
        wp_values = list(stats.workplace_distribution.values())
        colors = ["#38BDF8", "#818CF8", "#34D399", "#F472B6", "#FBBF24"][:len(wp_labels)]
        
        wedges, texts, autotexts = ax_wp.pie(
            wp_values,
            labels=wp_labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops={"edgecolor": CARD_BG, "linewidth": 2.5, "antialiased": True}
        )
        for t in texts:
            t.set_color(TEXT_TICK)
            t.set_fontsize(9.5)
            t.set_fontweight("semibold")
        for at in autotexts:
            at.set_color("#0D1527")
            at.set_fontsize(9.0)
            at.set_fontweight("bold")
            
        ax_wp.set_title("Workplace Mode Distribution", fontsize=11.5, fontweight="bold", pad=12, color=TEXT_TITLE)
        fig_wp.tight_layout()

    # 2. Experience Distribution Bar Chart
    if stats.experience_distribution:
        fig_exp, ax_exp = plt.subplots(figsize=(5.5, 4), dpi=150)
        exp_labels = [k.capitalize() for k in stats.experience_distribution.keys()]
        exp_values = list(stats.experience_distribution.values())
        palette = sns.color_palette("crest_r", len(exp_labels))
        
        bars = ax_exp.bar(exp_labels, exp_values, color=palette, edgecolor="none", width=0.6, zorder=3)
        for bar in bars:
            height = bar.get_height()
            ax_exp.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.15,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
                color=TEXT_DATA
            )
            
        max_h = max(exp_values) if exp_values else 10
        ax_exp.set_ylim(0, max_h * 1.25)
        ax_exp.set_title("Experience Level Breakdown", fontsize=11.5, fontweight="bold", pad=12, color=TEXT_TITLE)
        ax_exp.set_ylabel("Job Postings Count", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
        plt.setp(ax_exp.get_xticklabels(), rotation=20, ha="right", fontsize=8.5, color=TEXT_TICK)
        
        _apply_chart_theme(fig_exp, ax_exp, grid_axis="y")
        fig_exp.tight_layout()

    return fig_wp, fig_exp


def plot_category_breakdown(stats: AggregatedStats) -> Optional[plt.Figure]:
    """
    Generate horizontal bar chart comparing aggregate demand across tech categories.
    """
    if not stats.category_breakdown:
        return None

    cat_totals = []
    for cat_name, skill_list in stats.category_breakdown.items():
        total_mentions = sum(s["count"] for s in skill_list)
        cat_totals.append({"Category": cat_name, "Total Mentions": total_mentions})

    df = pd.DataFrame(cat_totals).sort_values(by="Total Mentions", ascending=True)
    if df.empty:
        return None

    fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=150)
    palette = sns.color_palette("crest_r", len(df))
    
    bars = ax.barh(df["Category"], df["Total Mentions"], color=palette, height=0.6, zorder=3)
    max_w = df["Total Mentions"].max() if not df.empty else 10
    
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + max_w * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)}",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=TEXT_DATA
        )

    ax.set_xlim(0, max_w * 1.20)
    ax.set_title("Aggregate Skill Mentions by Domain Category", fontsize=12.5, fontweight="bold", pad=14, color=TEXT_TITLE)
    ax.set_xlabel("Total Frequency across Postings", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
    
    _apply_chart_theme(fig, ax, grid_axis="x")
    fig.tight_layout()
    return fig


def plot_salary_by_country_scatter(country_salary_data: List[dict], color_by: str = "experience") -> Optional[plt.Figure]:
    """
    Generate a categorical strip/scatter plot with horizontal jitter showing
    compensation distributions across countries, annotated with median markers.
    """
    if not country_salary_data or len(country_salary_data) < 2:
        return None

    df = pd.DataFrame(country_salary_data)
    if df.empty or "country" not in df.columns or "salary_k" not in df.columns:
        return None

    # Filter to countries with valid values and guard against > $600k anomalies
    df = df[(df["salary_k"] > 5.0) & (df["salary_k"] <= 600.0)].copy()
    if df.empty:
        return None

    country_counts = df["country"].value_counts()
    top_countries = country_counts.head(12).index.tolist()
    df = df[df["country"].isin(top_countries)].copy()

    # Calculate median salary per country for ordering
    country_medians = df.groupby("country")["salary_k"].median().sort_values(ascending=False)
    order = country_medians.index.tolist()

    num_countries = len(order)
    fig_width = max(9.5, min(14.0, num_countries * 0.95 + 2.5))
    rot_angle = 35 if num_countries > 6 else 20
    fig, ax = plt.subplots(figsize=(fig_width, 5.5), dpi=150)

    # Determine hue column and palette
    hue_col = "experience" if color_by == "experience" and "experience" in df.columns else "workplace"
    palette_name = "crest"

    sns.stripplot(
        data=df,
        x="country",
        y="salary_k",
        hue=hue_col,
        order=order,
        jitter=0.25,
        alpha=0.85,
        size=7.5,
        palette=palette_name,
        edgecolor=CARD_BG,
        linewidth=0.8,
        ax=ax,
        zorder=3
    )

    # Overlay horizontal median line indicators for each country
    max_sal = max(df["salary_k"]) if not df.empty else 200
    for idx, c_name in enumerate(order):
        c_med = country_medians[c_name]
        ax.hlines(
            y=c_med,
            xmin=idx - 0.32,
            xmax=idx + 0.32,
            colors="#FB7185",
            linestyles="solid",
            linewidths=2.8,
            zorder=5
        )
        ax.text(
            idx,
            c_med + (max_sal * 0.025),
            f"${int(c_med)}k",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#FDA4AF",
            zorder=6
        )

    ax.set_title("Annual Compensation Distribution by Country ($k USD)", fontsize=13, fontweight="bold", pad=16, color=TEXT_TITLE)
    ax.set_xlabel("Country / Region (Sorted by Median)", fontsize=10, fontweight="semibold", color=TEXT_LABEL)
    ax.set_ylabel("Annual Salary ($k USD)", fontsize=10, fontweight="semibold", color=TEXT_LABEL)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"${int(x)}k"))

    plt.setp(ax.get_xticklabels(), rotation=rot_angle, ha="right", fontsize=9, fontweight="medium", color=TEXT_TICK)

    # Legend formatting
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        leg = ax.legend(
            handles=handles,
            labels=labels,
            title=hue_col.capitalize(),
            title_fontsize=9.5,
            fontsize=8.5,
            frameon=True,
            facecolor=LEGEND_BG,
            edgecolor=LEGEND_BORDER,
            loc="upper right"
        )
        if leg.get_title():
            leg.get_title().set_color(TEXT_TITLE)
        for t in leg.get_texts():
            t.set_color(TEXT_TICK)

    _apply_chart_theme(fig, ax, grid_axis="y")
    fig.tight_layout()
    return fig


def plot_top_hiring_companies(companies_data: List[dict], top_n: int = 10) -> Optional[plt.Figure]:
    """
    Generate horizontal bar chart of top hiring companies with demanded skill tags.
    Includes right margin protection and skill tag truncation to prevent overflow.
    """
    if not companies_data:
        return None

    items = companies_data[:top_n]
    df = pd.DataFrame(items)
    if df.empty or "company" not in df.columns or "job_count" not in df.columns:
        return None

    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(4.8, int(len(df) * 0.44))), dpi=150)
    palette = sns.color_palette("crest_r", n_colors=len(df))

    bars = ax.barh(df["company"], df["job_count"], color=palette, height=0.62, edgecolor="none", zorder=3)
    max_count = max(df["job_count"]) if not df.empty else 10

    for bar, (_, row) in zip(bars, df.iterrows()):
        width = bar.get_width()
        raw_skills = row.get("top_skills", [])[:2]
        skills_str = ", ".join(raw_skills)
        if len(skills_str) > 28:
            skills_str = skills_str[:26] + "…"
        tag = f" ({skills_str})" if skills_str else ""
        ax.text(
            width + max_count * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)} jobs{tag}",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color=TEXT_DATA,
            zorder=5
        )

    ax.set_title(f"Top {len(df)} Actively Hiring Employers", fontsize=12.5, fontweight="bold", pad=16, color=TEXT_TITLE)
    ax.set_xlabel("Open Positions Found", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
    ax.set_xlim(0, max_count * 1.55)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    _apply_chart_theme(fig, ax, grid_axis="x")
    fig.tight_layout()
    return fig


def plot_experience_skill_matrix(experience_skills_breakdown: dict) -> Optional[plt.Figure]:
    """
    Compare top demanded skills between Entry-Level vs Senior roles.
    """
    if not experience_skills_breakdown:
        return None

    # Compare Entry vs Senior
    entry_skills = {item["skill"]: item["percentage"] for item in experience_skills_breakdown.get("entry", [])}
    senior_skills = {item["skill"]: item["percentage"] for item in experience_skills_breakdown.get("senior", [])}

    all_keys = list(dict.fromkeys(list(senior_skills.keys()) + list(entry_skills.keys())))[:8]
    if not all_keys:
        return None

    chart_data = []
    for skill in all_keys:
        chart_data.append({
            "Skill": skill,
            "Senior (%)": senior_skills.get(skill, 0.0),
            "Entry (%)": entry_skills.get(skill, 0.0)
        })

    df = pd.DataFrame(chart_data)
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=150)

    y = np.arange(len(df))
    height = 0.36

    ax.barh(y - height/2, df["Senior (%)"], height, label="Senior Roles", color="#38BDF8", alpha=0.9, zorder=3)
    ax.barh(y + height/2, df["Entry (%)"], height, label="Entry Roles", color="#10B981", alpha=0.9, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(df["Skill"], fontsize=9.5, fontweight="semibold", color=TEXT_TICK)
    ax.invert_yaxis()

    ax.set_title("Skill Expectations: Entry-Level vs Senior Roles", fontsize=12.5, fontweight="bold", pad=14, color=TEXT_TITLE)
    ax.set_xlabel("Demand Frequency (%) in Level Postings", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=100))
    
    leg = ax.legend(
        loc="lower right",
        frameon=True,
        facecolor=LEGEND_BG,
        edgecolor=LEGEND_BORDER,
        fontsize=9
    )
    for t in leg.get_texts():
        t.set_color(TEXT_TITLE)

    _apply_chart_theme(fig, ax, grid_axis="x")
    fig.tight_layout()
    return fig


def plot_stack_density_distribution(stack_density_stats: dict) -> Optional[plt.Figure]:
    """
    Plot the distribution of required technologies per job posting (Tech Breadth).
    """
    dist = stack_density_stats.get("distribution", {})
    if not dist:
        return None

    sorted_counts = sorted(dist.items(), key=lambda x: x[0])
    x_vals = [k for k, _ in sorted_counts if k > 0][:15]
    y_vals = [v for k, v in sorted_counts if k > 0][:15]

    if not x_vals:
        return None

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    bars = ax.bar(x_vals, y_vals, color="#6366F1", width=0.68, edgecolor="#818CF8", alpha=0.9, zorder=3)

    avg_val = stack_density_stats.get("avg_skills_per_job", 0)
    if avg_val > 0:
        ax.axvline(avg_val, color="#FB7185", linestyle="--", linewidth=1.8, label=f"Average ({avg_val} skills/job)", zorder=5)
        leg = ax.legend(loc="upper right", frameon=True, facecolor=LEGEND_BG, edgecolor=LEGEND_BORDER, fontsize=9)
        for t in leg.get_texts():
            t.set_color(TEXT_TITLE)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.15,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=TEXT_DATA
        )

    max_y = max(y_vals) if y_vals else 10
    ax.set_ylim(0, max_y * 1.25)
    ax.set_title("Stack Complexity: Required Technologies per Posting", fontsize=12.5, fontweight="bold", pad=14, color=TEXT_TITLE)
    ax.set_xlabel("Distinct Required Skills Count", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
    ax.set_ylabel("Number of Postings", fontsize=9.5, fontweight="semibold", color=TEXT_LABEL)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    _apply_chart_theme(fig, ax, grid_axis="y")
    fig.tight_layout()
    return fig
