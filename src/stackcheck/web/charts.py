"""
Matplotlib (OOP API) & Seaborn Visualization Engine for StackCheck Web Dashboard.
Produces high-quality, statistical charts with clean typography, despine styling, and data labels.
"""

from typing import List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

from stackcheck.models import AggregatedStats, JobPost


# Configure sleek styling aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#e2e8f0"
plt.rcParams["axes.linewidth"] = 0.8


def plot_top_skills(stats: AggregatedStats, top_n: int = 15, use_weighted: bool = False) -> Optional[plt.Figure]:
    """
    Generate horizontal bar chart of top demanded skills using Matplotlib OOP API.
    Includes data labels and category color coding.
    """
    items = stats.weighted_top_skills if use_weighted else stats.top_skills_overall
    if not items:
        return None

    top_items = items[:top_n]
    df = pd.DataFrame(top_items)
    
    # Sort for bottom-up horizontal plotting
    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(5, int(top_n * 0.38))), dpi=150)
    
    palette = sns.color_palette("mako", n_colors=len(df))
    bars = ax.barh(df["skill"], df["percentage"], color=palette, height=0.65, edgecolor="none")

    # Add direct percentage annotations on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}%",
            ha="left",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#1e293b"
        )

    metric_name = "Positional Section-Weighted Demand" if use_weighted else "Job Market Demand (% of Postings)"
    ax.set_title(f"Top {len(df)} Demanded Tech Skills ({metric_name})", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
    ax.set_xlabel("Market Frequency / Requirement Weight (%)", fontsize=10, fontweight="semibold", color="#475569")
    ax.set_ylabel("Technology", fontsize=10, fontweight="semibold", color="#475569")
    
    max_val = df["percentage"].max() if not df.empty else 100
    ax.set_xlim(0, max_val * 1.18)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
    
    sns.despine(ax=ax, top=True, right=True, left=False, bottom=False)
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
    
    sns.heatmap(
        matrix_df,
        annot=True,
        fmt="d",
        cmap="Blues",
        linewidths=0.75,
        linecolor="#f1f5f9",
        cbar_kws={"label": "Postings Mentioning Both Techs"},
        ax=ax,
        square=True
    )

    ax.set_title("Tech Stack Synergies & Co-Occurrence Matrix", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
    plt.xticks(rotation=45, ha="right", fontsize=9.5, fontweight="semibold")
    plt.yticks(rotation=0, fontsize=9.5, fontweight="semibold")
    
    fig.tight_layout()
    return fig


def plot_salary_by_tech(stats: AggregatedStats, min_samples: int = 1) -> Optional[plt.Figure]:
    """
    Generate grouped salary comparison (Min, Avg, Max) for top technologies.
    """
    if not stats.salary_by_top_tech:
        return None

    data = []
    for skill, s_info in stats.salary_by_top_tech.items():
        if s_info.get("samples", 0) >= min_samples and s_info.get("avg", 0) > 0:
            data.append({
                "Skill": skill,
                "Min Salary": s_info.get("min", 0),
                "Avg Salary": s_info.get("avg", 0),
                "Max Salary": s_info.get("max", 0),
                "Samples": s_info.get("samples", 0)
            })

    if not data:
        return None

    df = pd.DataFrame(data).sort_values(by="Avg Salary", ascending=True).tail(12)

    fig, ax = plt.subplots(figsize=(9.5, max(4.5, len(df) * 0.4)), dpi=150)

    y_pos = np.arange(len(df))
    height = 0.55

    # Plot average bar
    bars = ax.barh(y_pos, df["Avg Salary"], height=height, color="#3b82f6", alpha=0.85, label="Average Salary")

    # Add error bar range from Min to Max
    err_min = df["Avg Salary"] - df["Min Salary"]
    err_max = df["Max Salary"] - df["Avg Salary"]
    ax.errorbar(
        df["Avg Salary"],
        y_pos,
        xerr=[err_min, err_max],
        fmt="none",
        ecolor="#0f172a",
        elinewidth=1.6,
        capsize=4,
        capthick=1.4,
        label="Salary Range (Min - Max)"
    )

    # Annotate average salary value
    for idx, (bar, avg_val) in enumerate(zip(bars, df["Avg Salary"])):
        ax.text(
            avg_val + 2000,
            bar.get_y() + bar.get_height() / 2,
            f"${avg_val:,.0f}",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b"
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["Skill"], fontsize=9.5, fontweight="semibold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x*1e-3:,.0f}k"))
    
    ax.set_title("Salary Benchmarks by Extracted Technology (USD / Yr)", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
    ax.set_xlabel("Compensation ($ USD)", fontsize=10, fontweight="semibold", color="#475569")
    ax.legend(loc="lower right", frameon=True)
    
    sns.despine(ax=ax, top=True, right=True)
    fig.tight_layout()
    return fig


def plot_distributions(stats: AggregatedStats) -> Tuple[Optional[plt.Figure], Optional[plt.Figure]]:
    """
    Generate Workplace and Experience level distribution charts.
    """
    fig_wp, fig_exp = None, None

    # 1. Workplace Distribution
    if stats.workplace_distribution:
        fig_wp, ax_wp = plt.subplots(figsize=(5.5, 4), dpi=150)
        wp_labels = [k.capitalize() for k in stats.workplace_distribution.keys()]
        wp_values = list(stats.workplace_distribution.values())
        colors = sns.color_palette("pastel", len(wp_labels))
        
        ax_wp.pie(
            wp_values,
            labels=wp_labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops={"edgecolor": "white", "linewidth": 2, "antialiased": True}
        )
        ax_wp.set_title("Workplace Mode Distribution", fontsize=11, fontweight="bold", color="#0f172a")
        fig_wp.tight_layout()

    # 2. Experience Distribution
    if stats.experience_distribution:
        fig_exp, ax_exp = plt.subplots(figsize=(5.5, 4), dpi=150)
        exp_labels = [k.capitalize() for k in stats.experience_distribution.keys()]
        exp_values = list(stats.experience_distribution.values())
        palette = sns.color_palette("Blues_d", len(exp_labels))
        
        bars = ax_exp.bar(exp_labels, exp_values, color=palette, edgecolor="none", width=0.6)
        for bar in bars:
            height = bar.get_height()
            ax_exp.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.3,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )
            
        ax_exp.set_title("Experience Level Breakdown", fontsize=11, fontweight="bold", color="#0f172a")
        ax_exp.set_ylabel("Job Postings Count", fontsize=9, color="#475569")
        plt.setp(ax_exp.get_xticklabels(), rotation=20, ha="right", fontsize=8.5)
        sns.despine(ax=ax_exp, top=True, right=True)
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
    palette = sns.color_palette("crest", len(df))
    
    bars = ax.barh(df["Category"], df["Total Mentions"], color=palette, height=0.6)
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)}",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#1e293b"
        )

    ax.set_title("Aggregate Skill Mentions by Domain Category", fontsize=12, fontweight="bold", pad=12, color="#0f172a")
    ax.set_xlabel("Total Frequency across Postings", fontsize=9.5, fontweight="semibold", color="#475569")
    sns.despine(ax=ax, top=True, right=True)
    fig.tight_layout()
    return fig
