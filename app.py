import gradio as gr
from pypdf import PdfReader

# --- ADVANCED RESUME SCANNER ENGINE ---
def analyze_resume(pdf_file):
    if pdf_file is None:
        return (
            "<div class='output-card animated-border'><span style='color: #ef4444; font-weight: bold;'>⚠️ Please upload a valid PDF file!</span></div>", 
            "<div class='output-card animated-border'><span style='color: #ef4444; font-weight: bold;'>❌ Diagnostic offline.</span></div>"
        )
    
    try:
        reader = PdfReader(pdf_file.name)
        resume_text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                resume_text += content
        
        text = resume_text.lower()
        skills_found = []
        recommendations = []
        
        # Matrix Categories
        categories = {
            "Development & Engineering": {
                "keywords": ['html', 'css', 'javascript', 'react', 'node', 'web development', 'java', 'c', 'python', 'software', 'git', 'sql', 'backend', 'frontend'],
                "role": "💻 Software Engineer / Web Developer"
            },
            "AI & Smart Systems (IoT)": {
                "keywords": ['data science', 'machine learning', 'pandas', 'ai', 'analytics', 'ollama', 'n8n', 'arduino', 'esp32', 'esp8266', 'iot', 'robotics'],
                "role": "📊 AI Automation & IoT Solutions Engineer"
            },
            "UI/UX & Creative Architecture": {
                "keywords": ['ui', 'ux', 'figma', 'photoshop', 'illustrator', 'design', 'blender', '3d modeling', 'animation'],
                "role": "🎨 UI/UX Designer / 3D Asset Creator"
            }
        }
        
        for cat, data in categories.items():
            found = [s for s in data["keywords"] if s in text]
            if found:
                skills_found.extend(found)
                recommendations.append(data["role"])
        
        # HTML UI Formatting for Output
        if skills_found:
            skills_html = f"<div class='output-card container-glow'>{''.join([f'<span class=\"skill-badge\">{s.upper()}</span>' for s in set(skills_found)])}</div>"
        else:
            skills_html = "<div class='output-card container-glow'><span class='skill-badge-warn'>No Core Tech Keywords Detected</span></div>"
            
        if recommendations:
            jobs_html = f"<div class='output-card container-glow'>{''.join([f'<div class=\"job-item\">✨ {job}</div>' for job in recommendations])}</div>"
        else:
            jobs_html = "<div class='output-card container-glow'><div class='job-item'>🏢 Junior Technical Associate / Corporate Operations</div></div>"
            
        return jobs_html, skills_html

    except Exception as e:
        return f"<div class='output-card'><span style='color: #ef4444;'>Error: {str(e)}</span></div>", "Error."

# --- CINEMATIC CYBERPUNK CSS WITH CUSTOM ANIMATIONS ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght=600;700&display=swap');

.gradio-container {
    background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #090514 80%) !important;
    border: 2px solid #3b82f6 !important;
    border-radius: 24px !important;
    box-shadow: 0 0 40px rgba(59, 130, 246, 0.2), inset 0 0 20px rgba(168, 85, 247, 0.1);
    padding: 35px !important;
}

h1, h2, h3, p, span, label {
    font-family: 'Rajdhani', sans-serif !important;
}

.title-glow {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 900;
    font-size: 3.2rem !important;
    text-transform: uppercase;
    text-align: center;
    letter-spacing: 4px;
    background: linear-gradient(90deg, #00f2fe 0%, #4facfe 30%, #0000ff 70%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: textPulse 4s infinite ease-in-out;
}

@keyframes textPulse {
    0%, 100% { filter: drop-shadow(0 0 10px rgba(0,242,254,0.3)); }
    50% { filter: drop-shadow(0 0 25px rgba(168,85,247,0.6)); }
}

.panel-box {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(56, 189, 248, 0.15) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px);
    padding: 20px !important;
}

.file-box {
    background: rgba(13, 10, 31, 0.6) !important;
    border: 2px dashed #a855f7 !important;
    border-radius: 14px !important;
    box-shadow: inset 0 0 15px rgba(168, 85, 247, 0.1);
    transition: all 0.4s ease-in-out;
}
.file-box:hover {
    border-color: #00f2fe !important;
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.3), inset 0 0 10px rgba(0, 242, 254, 0.2);
}

