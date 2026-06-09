"""
Resume Batch Ranker — Improved accuracy with TF-IDF + weighted skill scoring
"""

import os
import re
import pandas as pd
import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import gradio as gr

# ─── SKILL TAXONOMY ───────────────────────────────────────────────────────────
# Each skill has a weight: rare/advanced skills score higher than common ones
SKILL_TAXONOMY = {
    "Development & Engineering": {
        # Core languages
        "python": 2, "java": 2, "javascript": 2, "typescript": 3, "c++": 3, "c#": 3,
        "go": 3, "rust": 4, "kotlin": 3, "swift": 3, "php": 1, "ruby": 2,
        # Web
        "react": 3, "vue": 3, "angular": 3, "node.js": 3, "nodejs": 3, "next.js": 3,
        "html": 1, "css": 1, "tailwind": 2, "sass": 2, "webpack": 2,
        # Backend & infra
        "django": 3, "flask": 2, "fastapi": 3, "spring boot": 4, "express": 2,
        "docker": 3, "kubernetes": 4, "aws": 3, "azure": 3, "gcp": 3, "linux": 2,
        "ci/cd": 3, "github actions": 3, "jenkins": 2,
        # DB
        "sql": 2, "postgresql": 3, "mongodb": 2, "mysql": 2, "redis": 3,
        # Other
        "git": 1, "rest api": 2, "graphql": 3, "microservices": 4, "agile": 1,
        "backend": 1, "frontend": 1, "full stack": 2, "software engineer": 1,
    },
    "AI & Data Science": {
        # Core ML/DL
        "machine learning": 3, "deep learning": 4, "neural network": 4,
        "natural language processing": 4, "nlp": 4, "computer vision": 4,
        "reinforcement learning": 5, "transformers": 4, "llm": 4,
        # Frameworks
        "tensorflow": 3, "pytorch": 4, "keras": 3, "scikit-learn": 3, "opencv": 3,
        "hugging face": 4, "langchain": 4, "openai": 3,
        # Data tools
        "pandas": 2, "numpy": 2, "matplotlib": 1, "seaborn": 1, "plotly": 2,
        "spark": 4, "hadoop": 3, "airflow": 4, "dbt": 3,
        # Analytics & BI
        "data science": 2, "data analysis": 1, "power bi": 2, "tableau": 2,
        "statistics": 2, "hypothesis testing": 3, "a/b testing": 3,
        # IoT / Embedded
        "iot": 3, "arduino": 3, "esp32": 3, "raspberry pi": 3, "robotics": 4,
        "embedded systems": 4, "rtos": 4, "mqtt": 3, "n8n": 2, "ollama": 3,
    },
    "UI/UX & Design": {
        # Design tools
        "figma": 3, "sketch": 2, "adobe xd": 2, "invision": 2, "zeplin": 2,
        "photoshop": 2, "illustrator": 2, "after effects": 3, "premiere": 2,
        # Skills
        "ui design": 2, "ux design": 3, "user research": 3, "wireframing": 2,
        "prototyping": 2, "usability testing": 3, "design system": 3,
        "information architecture": 3, "interaction design": 3,
        # 3D / Creative
        "blender": 3, "3d modeling": 3, "animation": 2, "motion graphics": 3,
        "cinema 4d": 3, "unity": 3, "unreal engine": 4,
    },
    "Project & Product Management": {
        "project management": 2, "product management": 3, "scrum": 2, "kanban": 2,
        "jira": 1, "confluence": 1, "roadmap": 2, "stakeholder": 2,
        "pmp": 4, "prince2": 4, "okr": 3, "kpi": 2,
        "business analysis": 3, "requirements gathering": 2,
    },
    "Cybersecurity": {
        "cybersecurity": 3, "penetration testing": 5, "ethical hacking": 5,
        "network security": 4, "siem": 4, "soc": 3, "vulnerability assessment": 4,
        "incident response": 4, "forensics": 4, "oscp": 5, "ceh": 4,
        "firewall": 2, "vpn": 2, "encryption": 3, "zero trust": 4, "devsecops": 4,
    }
}

# Flatten for quick lookup
ALL_SKILLS = {}
for cat, skills in SKILL_TAXONOMY.items():
    for skill, weight in skills.items():
        ALL_SKILLS[skill] = (cat, weight)

# Job Description Templates (for cosine similarity scoring)
JD_TEMPLATES = {
    "Development & Engineering": """
        software engineer developer python java javascript typescript react node docker kubernetes
        aws backend frontend full stack rest api git agile ci/cd microservices sql postgresql
    """,
    "AI & Data Science": """
        machine learning deep learning data science neural network nlp computer vision
        tensorflow pytorch pandas numpy spark statistics model training llm transformers
        data analysis feature engineering pipeline deployment mlops
    """,
    "UI/UX & Design": """
        ui ux design figma user research wireframing prototyping design system usability
        photoshop illustrator interaction design visual design user experience adobe
    """,
    "Project & Product Management": """
        project management product roadmap stakeholder scrum agile sprint planning
        requirements jira confluence okr kpi business analysis
    """,
    "Cybersecurity": """
        cybersecurity security penetration testing ethical hacking network firewall
        vulnerability assessment incident response encryption siem oscp devsecops
    """
}

