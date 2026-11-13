"""
Explainable Personalized Recommendation Engine
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Combines:
1. Collaborative Filtering (User-Item Implicit Interaction Matrix & Cosine Similarity)
2. Association Rule Mining (Co-occurrence, Support, Confidence, Lift)
3. Cluster-level Behavioral Affinity
4. Transparent Explainability Layer (Reasoning text & contributing factors for every recommendation)
"""

import os
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from itertools import combinations
from sklearn.metrics.pairwise import cosine_similarity


def load_data():
    """Loads cleaned transactions, web activity, and customer segment assignments."""
    tx_path = "data/processed/cleaned_transactions.csv"
    web_path = "data/processed/cleaned_web_activity.csv"
    seg_path = "data/processed/customer_segment_assignments.csv"

    if not (os.path.exists(tx_path) and os.path.exists(web_path) and os.path.exists(seg_path)):
        raise FileNotFoundError("Processed datasets missing. Run Stage 3 and K-Means training first.")

    df_tx = pd.read_csv(tx_path)
    df_web = pd.read_csv(web_path)
    df_seg = pd.read_csv(seg_path)

    return df_tx, df_web, df_seg


def build_product_catalog(df_tx: pd.DataFrame) -> dict:
    """Extracts unique products catalog with category and unit price."""
    cat_df = df_tx[["product_id", "product_name", "product_category", "unit_price"]].drop_duplicates("product_id")
    catalog = {}
    for _, row in cat_df.iterrows():
        catalog[row["product_id"]] = {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "category": row["product_category"],
            "unit_price": float(row["unit_price"])
        }
    return catalog


def build_interaction_matrix(df_tx: pd.DataFrame, df_web: pd.DataFrame, customers: list, products: list):
    """
    Builds an implicit interaction matrix:
    - Completed Purchase: 5.0 * quantity
    - Add to Cart: 2.5
    - Product Detail View: 1.0
    """
    matrix = pd.DataFrame(0.0, index=customers, columns=products)

    # 1. Purchase weights
    completed_tx = df_tx[df_tx["order_status"] == "Completed"]
    for _, row in completed_tx.iterrows():
        cid = row["customer_id"]
        pid = row["product_id"]
        if cid in matrix.index and pid in matrix.columns:
            matrix.loc[cid, pid] += 5.0 * float(row["quantity"])

    # 2. Web interactions
    web_prod = df_web[df_web["product_id"].notna() & (df_web["product_id"] != "")]
    for _, row in web_prod.iterrows():
        cid = row["customer_id"]
        pid = row["product_id"]
        action = row["action_type"]
        if cid in matrix.index and pid in matrix.columns:
            if action == "add_to_cart":
                matrix.loc[cid, pid] += 2.5
            elif action == "product_view":
                matrix.loc[cid, pid] += 1.0
            elif action == "wishlist":
                matrix.loc[cid, pid] += 1.5

    return matrix


def mine_association_rules(df_tx: pd.DataFrame, min_support: int = 15, min_confidence: float = 0.20):
    """
    Mines 2-item association rules from customer purchase baskets:
    Rule: A -> B with Support, Confidence, Lift
    """
    completed_tx = df_tx[df_tx["order_status"] == "Completed"]
    baskets = completed_tx.groupby("customer_id")["product_id"].unique().to_dict()
    total_baskets = len(baskets)

    item_counts = defaultdict(int)
    pair_counts = defaultdict(int)

    for cid, items in baskets.items():
        unique_items = sorted(list(set(items)))
        for item in unique_items:
            item_counts[item] += 1
        for a, b in combinations(unique_items, 2):
            pair_counts[(a, b)] += 1
            pair_counts[(b, a)] += 1

    rules = []
    for (a, b), pair_cnt in pair_counts.items():
        if pair_cnt >= min_support:
            support_ab = pair_cnt / total_baskets
            support_a = item_counts[a] / total_baskets
            support_b = item_counts[b] / total_baskets
            confidence = pair_cnt / item_counts[a]
            lift = confidence / support_b if support_b > 0 else 1.0

            if confidence >= min_confidence:
                rules.append({
                    "antecedent": a,
                    "consequent": b,
                    "support": round(support_ab, 4),
                    "confidence": round(confidence, 4),
                    "lift": round(lift, 2)
                })

    # Sort by lift descending
    rules.sort(key=lambda x: x["lift"], reverse=True)
    return rules