.cyber-btn {
    background: linear-gradient(135deg, #00f2fe 0%, #a855f7 100%) !important;
    color: #ffffff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.25rem !important;
    letter-spacing: 2px;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}
.cyber-btn:hover {
    transform: scale(1.02);
    box-shadow: 0 0 30px rgba(0, 242, 254, 0.8) !important;
    text-shadow: 0 0 8px #fff;
}

.output-card {
    background: rgba(9, 5, 20, 0.75);
    border: 1px solid rgba(168, 85, 247, 0.2);
    border-radius: 14px;
    padding: 20px;
    min-height: 120px;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.6);
}

.container-glow {
    border: 1px solid rgba(0, 242, 254, 0.3);
    animation: borderGlow 3s infinite alternate;
}

@keyframes borderGlow {
    0% { border-color: rgba(0, 242, 254, 0.2); box-shadow: 0 0 10px rgba(0, 242, 254, 0.05); }
    100% { border-color: rgba(168, 85, 247, 0.5); box-shadow: 0 0 15px rgba(168, 85, 247, 0.2); }
}

.skill-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.1), rgba(168, 85, 247, 0.15));
    color: #00f2fe;
    border: 1px solid rgba(0, 242, 254, 0.4);
    padding: 8px 16px;
    margin: 6px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 0.95rem;
    box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
    transition: all 0.3s ease;
}
.skill-badge:hover {
    transform: translateY(-2px);
    color: #fff;
    background: #a855f7;
    border-color: #a855f7;
    box-shadow: 0 0 15px #a855f7;
}

.job-item {
    background: rgba(255, 255, 255, 0.03);
    border-left: 4px solid #00f2fe;
    color: #e2e8f0;
    padding: 14px 20px;
    margin-bottom: 12px;
    border-radius: 0 10px 10px 0;
    font-size: 1.2rem;
    font-weight: 700;
    transition: all 0.3s;
}
.job-item:hover {
    background: rgba(0, 242, 254, 0.08);
    transform: translateX(5px);
}
"""

sound_js = """
function playCyberSound() {
    var audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2568/2568-84.wav');
    audio.volume = 0.5;
    audio.play();
}
"""

with gr.Blocks(css=custom_css, theme=gr.themes.Default(), js=sound_js) as demo:
    gr.HTML("<div style='display:none;'></div>")
    gr.Markdown("<h1 class='title-glow'>QUANTUM MATRIX AI</h1>")
    gr.Markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.35rem; letter-spacing: 1px; margin-bottom: 35px;'>Next-Gen Cybernetic Profile & Industry Diagnostics</p>")
    
    with gr.Row():
        with gr.Column(scale=1, elem_classes="panel-box"):
            gr.Markdown("<h3 style='color: #00f2fe; font-size: 1.4rem; margin-bottom: 8px;'>⚡ CORE INPUT PORT</h3>")
            file_input = gr.File(label="Feed System Dossier (PDF)", file_types=[".pdf"], elem_classes="file-box")
            submit_btn = gr.Button("💥 INITIALIZE DIAGNOSTICS", elem_classes="cyber-btn")
            
        with gr.Column(scale=1, elem_classes="panel-box"):
            gr.Markdown("<h3 style='color: #a855f7; font-size: 1.4rem; margin-bottom: 8px;'>🔮 QUANTUM ANALYTICS</h3>")
            gr.Markdown("<span style='color: #94a3b8; font-size: 1.1rem; font-weight: bold;'>🔑 Extracted Competencies:</span>")
            output_skills = gr.HTML(value="<div class='output-card'><span style='color:#475569;'>System idling...</span></div>")
            
            gr.Markdown("<br><span style='color: #94a3b8; font-size: 1.1rem; font-weight: bold;'>🎯 Recommended Vector Paths:</span>")
            output_jobs = gr.HTML(value="<div class='output-card'><span style='color:#475569;'>System idling...</span></div>")
            
    submit_btn.click(
        fn=analyze_resume, 
        inputs=file_input, 
        outputs=[output_jobs, output_skills],
        js="() => { playCyberSound(); }"
    )

if __name__ == "__main__":
    demo.launch(share=True)