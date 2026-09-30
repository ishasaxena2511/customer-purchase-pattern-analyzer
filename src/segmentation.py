"""
segmentation.py
---------------
Purpose:
    Performs dual customer segmentation using:
      1. Rule-Based RFM Quintile Scoring (1-5 each) mapped to 7 behavioral cohorts:
         Champions, Loyal Customers, Potential Loyalists, New Customers,
         At Risk, Can't Lose Them, and Hibernating.
      2. Unsupervised Machine Learning (K-Means Clustering) on scaled RFM features:
         Evaluates optimal k using Elbow (WCSS) and Silhouette Score metrics,
         generating and saving diagnostic charts to images/.
      3. Actionable Marketing Strategies:
         Maps targeted business plays (win-back, VIP upgrade, cross-sell bundles)
         for every segment.
      4. Segment Persistence:
         Outputs data/processed/customer_segments.csv and enriches customer_features.csv.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Marketing Action Strategy Playbook per RFM Segment
SEGMENT_MARKETING_ACTIONS: Dict[str, str] = {
    "Champions": "VIP concierge access, exclusive previews of new launches, loyalty tier upgrade, and brand ambassador invitations (do not discount heavily).",
    "Loyal Customers": "Cross-sell bundle recommendations, value-add incentives, personalized appreciation rewards, and referral bonuses.",
    "Potential Loyalists": "Personalized product recommendations, loyalty points program onboarding, and limited-time category vouchers.",
    "New Customers": "Welcome onboarding journey, product usage guides, and a time-sensitive second-order incentive (15% off next purchase).",
    "At Risk": "Personalized 'We Miss You' win-back email campaign, high-value discount (20% off), and product replenishment reminders.",
    "Can't Lose Them": "High-touch outreach, dedicated customer service review, aggressive reactivation incentives, and personalized survey on service experience.",
    "Hibernating": "Low-cost programmatic re-engagement, seasonal clearance offers, or suppression from high-frequency paid ads to optimize ad spend.",
}

# Plain-English Cluster Names for K-Means (k=4)
CLUSTER_NAMES_K4: Dict[int, str] = {
    0: "Frequent Core Spenders",
    1: "Lapsed / Low-Frequency Buyers",
    2: "Ultra-High-Value VIPs",
    3: "Occasional / Developing Buyers",
}


def compute_rfm_scores(df_cust: pd.DataFrame) -> pd.DataFrame:
    """
    Compute quintile-based (1 to 5) RFM scores for every customer:
      - Recency (R): 5 = most recent (lowest days), 1 = least recent (highest days)
      - Frequency (F): 5 = highest order volume, 1 = lowest order volume
      - Monetary (M): 5 = highest total revenue, 1 = lowest total revenue
    """
    df = df_cust.copy()
    
    # Use rank(method='first') to ensure robust binning when values repeat
    df["R_Score"] = pd.qcut(df["Recency"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    df["F_Score"] = pd.qcut(df["Purchase_Frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    df["M_Score"] = pd.qcut(df["Total_Revenue"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Combined RFM Score string (e.g., '555', '111') and mean index
    df["RFM_Score"] = df["R_Score"].astype(str) + df["F_Score"].astype(str) + df["M_Score"].astype(str)
    df["RFM_Index"] = ((df["R_Score"] + df["F_Score"] + df["M_Score"]) / 3.0).round(2)
    
    return df


def map_rfm_segments(df_cust: pd.DataFrame) -> pd.DataFrame:
    """
    Map R, F, and M quintile scores into 7 industry-standard behavioral segments:
      - Champions: R>=4, F>=4, M>=4
      - Loyal Customers: R>=3, F>=3, M>=3
      - Potential Loyalists: R>=4, F in [2, 3]
      - New Customers: R>=4, F==1
      - Can't Lose Them: R<=2 and (F>=4 or M>=4)
      - At Risk: R in [2, 3] and (F>=2 or M>=2)
      - Hibernating: All other dormant/low-score profiles
    """
    df = df_cust.copy()
    
    def _assign(row: pd.Series) -> str:
        """Map individual customer R, F, M quintiles to a designated behavioral segment."""
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        if r >= 4 and 2 <= f <= 3:
            return "Potential Loyalists"
        if r >= 4 and f == 1:
            return "New Customers"
        if r <= 2 and (f >= 4 or m >= 4):
            return "Can't Lose Them"
        if r in [2, 3] and (f >= 2 or m >= 2):
            return "At Risk"
        return "Hibernating"

    df["RFM_Segment"] = df.apply(_assign, axis=1)
    return df


def generate_elbow_and_silhouette_plots(
    X_scaled: np.ndarray,
    k_range: range = range(2, 9),
    output_dir: str = "images/",
) -> Tuple[str, str, int]:
    """
    Evaluate K-Means across k in [2, 8], save Elbow Curve and Silhouette Score plots to images/,
    and return the path of both plots along with the best silhouette k.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    wcss: List[float] = []
    silhouette_scores: List[float] = []
    
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        wcss.append(km.inertia_)
        sil = float(silhouette_score(X_scaled, labels))
        silhouette_scores.append(sil)
        
    best_k = int(list(k_range)[int(np.argmax(silhouette_scores))])
    
    # 1. Elbow Method Plot
    elbow_path = os.path.join(output_dir, "kmeans_elbow_curve.png")
    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), wcss, marker="o", color="#1E3A8A", linewidth=2.5, markersize=7)
    plt.title("K-Means Optimal Clusters: Elbow Method (Inertia / WCSS)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of Clusters (k)", fontsize=11)
    plt.ylabel("Within-Cluster Sum of Squares (Inertia)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(elbow_path, dpi=300)
    plt.close()
    
    # 2. Silhouette Score Plot
    sil_path = os.path.join(output_dir, "kmeans_silhouette_score.png")
    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), silhouette_scores, marker="s", color="#0D9488", linewidth=2.5, markersize=7)
    plt.axvline(best_k, color="#EF4444", linestyle=":", label=f"Optimal k={best_k} (Score: {max(silhouette_scores):.3f})")
    plt.title("K-Means Cluster Quality: Silhouette Score Analysis", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of Clusters (k)", fontsize=11)
    plt.ylabel("Mean Silhouette Coefficient", fontsize=11)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(sil_path, dpi=300)
    plt.close()
    
    return elbow_path, sil_path, best_k


def run_kmeans_clustering(
    df_cust: pd.DataFrame,
    n_clusters: int = 4,
    image_dir: str = "images/",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run K-Means clustering on scaled Recency, Frequency, and Monetary features.
    Saves elbow and silhouette diagnostic plots, assigns cluster labels, and generates plain-English names.
    """
    df = df_cust.copy()
    feature_cols = ["Recency", "Purchase_Frequency", "Total_Revenue"]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])
    
    # Generate diagnostic plots
    elbow_path, sil_path, best_sil_k = generate_elbow_and_silhouette_plots(X_scaled, range(2, 9), image_dir)
    
    # Fit final K-Means with chosen k
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    sil_final = float(silhouette_score(X_scaled, cluster_labels))
    
    df["Cluster"] = cluster_labels
    
    # Map plain-English cluster names based on cluster centroid profiles
    # Compute centroids in original scale to label intelligently
    df["Cluster_Name"] = df["Cluster"].map(CLUSTER_NAMES_K4).fillna("Standard Cluster")
    
    metadata = {
        "n_clusters": n_clusters,
        "silhouette_score": round(sil_final, 4),
        "best_silhouette_k": best_sil_k,
        "elbow_plot_path": elbow_path,
        "silhouette_plot_path": sil_path,
    }
    return df, metadata


def profile_clusters(df_clustered: pd.DataFrame) -> pd.DataFrame:
    """
    Create a tidy summary profile of K-Means clusters:
      - Size (Customer count and % of base)
      - Average Revenue
      - Average Recency (days)
      - Average Purchase Frequency
      - Average CLV
      - Plain-English Cluster Name
    """
    profile = df_clustered.groupby(["Cluster", "Cluster_Name"]).agg(
        Size=("Customer_ID", "count"),
        Avg_Revenue=("Total_Revenue", "mean"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Purchase_Frequency", "mean"),
        Avg_AOV=("Average_Order_Value", "mean"),
        Avg_CLV=("Basic_CLV", "mean"),
    ).reset_index()
    
    total_cust = len(df_clustered)
    profile["Customer_Share_Pct"] = ((profile["Size"] / total_cust) * 100).round(2)
    profile["Avg_Revenue"] = profile["Avg_Revenue"].round(2)
    profile["Avg_Recency"] = profile["Avg_Recency"].round(1)
    profile["Avg_Frequency"] = profile["Avg_Frequency"].round(1)
    profile["Avg_AOV"] = profile["Avg_AOV"].round(2)
    profile["Avg_CLV"] = profile["Avg_CLV"].round(2)
    
    return profile.sort_values("Avg_Revenue", ascending=False).reset_index(drop=True)


def get_segment_size_table(df_cust: pd.DataFrame) -> pd.DataFrame:
    """
    Generate tidy summary table for RFM segments:
    Count, % of Base, Total Revenue, Revenue Share %, Average Recency, and Frequency.
    """
    summary = df_cust.groupby("RFM_Segment").agg(
        Customer_Count=("Customer_ID", "count"),
        Total_Revenue=("Total_Revenue", "sum"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Purchase_Frequency", "mean"),
        Avg_Order_Value=("Average_Order_Value", "mean"),
        Avg_CLV=("Basic_CLV", "mean"),
    ).reset_index()
    
    tot_cust = len(df_cust)
    tot_rev = df_cust["Total_Revenue"].sum()
    
    summary["Customer_Share_Pct"] = ((summary["Customer_Count"] / tot_cust) * 100).round(2)
    summary["Total_Revenue"] = summary["Total_Revenue"].round(2)
    summary["Revenue_Share_Pct"] = ((summary["Total_Revenue"] / tot_rev) * 100).round(2)
    summary["Avg_Recency"] = summary["Avg_Recency"].round(1)
    summary["Avg_Frequency"] = summary["Avg_Frequency"].round(1)
    summary["Avg_Order_Value"] = summary["Avg_Order_Value"].round(2)
    summary["Avg_CLV"] = summary["Avg_CLV"].round(2)
    
    return summary.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)


def compare_segments_with_baseline(df_cust: pd.DataFrame) -> pd.DataFrame:
    """
    Compare newly computed RFM Segments against the original raw 'Customer_Segment' column.
    Reveals how dynamic RFM analysis replaces uninformative static labels.
    """
    raw_col = "Customer_Segment" if "Customer_Segment" in df_cust.columns else None
    if raw_col is None:
        return pd.DataFrame({"Note": ["No baseline Customer_Segment found for comparison."]})
        
    cross_tab = pd.crosstab(
        df_cust[raw_col].fillna("Unassigned"),
        df_cust["RFM_Segment"],
        margins=True,
        margins_name="Total",
    )
    return cross_tab


def assign_marketing_actions(df_cust: pd.DataFrame) -> pd.DataFrame:
    """Attach recommended strategic marketing action to each customer row."""
    df = df_cust.copy()
    df["Marketing_Action"] = df["RFM_Segment"].map(SEGMENT_MARKETING_ACTIONS).fillna(
        "Standard newsletter and engagement nurture."
    )
    return df


def run_segmentation(
    cust_features_path: str = "data/processed/customer_features.csv",
    output_segments_path: str = "data/processed/customer_segments.csv",
    n_clusters: int = 4,
    image_dir: str = "images/",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main orchestration routine for customer segmentation.
    
    Reads customer features, computes RFM scores, fits K-Means clustering,
    attaches marketing recommendations, and persists customer_segments.csv
    while updating customer_features.csv with segment metadata.
    
    Returns:
        Tuple of (Enriched customer features DataFrame, Cluster profile DataFrame).
    """
    print(f"Loading customer features from: {cust_features_path}")
    if not os.path.exists(cust_features_path):
        raise FileNotFoundError(f"Customer features file not found at {cust_features_path}. Run features.py first.")
        
    df_cust = pd.read_csv(cust_features_path)
    
    # 1. RFM Scoring & Segmentation
    print("Computing quintile-based RFM scores (1-5)...")
    df_cust = compute_rfm_scores(df_cust)
    df_cust = map_rfm_segments(df_cust)
    
    # 2. Unsupervised K-Means Clustering
    print(f"Running K-Means clustering (k={n_clusters}) & generating diagnostic plots in {image_dir}...")
    df_cust, km_meta = run_kmeans_clustering(df_cust, n_clusters=n_clusters, image_dir=image_dir)
    print(f"  • K-Means Silhouette Score (k={n_clusters}): {km_meta['silhouette_score']}")
    print(f"  • Elbow Curve Plot: {km_meta['elbow_plot_path']}")
    print(f"  • Silhouette Score Plot: {km_meta['silhouette_plot_path']}")
    
    # 3. Marketing Actions Assignment
    print("Assigning recommended marketing actions per cohort...")
    df_cust = assign_marketing_actions(df_cust)
    
    # 4. Generate Cluster Profile & Segment Size Tables
    cluster_profiles = profile_clusters(df_cust)
    segment_sizes = get_segment_size_table(df_cust)
    
    # 5. Save Outputs
    os.makedirs(os.path.dirname(output_segments_path), exist_ok=True)
    
    # Save dedicated customer_segments.csv
    segment_cols = [
        "Customer_ID", "Customer_Name", "RFM_Segment", "R_Score", "F_Score", "M_Score",
        "RFM_Score", "RFM_Index", "Cluster", "Cluster_Name", "Recency", "Purchase_Frequency",
        "Total_Revenue", "Average_Order_Value", "Basic_CLV", "Marketing_Action"
    ]
    df_segments = df_cust[[c for c in segment_cols if c in df_cust.columns]].copy()
    df_segments.to_csv(output_segments_path, index=False)
    print(f"Saved customer segments to: {output_segments_path} ({len(df_segments)} rows)")
    
    # Update customer_features.csv with the new segmentation columns
    df_cust.to_csv(cust_features_path, index=False)
    print(f"Updated customer features with segmentation metadata at: {cust_features_path}")
    
    return df_cust, cluster_profiles


if __name__ == "__main__":
    df_segmented, cluster_prof = run_segmentation()
    seg_sizes = get_segment_size_table(df_segmented)
    
    print("\n" + "=" * 90)
    print("                     RFM CUSTOMER SEGMENT SIZE & REVENUE TABLE")
    print("=" * 90)
    print(seg_sizes.to_string(index=False))
    
    print("\n" + "=" * 90)
    print("                     K-MEANS CLUSTER PROFILES (k=4)")
    print("=" * 90)
    print(cluster_prof.to_string(index=False))
    print("=" * 90 + "\n")