def generate_recommendations():
    print("=" * 70)
    print("STAGE 4: EXPLAINABLE PERSONALIZED RECOMMENDATION ENGINE")
    print("=" * 70)

    # 1. Load data
    df_tx, df_web, df_seg = load_data()
    catalog = build_product_catalog(df_tx)
    all_products = sorted(list(catalog.keys()))
    all_customers = sorted(df_seg["customer_id"].unique().tolist())

    print(f"Loaded {len(all_customers)} customers and {len(all_products)} catalog products.")

    # 2. Association Rules Mining
    print("Mining association rules from purchase histories...")
    association_rules = mine_association_rules(df_tx)
    print(f"Mined {len(association_rules)} high-confidence association rules.")

    # Index rules by antecedent for quick lookup
    rules_by_item = defaultdict(list)
    for rule in association_rules:
        rules_by_item[rule["antecedent"]].append(rule)

    # 3. Collaborative Filtering Matrix
    print("Building implicit user-item interaction matrix...")
    interaction_matrix = build_interaction_matrix(df_tx, df_web, all_customers, all_products)

    # Compute Cosine Similarity between customer profiles
    print("Computing customer similarity matrix...")
    customer_sim = cosine_similarity(interaction_matrix.values)
    sim_df = pd.DataFrame(customer_sim, index=all_customers, columns=all_customers)

    # Cluster profiles and popularity
    seg_map = df_seg.set_index("customer_id")["cluster_name"].to_dict()
    cluster_top_items = defaultdict(list)
    for cname, group in df_seg.groupby("cluster_name"):
        c_ids = group["customer_id"].tolist()
        cluster_item_sums = interaction_matrix.loc[c_ids].sum(axis=0).sort_values(ascending=False)
        cluster_top_items[cname] = cluster_item_sums.head(8).index.tolist()

    # 4. Generate Top Recommendations per Customer
    print("Generating personalized recommendations with explicit reasoning...")
    recommendations_by_customer = {}

    for idx, cid in enumerate(all_customers):
        c_segment = seg_map.get(cid, "General Customer")
        user_vector = interaction_matrix.loc[cid]
        already_purchased = set(user_vector[user_vector > 5.0].index.tolist())
        already_viewed = set(user_vector[user_vector > 0.0].index.tolist())

        # Top 15 similar peers (excluding self)
        similar_peers = sim_df.loc[cid].drop(cid).sort_values(ascending=False).head(15)
        top_peer_ids = similar_peers.index.tolist()
        peer_weights = similar_peers.values

        # Collaborative scores
        peer_matrix = interaction_matrix.loc[top_peer_ids]
        collab_scores = np.dot(peer_weights, peer_matrix.values) / (np.sum(np.abs(peer_weights)) + 1e-6)
        collab_series = pd.Series(collab_scores, index=all_products)

        # Candidate item ranking
        candidate_scores = {}
        for pid in all_products:
            if pid in already_purchased:
                continue  # Don't recommend recently purchased items

            base_collab = float(collab_series.get(pid, 0.0))
            assoc_boost = 0.0
            assoc_rule_match = None

            # Check association with items the customer already bought
            for bought_pid in already_purchased:
                for rule in rules_by_item.get(bought_pid, []):
                    if rule["consequent"] == pid:
                        if rule["lift"] > assoc_boost:
                            assoc_boost = rule["lift"]
                            assoc_rule_match = (bought_pid, rule)

            # Segment affinity boost
            cluster_boost = 1.5 if pid in cluster_top_items.get(c_segment, []) else 0.0

            # Browsing intent boost (viewed or added to cart but not purchased)
            browsing_boost = 2.0 if pid in already_viewed else 0.0

            # Composite recommendation score (normalized to 0-100)
            final_raw = (base_collab * 2.5) + (assoc_boost * 3.0) + (cluster_boost * 2.0) + (browsing_boost * 2.5)
            norm_score = min(99.0, max(45.0, round(final_raw * 2.5 + 40.0, 1)))

            # Formulate explainable reason
            if assoc_rule_match:
                bought_name = catalog[assoc_rule_match[0]]["product_name"]
                lift_val = assoc_rule_match[1]["lift"]
                conf_pct = int(assoc_rule_match[1]["confidence"] * 100)
                reason_type = "association_rule"
                explanation = f"Frequently bought together with '{bought_name}' (Association confidence: {conf_pct}%, Lift: {lift_val}x)."
            elif pid in already_viewed:
                reason_type = "browsing_intent"
                explanation = f"Picked based on your recent browsing interactions and active interest in {catalog[pid]['category']}."
            elif base_collab > 1.2:
                reason_type = "collaborative_peer"
                explanation = f"Highly rated by peer customers with similar purchase patterns in your '{c_segment}' profile."
            else:
                reason_type = "cluster_affinity"
                explanation = f"Top-performing popular choice among fellow shoppers in the '{c_segment}' segment."

            candidate_scores[pid] = {
                "product_id": pid,
                "product_name": catalog[pid]["product_name"],
                "category": catalog[pid]["category"],
                "unit_price": catalog[pid]["unit_price"],
                "score": norm_score,
                "reason_type": reason_type,
                "explanation": explanation
            }

        # Select top 5 recommendations
        sorted_candidates = sorted(candidate_scores.values(), key=lambda x: x["score"], reverse=True)[:5]
        recommendations_by_customer[cid] = sorted_candidates

    # 5. Save Artifacts
    models_dir = "ml/models"
    os.makedirs(models_dir, exist_ok=True)

    with open(os.path.join(models_dir, "product_association_rules.json"), "w", encoding="utf-8") as f:
        json.dump(association_rules, f, indent=2)

    with open(os.path.join(models_dir, "customer_recommendations.json"), "w", encoding="utf-8") as f:
        json.dump(recommendations_by_customer, f, indent=2)

    # Also export top recommendations to flat CSV for easy inspection & tabular querying
    flat_rows = []
    for cid, recs in recommendations_by_customer.items():
        for rank, r in enumerate(recs, start=1):
            flat_rows.append({
                "customer_id": cid,
                "rank": rank,
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "category": r["category"],
                "unit_price": r["unit_price"],
                "score": r["score"],
                "reason_type": r["reason_type"],
                "explanation": r["explanation"]
            })

    df_flat_recs = pd.DataFrame(flat_rows)
    df_flat_recs.to_csv("data/processed/customer_recommendations.csv", index=False)
    print(f"Saved recommendations to data/processed/customer_recommendations.csv and {os.path.join(models_dir, 'customer_recommendations.json')}")

    # Sample preview for first customer
    sample_cid = all_customers[0]
    print(f"\nSample Recommendations for {sample_cid} ({seg_map.get(sample_cid)}):")
    for r in recommendations_by_customer[sample_cid]:
        print(f"  * [{r['score']}%] {r['product_name']} ({r['category']}, ${r['unit_price']})")
        print(f"    Reason ({r['reason_type']}): {r['explanation']}")

    print("=" * 70)
    print("RECOMMENDATION ENGINE EXECUTION COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    generate_recommendations()
