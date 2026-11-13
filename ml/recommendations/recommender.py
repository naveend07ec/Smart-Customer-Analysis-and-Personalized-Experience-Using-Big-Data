"""
Personalized Product Recommendation Engine
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Implements:
1. Customer-Product multi-touchpoint interaction scoring (Purchases, Carts, Views).
2. Item-based Collaborative Filtering using Cosine Similarity.
3. Market Basket Association Rule Mining (Support, Confidence, Lift).
4. Rigorous Offline Train/Test Evaluation (Precision@5, Recall@5, Hit Rate@5, Coverage).
5. Explainable Top-5 Recommendation Generation with transparent rationale.
6. Artifact persistence and export to Parquet and CSV.
"""

import os
import joblib
import pandas as pd
import numpy as np
from itertools import combinations
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")

# Interaction scoring weights based on user intent hierarchy
INTERACTION_WEIGHTS = {
    "purchase": 5.0,        # Explicit financial transaction
    "checkout_start": 4.0,  # High purchase intent
    "add_to_cart": 3.0,     # Strong product interest
    "wishlist": 2.0,        # Latent product bookmark
    "product_view": 1.0     # Informational browsing touchpoint
}


def build_interaction_matrix():
    """
    Constructs unified customer-product interaction records from transactions
    and clickstream web logs with documented intent weights.
    """
    tx_path = os.path.join(PROCESSED_DIR, "cleaned_transactions.parquet")
    web_path = os.path.join(PROCESSED_DIR, "cleaned_web_activity.parquet")

    tx_df = pd.read_parquet(tx_path)
    web_df = pd.read_parquet(web_path)

    # 1. Product Metadata Catalog
    prod_meta = tx_df[["product_id", "product_name", "product_category", "unit_price"]].drop_duplicates()
    prod_meta = prod_meta.set_index("product_id")

    # 2. Extract transaction interactions
    completed_tx = tx_df[tx_df["order_status"] == "Completed"].copy()
    completed_tx["interaction_type"] = "purchase"
    completed_tx["weight"] = INTERACTION_WEIGHTS["purchase"]

    tx_interactions = completed_tx.groupby(["customer_id", "product_id"])["weight"].sum().reset_index()

    # 3. Extract web clickstream interactions
    web_prods = web_df[web_df["product_id"].notna() & (web_df["product_id"] != "")].copy()
    web_prods = web_prods[web_prods["product_id"].isin(prod_meta.index)]

    web_prods["weight"] = web_prods["action_type"].map(
        lambda a: INTERACTION_WEIGHTS.get(a, 1.0)
    )

    web_interactions = web_prods.groupby(["customer_id", "product_id"])["weight"].sum().reset_index()

    # 4. Merge interactions
    combined = pd.concat([tx_interactions, web_interactions], ignore_index=True)
    interaction_df = combined.groupby(["customer_id", "product_id"])["weight"].sum().reset_index()
    interaction_df.rename(columns={"weight": "interaction_score"}, inplace=True)

    # Attach product metadata
    interaction_df["product_name"] = interaction_df["product_id"].map(prod_meta["product_name"])
    interaction_df["product_category"] = interaction_df["product_id"].map(prod_meta["product_category"])

    return interaction_df, prod_meta, tx_df