# ─── PDF TEXT EXTRACTION ──────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = " ".join(
            page.extract_text() or ""
            for page in reader.pages
        )
        return text
    except Exception as e:
        return ""

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s\.\+#/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ─── SCORING ENGINE ───────────────────────────────────────────────────────────

def score_candidate(text: str, filename: str) -> dict:
    cleaned = clean_text(text)

    # 1. Weighted keyword matching
    matched_skills = {}
    for skill, (cat, weight) in ALL_SKILLS.items():
        # Use word boundary matching for better precision
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, cleaned):
            matched_skills[skill] = (cat, weight)

    # 2. Category scores (sum of weights per category)
    cat_scores = {}
    for cat in SKILL_TAXONOMY:
        cat_skills = {s: w for s, (c, w) in matched_skills.items() if c == cat}
        if cat_skills:
            # Normalize: max possible score for that category
            max_possible = sum(SKILL_TAXONOMY[cat].values())
            raw = sum(cat_skills.values())
            cat_scores[cat] = round(min(raw / max_possible * 100, 100), 1)
        else:
            cat_scores[cat] = 0.0

    # 3. TF-IDF cosine similarity against job description templates
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    docs = list(JD_TEMPLATES.values()) + [cleaned]
    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
        cosine_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
        tfidf_cat_scores = {
            cat: round(float(score) * 100, 1)
            for cat, score in zip(JD_TEMPLATES.keys(), cosine_scores)
        }
    except Exception:
        tfidf_cat_scores = {cat: 0.0 for cat in JD_TEMPLATES}

    # 4. Blend: 60% keyword weight score + 40% TF-IDF cosine
    blended = {}
    for cat in SKILL_TAXONOMY:
        kw = cat_scores.get(cat, 0)
        tf = tfidf_cat_scores.get(cat, 0)
        blended[cat] = round(0.6 * kw + 0.4 * tf, 1)

    # 5. Overall score = weighted average across categories
    overall = round(np.mean(list(blended.values())), 1)

    # 6. Best-fit role
    best_role = max(blended, key=blended.get) if blended else "General"
    best_role_score = blended[best_role]

    # 7. Top skills list
    top_skills = sorted(
        [(s, w) for s, (c, w) in matched_skills.items()],
        key=lambda x: -x[1]
    )[:15]

    # 8. Skill gap (missing high-weight skills for best role)
    best_cat_skills = SKILL_TAXONOMY.get(best_role, {})
    missing = [
        s for s, w in sorted(best_cat_skills.items(), key=lambda x: -x[1])
        if s not in matched_skills and w >= 3
    ][:5]

    return {
        "filename": filename,
        "overall_score": overall,
        "best_role": best_role,
        "best_role_score": best_role_score,
        "category_scores": blended,
        "top_skills": [s.upper() for s, _ in top_skills],
        "skill_gaps": [s.upper() for s in missing],
        "total_skills_found": len(matched_skills),
    }

# ─── GRADIO UI ────────────────────────────────────────────────────────────────

