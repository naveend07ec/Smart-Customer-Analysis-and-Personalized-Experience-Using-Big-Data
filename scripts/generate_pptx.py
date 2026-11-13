"""
Generate Professional Presentation Slides (.pptx)
Project: Smart Customer Analysis and Personalized Experience Using Big Data
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    PRIMARY = RGBColor(15, 23, 42)     # #0f172a Deep Slate
    ACCENT = RGBColor(99, 102, 241)    # #6366f1 Indigo
    SECONDARY = RGBColor(30, 41, 59)   # #1e293b Card Navy
    TEXT_LIGHT = RGBColor(241, 245, 249) # #f1f5f9
    TEXT_MUTED = RGBColor(148, 163, 184) # #94a3b8
    WHITE = RGBColor(255, 255, 255)

    def set_slide_background(slide):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = PRIMARY

    def add_header(slide, title_text, category_text="FINAL YEAR ACADEMIC PROJECT DEFENSE"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = category_text.upper()
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT

        p2 = tf.add_paragraph()
        p2.text = title_text
        p2.font.size = Pt(24)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_LIGHT

    # Slide 1: Title
    blank_layout = prs.slide_layouts[6]
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "FINAL YEAR ACADEMIC PROJECT PRESENTATION"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT

    p1 = tf.add_paragraph()
    p1.text = "Smart Customer Analysis & Personalized Experience\nUsing Big Data"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT

    p2 = tf.add_paragraph()
    p2.text = "\nAn End-to-End Distributed Big Data, Machine Learning, and Analytics Platform"
    p2.font.size = Pt(16)
    p2.font.color.rgb = TEXT_MUTED

    p3 = tf.add_paragraph()
    p3.text = "\nTechnologies: PySpark 3.5.1 | Hadoop HDFS | Scikit-learn | Flask REST API | React 18 & Chart.js"
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = ACCENT

    # Slide 2: Problem Statement & Motivation
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Problem Statement & Industry Motivation")

    card_left = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    card_left.fill.solid()
    card_left.fill.fore_color.rgb = SECONDARY
    card_left.line.color.rgb = RGBColor(51, 65, 85)
    tf_l = card_left.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "The Challenge in Modern E-Commerce"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    bullets_l = [
        "Data Fragmentation: Transaction logs, clickstream records, and social sentiment live in isolated silos.",
        "Scalability Bottlenecks: Traditional single-node systems fail when processing hundreds of thousands of events.",
        "Generic Clustering: Typical segmentation groups customers without explainability or actionable business context.",
        "Black-Box Recommendations: Standard recommendation engines fail to provide transparent reasons for customer suggestions."
    ]
    for b in bullets_l:
        p = tf_l.add_paragraph()
        p.text = f"\n• {b}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT

    card_right = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0))
    card_right.fill.solid()
    card_right.fill.fore_color.rgb = SECONDARY
    card_right.line.color.rgb = RGBColor(51, 65, 85)
    tf_r = card_right.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Our Proposed Big Data Solution"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    bullets_r = [
        "Distributed Ingestion: Ingests 142,000+ raw records across transactions, web activity, and social media via PySpark.",
        "Explainable K-Means: Optimal 5-cluster segmentation with mathematically proven Silhouette score (0.3533).",
        "Hybrid Recommendation Engine: Blends collaborative filtering with 541 Market Basket association rules.",
        "Real-Time React Dashboard: 6 interactive analytics pages powered by a production-ready Flask REST API."
    ]
    for b in bullets_r:
        p = tf_r.add_paragraph()
        p.text = f"\n• {b}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT

    # Slide 3: System Architecture
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Multi-Tier Distributed Architecture")

    layers = [
        ("Layer 1: Multi-Source Ingestion", "Transactions (12.2k) | Web Logs (121k) | Social Sentiment (8.8k)", "Dual storage: Local Staged Parquet & Hadoop HDFS"),
        ("Layer 2: PySpark Processing", "Distributed Ingestion & Cleaning | Pre-aggregation by customer_id", "Generates 24-column Unified Customer Behavioral Matrix"),
        ("Layer 3: Machine Learning & Recs", "K-Means (k=5) + PCA 2D coordinates | Silhouette = 0.3533", "Item-based Collaborative Filtering + Market Basket Mining"),
        ("Layer 4: REST API & Analytics UI", "15 Flask Endpoints serving real batch analytics results", "React 18 + Vite + Chart.js across 6 responsive views")
    ]
    for i, (title, desc1, desc2) in enumerate(layers):
        y = Inches(1.8 + i * 1.3)
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.7), Inches(1.1))
        card.fill.solid()
        card.fill.fore_color.rgb = SECONDARY
        card.line.color.rgb = ACCENT if i == 1 or i == 2 else RGBColor(51, 65, 85)
        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT

        p2 = tf.add_paragraph()
        p2.text = f"{desc1}  —  {desc2}"
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_LIGHT

    # Slide 4: Results & K-Means Clusters
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Customer Segmentation: 5 Behavioral Personas")

    clusters = [
        ("Cluster 0: Churn-Risk Inactives", "13.67%", "Spend: $321.40 | Recency: 84.1d | Neg Sentiment", "At-risk customers needing re-engagement campaigns"),
        ("Cluster 1: Tech-Savvy Researchers", "23.42%", "Spend: $1,420.10 | 148 web acts | 8.2 cart adds", "High browsing engagement and high cart affinity"),
        ("Cluster 2: Disengaged Dissatisfied", "15.08%", "Spend: $412.30 | Cancellation: 8.4% | Sentiment: -0.42", "High return/cancellation rates, negative sentiment"),
        ("Cluster 3: Social Brand Advocates", "20.58%", "Spend: $1,845.60 | 9.8 social acts | Sentiment: +0.76", "Strong social media sentiment and engagement"),
        ("Cluster 4: High-Value VIP Champions", "27.25%", "Spend: $2,890.50 | 14.2 orders | AOV: $203.55", "Top revenue drivers and highly frequent shoppers")
    ]
    for i, (name, pct, stats, action) in enumerate(clusters):
        y = Inches(1.8 + i * 1.05)
        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.7), Inches(0.95))
        card.fill.solid()
        card.fill.fore_color.rgb = SECONDARY
        card.line.color.rgb = RGBColor(51, 65, 85)
        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{name} ({pct})"
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT

        p2 = tf.add_paragraph()
        p2.text = f"{stats} | Strategy: {action}"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_LIGHT

    # Slide 5: Recommendation Engine & Summary
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Recommendation Engine & Project Conclusion")

    c1 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    c1.fill.solid()
    c1.fill.fore_color.rgb = SECONDARY
    c1.line.color.rgb = RGBColor(51, 65, 85)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Explainable Recommendation System"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    b1 = [
        "Item-Based Collaborative Filtering: Cosine similarity on weighted interaction matrix (purchases=5, checkout=4, cart=3, view=1).",
        "Market Basket Association Mining: 541 validated rules with Support >= 0.01 and Confidence >= 0.20.",
        "Explainable Rationales: Clear English explanations for every recommended item (e.g., 'Frequently bought with your Wireless Mouse').",
        "Offline Verification: Precision@5 = 0.248, Recall@5 = 0.382, Catalog Coverage = 88.5%."
    ]
    for b in b1:
        p = tf1.add_paragraph()
        p.text = f"\n• {b}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_LIGHT

    c2 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0))
    c2.fill.solid()
    c2.fill.fore_color.rgb = SECONDARY
    c2.line.color.rgb = RGBColor(51, 65, 85)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Academic Summary & Key Takeaways"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    b2 = [
        "100% Open-Source & Reproducible: Zero cloud fees, zero paid APIs, optimized for 8 GB RAM machines.",
        "Zero Fake Data in Dashboard: 100% of frontend metrics are derived directly from actual PySpark batch results.",
        "Full Software Lifecycle: From raw big data schemas to ML clustering, REST endpoints, and modern React UI.",
        "Transferable Repository: Fully documented with unit tests, scripts, IEEE-style report, and viva Q&A guide."
    ]
    for b in b2:
        p = tf2.add_paragraph()
        p.text = f"\n• {b}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_LIGHT

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation_deck.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_deck()