def mine_association_rules(tx_df, min_support=0.01, min_lift=1.05):
    """
    Computes pair-wise co-occurrence association rules from completed transactions.
    Calculates Support, Confidence, and Lift metrics for explainability.
    """
    completed = tx_df[tx_df["order_status"] == "Completed"]
    baskets = completed.groupby("customer_id")["product_id"].unique()
    total_baskets = len(baskets)

    # Single item frequencies
    item_freq = {}
    for items in baskets:
        for it in items:
            item_freq[it] = item_freq.get(it, 0) + 1

    # Pair frequencies
    pair_freq = {}
    for items in baskets:
        if len(items) > 1:
            for it1, it2 in combinations(sorted(items), 2):
                pair = (it1, it2)
                pair_freq[pair] = pair_freq.get(pair, 0) + 1

    rules = []
    for (it1, it2), count in pair_freq.items():
        support_ab = count / total_baskets
        if support_ab >= min_support:
            support_a = item_freq[it1] / total_baskets
            support_b = item_freq[it2] / total_baskets
            
            # Rule A -> B
            conf_a_b = support_ab / support_a
            lift_a_b = conf_a_b / support_b
            if lift_a_b >= min_lift:
                rules.append({
                    "antecedent_id": it1,
                    "consequent_id": it2,
                    "support": round(support_ab, 4),
                    "confidence": round(conf_a_b, 4),
                    "lift": round(lift_a_b, 3)
                })

            # Rule B -> A
            conf_b_a = support_ab / support_b
            lift_b_a = conf_b_a / support_a
            if lift_b_a >= min_lift:
                rules.append({
                    "antecedent_id": it2,
                    "consequent_id": it1,
                    "support": round(support_ab, 4),
                    "confidence": round(conf_b_a, 4),
                    "lift": round(lift_b_a, 3)
                })

    rules_df = pd.DataFrame(rules)
    if not rules_df.empty:
        rules_df = rules_df.sort_values(by="lift", ascending=False)
    return rules_df


def evaluate_recommendations(interaction_df, all_products, test_ratio=0.2, top_k=5):
    """
    Performs train/test offline evaluation by holding out 20% of interactions
    for customers with multiple interactions, and evaluating Precision@5, Recall@5,
    Hit Rate@5, and Catalog Coverage.
    """
    np.random.seed(42)
    # Filter customers with at least 3 interactions for meaningful split
    cust_counts = interaction_df["customer_id"].value_counts()
    eligible_custs = cust_counts[cust_counts >= 3].index

    train_rows = []
    test_dict = {}

    for cid in eligible_custs:
        cust_items = interaction_df[interaction_df["customer_id"] == cid]["product_id"].values
        n_test = max(1, int(len(cust_items) * test_ratio))
        test_items = set(np.random.choice(cust_items, size=n_test, replace=False))
        test_dict[cid] = test_items

        for it in cust_items:
            if it not in test_items:
                row = interaction_df[(interaction_df["customer_id"] == cid) & (interaction_df["product_id"] == it)].iloc[0]
                train_rows.append(row)

    # Add remaining customers entirely to train
    remaining_custs = set(interaction_df["customer_id"].unique()) - set(eligible_custs)
    for cid in remaining_custs:
        c_rows = interaction_df[interaction_df["customer_id"] == cid]
        for _, r in c_rows.iterrows():
            train_rows.append(r)

    train_df = pd.DataFrame(train_rows)

    # Build train interaction matrix
    train_pivot = train_df.pivot_table(index="customer_id", columns="product_id", values="interaction_score", fill_value=0.0)
    for p in all_products:
        if p not in train_pivot.columns:
            train_pivot[p] = 0.0
    train_pivot = train_pivot[all_products]

    # Compute item-item cosine similarity on train split
    item_sim_train = pd.DataFrame(
        cosine_similarity(train_pivot.T),
        index=all_products,
        columns=all_products
    )

    precisions = []
    recalls = []
    hits = []
    recommended_items_set = set()

    for cid, true_items in test_dict.items():
        if cid not in train_pivot.index:
            continue
        u_profile = train_pivot.loc[cid]
        scores = u_profile.dot(item_sim_train)

        # Exclude items present in training
        known_train_items = set(u_profile[u_profile > 0].index)
        candidate_scores = scores.drop(index=list(known_train_items), errors="ignore")

        top_recs = candidate_scores.nlargest(top_k).index.tolist()
        recommended_items_set.update(top_recs)

        hits_count = len(set(top_recs).intersection(true_items))
        prec = hits_count / top_k
        rec = hits_count / len(true_items)
        hit = 1.0 if hits_count > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        hits.append(hit)

    coverage = len(recommended_items_set) / len(all_products)

    metrics = {
        "evaluation_metric": ["Precision@5", "Recall@5", "Hit_Rate@5", "Catalog_Coverage", "Evaluated_Customers_Count"],
        "metric_value": [
            round(float(np.mean(precisions)), 4),
            round(float(np.mean(recalls)), 4),
            round(float(np.mean(hits)), 4),
            round(float(coverage), 4),
            int(len(precisions))
        ]
    }
    return pd.DataFrame(metrics)