def rank_resumes(pdf_files):
    if not pdf_files:
        return (
            "<p style='color:#ef4444; padding:16px;'>⚠️ No PDF files uploaded.</p>",
            None
        )

    results = []
    for file_obj in pdf_files:
        path = file_obj.name if hasattr(file_obj, "name") else file_obj
        name = os.path.basename(path)
        raw_text = extract_text(path)
        if not raw_text.strip():
            continue
        result = score_candidate(raw_text, name)
        results.append(result)

    if not results:
        return (
            "<p style='color:#ef4444; padding:16px;'>Could not extract text from any file.</p>",
            None
        )

    # Sort by overall score
    results.sort(key=lambda x: -x["overall_score"])

    # Build HTML table
    rows = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(results):
        medal = medals[i] if i < 3 else f"#{i+1}"
        score_color = (
            "#22c55e" if r["overall_score"] >= 60
            else "#f59e0b" if r["overall_score"] >= 30
            else "#ef4444"
        )
        cat_bars = "".join(
            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:2px;'>"
            f"<span style='font-size:11px;width:170px;color:#94a3b8;'>{cat}</span>"
            f"<div style='flex:1;height:5px;background:#1e293b;border-radius:99px;'>"
            f"<div style='width:{min(sc,100)}%;height:100%;background:#7c3aed;border-radius:99px;'></div></div>"
            f"<span style='font-size:11px;color:#e2e8f0;min-width:36px;'>{sc}%</span>"
            f"</div>"
            for cat, sc in r["category_scores"].items()
        )
        skills_html = " ".join(
            f"<span style='background:#1e3a5f;color:#7dd3fc;font-size:11px;padding:2px 8px;border-radius:99px;'>{s}</span>"
            for s in r["top_skills"]
        )
        gaps_html = " ".join(
            f"<span style='background:#3b1a1a;color:#f87171;font-size:11px;padding:2px 8px;border-radius:99px;'>{g}</span>"
            for g in r["skill_gaps"]
        ) if r["skill_gaps"] else "<span style='color:#4ade80;font-size:11px;'>No major gaps</span>"

        rows += f"""
        <tr>
          <td style='padding:18px 12px; vertical-align:top; font-size:20px; text-align:center;'>{medal}</td>
          <td style='padding:18px 12px; vertical-align:top;'>
            <div style='font-weight:700;font-size:14px;color:#f1f5f9;margin-bottom:2px;'>{r["filename"].replace(".pdf","")}</div>
            <div style='font-size:12px;color:#64748b;'>{r["total_skills_found"]} skills detected</div>
          </td>
          <td style='padding:18px 12px; vertical-align:top; text-align:center;'>
            <div style='font-size:26px;font-weight:900;color:{score_color};'>{r["overall_score"]}%</div>
            <div style='font-size:11px;color:#64748b;'>overall</div>
          </td>
          <td style='padding:18px 12px; vertical-align:top;'>
            <div style='font-size:12px;font-weight:600;color:#a78bfa;margin-bottom:4px;'>Best fit → {r["best_role"]} ({r["best_role_score"]}%)</div>
            {cat_bars}
          </td>
          <td style='padding:18px 12px; vertical-align:top;'>
            <div style='font-size:11px;color:#64748b;margin-bottom:4px;'>Top skills</div>
            <div style='display:flex;flex-wrap:wrap;gap:4px;'>{skills_html}</div>
            <div style='font-size:11px;color:#64748b;margin:8px 0 4px;'>Skill gaps</div>
            <div style='display:flex;flex-wrap:wrap;gap:4px;'>{gaps_html}</div>
          </td>
        </tr>
        """

    html = f"""
    <div style='background:#0f172a;border-radius:16px;padding:24px;font-family:system-ui,sans-serif;'>
      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;'>
        <h2 style='color:#f1f5f9;margin:0;font-size:18px;'>📊 Candidate Rankings</h2>
        <span style='color:#64748b;font-size:13px;'>{len(results)} candidate(s) analyzed</span>
      </div>
      <table style='width:100%;border-collapse:collapse;'>
        <thead>
          <tr style='border-bottom:1px solid #1e293b;'>
            <th style='padding:8px 12px;color:#475569;font-size:12px;text-align:center;'>Rank</th>
            <th style='padding:8px 12px;color:#475569;font-size:12px;text-align:left;'>Candidate</th>
            <th style='padding:8px 12px;color:#475569;font-size:12px;text-align:center;'>Score</th>
            <th style='padding:8px 12px;color:#475569;font-size:12px;text-align:left;'>Category Breakdown</th>
            <th style='padding:8px 12px;color:#475569;font-size:12px;text-align:left;'>Skills</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """

    # Export CSV
    df_rows = []
    for r in results:
        df_rows.append({
            "Candidate": r["filename"],
            "Overall Score (%)": r["overall_score"],
            "Best Fit Role": r["best_role"],
            "Best Role Score (%)": r["best_role_score"],
            **{f"{cat} (%)": sc for cat, sc in r["category_scores"].items()},
            "Top Skills": ", ".join(r["top_skills"]),
            "Skill Gaps": ", ".join(r["skill_gaps"]),
        })
    df = pd.DataFrame(df_rows)
    csv_path = "/tmp/ranked_candidates.csv"
    df.to_csv(csv_path, index=False)

    return html, csv_path


# ─── LAUNCH ───────────────────────────────────────────────────────────────────

CSS = """
body { background: #05020a !important; }
.gradio-container { background: #05020a !important; }
.title { text-align:center; color:#a855f7; font-size:2rem; font-weight:900; letter-spacing:1px; padding:8px 0; }
.subtitle { text-align:center; color:#475569; margin-bottom:24px; }
footer { display:none !important; }
"""

with gr.Blocks(css=CSS, title="Resume Batch Ranker") as demo:
    gr.HTML("<h1 class='title'>⚡ Resume Batch Ranker</h1>")
    gr.HTML("<p class='subtitle'>TF-IDF + Weighted Keyword Scoring | 5 Role Categories | Skill Gap Analysis</p>")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload PDF Resumes",
                file_count="multiple",
                file_types=[".pdf"]
            )
            run_btn = gr.Button("🔍 Rank Candidates", variant="primary")

        with gr.Column(scale=2):
            html_out = gr.HTML(
                value="<p style='color:#475569;padding:16px;'>Upload resumes and click Rank Candidates.</p>"
            )
            csv_out = gr.File(label="Download CSV Report")

    run_btn.click(fn=rank_resumes, inputs=file_input, outputs=[html_out, csv_out])

demo.launch(share=True)