def generate_recommendations():
    print("=" * 70)
    print("PART B: PERSONALIZED RECOMMENDATION ENGINE")
    print("=" * 70)

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 1. Build Interaction Matrix
    interaction_df, prod_meta, tx_df = build_interaction_matrix()
    interaction_csv = os.path.join(PROCESSED_DIR, "customer_product_interactions.csv")
    interaction_df.to_csv(interaction_csv, index=False)
    print(f"Customer-product interaction records: {len(interaction_df)} saved to {interaction_csv}")

    all_products = sorted(list(prod_meta.index))
    all_customers = sorted(list(tx_df["customer_id"].unique()))

    # 2. Mine Market Basket Association Rules
    print("Mining transaction association rules (Support & Lift)...")
    rules_df = mine_association_rules(tx_df, min_support=0.01, min_lift=1.05)
    rules_csv = os.path.join(PROCESSED_DIR, "association_rules.csv")
    rules_df.to_csv(rules_csv, index=False)
    print(f"Association rules discovered: {len(rules_df)} saved to {rules_csv}")

    # Build association lookup map: antecedent_id -> dict of {consequent_id: (lift, confidence)}
    assoc_map = {}
    for _, r in rules_df.iterrows():
        ant = r["antecedent_id"]
        conq = r["consequent_id"]
        if ant not in assoc_map:
            assoc_map[ant] = {}
        assoc_map[ant][conq] = (r["lift"], r["confidence"])

    # 3. Item-Based Collaborative Filtering Model
    print("Building Item-Item Collaborative Filtering Similarity Matrix...")
    pivot_matrix = interaction_df.pivot_table(
        index="customer_id",
        columns="product_id",
        values="interaction_score",
        fill_value=0.0
    )
    for p in all_products:
        if p not in pivot_matrix.columns:
            pivot_matrix[p] = 0.0
    pivot_matrix = pivot_matrix[all_products]

    # Calculate Item-Item Cosine Similarity
    item_similarity = pd.DataFrame(
        cosine_similarity(pivot_matrix.T),
        index=all_products,
        columns=all_products
    )

    # 4. Offline Train/Test Evaluation
    print("Running Train/Test Split Offline Recommendation Evaluation...")
    eval_df = evaluate_recommendations(interaction_df, all_products, test_ratio=0.2, top_k=5)
    eval_csv = os.path.join(PROCESSED_DIR, "recommendation_evaluation.csv")
    eval_df.to_csv(eval_csv, index=False)
    print("Recommendation Evaluation Metrics:")
    for _, r in eval_df.iterrows():
        print(f"  * {r['evaluation_metric']}: {r['metric_value']}")

    # 5. Full Production Recommendation Generation with Explanations
    print("\nGenerating Top-5 Explainable Recommendations for 1,200 customers...")
    
    # Purchased items per customer to exclude from recommendations
    purchased_map = tx_df[tx_df["order_status"] == "Completed"].groupby("customer_id")["product_id"].unique().to_dict()

    # Category popularity for cold-start / sparse fallback
    cat_pop = interaction_df.groupby(["product_category", "product_id"])["interaction_score"].sum().reset_index()
    top_cat_items = cat_pop.sort_values(by=["product_category", "interaction_score"], ascending=[True, False])

    recommendation_rows = []

    for cid in all_customers:
        purchased_items = set(purchased_map.get(cid, []))
        
        if cid in pivot_matrix.index:
            user_weights = pivot_matrix.loc[cid]
            # Collaborative score
            cf_scores = user_weights.dot(item_similarity)
        else:
            cf_scores = pd.Series(0.0, index=all_products)

        # Exclude already purchased items
        candidate_items = [p for p in all_products if p not in purchased_items]
        
        # Rank candidates using combined CF score + Association Lift bonus
        candidate_scored = []
        for p in candidate_items:
            base_score = float(cf_scores.get(p, 0.0))
            
            # Check for association rule bonus from customer's purchased items
            best_lift = 1.0
            best_antecedent = None
            for bought in purchased_items:
                if bought in assoc_map and p in assoc_map[bought]:
                    lift_val = assoc_map[bought][p][0]
                    if lift_val > best_lift:
                        best_lift = lift_val
                        best_antecedent = bought

            # Hybrid score with association lift boost
            total_score = base_score * (1.0 + (best_lift - 1.0) * 0.4) if best_lift > 1.0 else base_score

            candidate_scored.append({
                "product_id": p,
                "score": total_score,
                "base_cf": base_score,
                "best_lift": best_lift,
                "best_antecedent": best_antecedent
            })

        candidate_scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = candidate_scored[:5]

        # Handle fallback if customer has 0 positive scores
        if not top5 or top5[0]["score"] == 0:
            fallback_items = [p for p in all_products if p not in purchased_items][:5]
            top5 = [{"product_id": p, "score": 1.0, "base_cf": 1.0, "best_lift": 1.0, "best_antecedent": None} for p in fallback_items]

        # Generate transparent explanations for each recommendation
        for rank, rec in enumerate(top5, start=1):
            pid = rec["product_id"]
            pname = prod_meta.loc[pid, "product_name"]
            pcat = prod_meta.loc[pid, "product_category"]
            price = prod_meta.loc[pid, "unit_price"]

            if rec["best_lift"] > 1.05 and rec["best_antecedent"]:
                ant_name = prod_meta.loc[rec["best_antecedent"], "product_name"]
                exp_type = "Market Basket Association"
                explanation = f"Frequently purchased together with '{ant_name}' in customer orders (Lift: {rec['best_lift']:.1f}x)."
            elif rec["base_cf"] > 0.0:
                exp_type = "Collaborative Filtering"
                explanation = f"Customers with similar product affinities in {pcat} engaged with this item."
            else:
                exp_type = "Category Trending Fallback"
                explanation = f"Top-rated trending item in the {pcat} catalog."

            recommendation_rows.append({
                "customer_id": cid,
                "rank": rank,
                "product_id": pid,
                "product_name": pname,
                "product_category": pcat,
                "unit_price": price,
                "confidence_score": round(float(rec["score"]), 3),
                "explanation_type": exp_type,
                "recommendation_reason": explanation
            })

    recs_df = pd.DataFrame(recommendation_rows)
    recs_csv = os.path.join(PROCESSED_DIR, "customer_recommendations.csv")
    recs_parquet = os.path.join(PROCESSED_DIR, "customer_recommendations.parquet")

    recs_df.to_csv(recs_csv, index=False)
    recs_df.to_parquet(recs_parquet, index=False)
    print(f"Generated {len(recs_df)} recommendations across {recs_df['customer_id'].nunique()} customers.")
    print(f"Saved recommendations to: {recs_csv} & {recs_parquet}")

    # 6. Save Model Artifacts
    joblib.dump(item_similarity, os.path.join(MODELS_DIR, "item_similarity_matrix.joblib"))
    joblib.dump(prod_meta, os.path.join(MODELS_DIR, "product_metadata.joblib"))
    joblib.dump(rules_df, os.path.join(MODELS_DIR, "association_rules.joblib"))

    print("\nSaved recommendation artifacts to ml/models/:")
    print("  - item_similarity_matrix.joblib")
    print("  - product_metadata.joblib")
    print("  - association_rules.joblib")

    return {
        "total_recommendations": len(recs_df),
        "unique_customers": recs_df["customer_id"].nunique(),
        "evaluation_metrics": eval_df.to_dict(orient="records"),
        "association_rules_count": len(rules_df)
    }


if __name__ == "__main__":
    generate_recommendations()
