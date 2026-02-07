import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from google import genai
from PIL import Image
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class MysteryShopperAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.screenshots = []
        self.action_history = []
        
    async def get_ai_decision(self, screenshot_path, goal, history, step):
        """AI decision making with error handling"""
        try:
            raw_image = Image.open(screenshot_path)
            
            prompt = f"""
You are an Autonomous AI Mystery Shopper analyzing a website.

Goal: {goal}
Step: {step}
Previous Actions: {history[-3:] if history else []}

RULES:
- Don't repeat cookie acceptance
- Look for: Sign In, Login, Register, Create Account, Get Started
- Analyze forms for UX quality
- After 5-6 steps or reaching signup, finish

Return JSON:
{{
    "action": "click" | "scroll" | "finish",
    "label": "button/link text",
    "value": "",
    "reason": "why taking this action",
    "ux_observation": "UX issues noticed"
}}
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[prompt, raw_image],
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except Exception as e:
            return {
                "action": "finish",
                "label": "Analysis complete",
                "value": "",
                "reason": f"AI error: {str(e)[:50]}",
                "ux_observation": "Error occurred"
            }
    
    async def analyze_screenshot_ux(self, screenshot_path, page_context):
        """UX analysis with error handling"""
        try:
            raw_image = Image.open(screenshot_path)
            
            prompt = f"""
Analyze this screenshot from: {page_context}

Return JSON:
{{
    "page_type": "homepage | signup | login | other",
    "ux_issues": [
        {{
            "severity": "high | medium | low",
            "issue": "description",
            "location": "where",
            "impact": "conversion impact"
        }}
    ],
    "positive_aspects": ["good practices"],
    "actionable_suggestions": [
        {{
            "suggestion": "what to improve",
            "implementation": "how to fix",
            "expected_impact": "improvement estimate"
        }}
    ],
    "conversion_score": 75,
    "overall_assessment": "summary"
}}
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[prompt, raw_image],
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except Exception as e:
            return {
                "page_type": "unknown",
                "ux_issues": [],
                "positive_aspects": [],
                "actionable_suggestions": [],
                "conversion_score": 0,
                "overall_assessment": f"Analysis error: {str(e)[:50]}"
            }
    
    async def run_journey(self, start_url, goal, max_steps=8, progress_callback=None):
        """Run complete journey with robust error handling"""
        async with async_playwright() as p:
            try:
                # Launch browser with extra args for stability
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                page.set_default_timeout(90000)  # 90 seconds global timeout
                
                if progress_callback:
                    progress_callback(f"🚀 Loading: {start_url}", 0)
                
                # Multiple loading strategies with error recovery
                page_loaded = False
                try:
                    # Strategy 1: Load without waiting for everything
                    await page.goto(start_url, wait_until="commit", timeout=90000)
                    await asyncio.sleep(3)  # Let page start rendering
                    page_loaded = True
                    if progress_callback:
                        progress_callback(f"✅ Page accessible", 10)
                except Exception as e1:
                    if progress_callback:
                        progress_callback(f"⚠️ Trying alternative loading...", 5)
                    try:
                        # Strategy 2: Direct navigation
                        await page.goto(start_url, timeout=90000)
                        page_loaded = True
                    except Exception as e2:
                        if progress_callback:
                            progress_callback(f"❌ Cannot load page: {str(e2)[:50]}", 0)
                        await browser.close()
                        return []
                
                if not page_loaded:
                    await browser.close()
                    return []
                
                # Journey steps
                for step in range(1, max_steps + 1):
                    try:
                        # Wait for page to settle
                        await asyncio.sleep(2)
                        
                        # Screenshot
                        screenshot_path = f"step_{step}_{datetime.now().strftime('%H%M%S')}.png"
                        
                        try:
                            await page.screenshot(path=screenshot_path, timeout=20000)
                        except Exception as e:
                            if progress_callback:
                                progress_callback(f"⚠️ Screenshot failed, skipping step", None)
                            continue
                        
                        if progress_callback:
                            progress_callback(f"📸 Step {step}: Analyzing...", 10 + (step / max_steps * 40))
                        
                        # AI Analysis
                        decision = await self.get_ai_decision(screenshot_path, goal, self.action_history, step)
                        ux_analysis = await self.analyze_screenshot_ux(screenshot_path, page.url)
                        
                        # Store results
                        self.screenshots.append({
                            'path': screenshot_path,
                            'step': step,
                            'url': page.url,
                            'decision': decision,
                            'ux_analysis': ux_analysis
                        })
                        
                        if progress_callback:
                            progress_callback(
                                f"🤖 Step {step}: {decision['action']} - {decision['label'][:40]}", 
                                50 + (step / max_steps * 40)
                            )
                        
                        # Execute action
                        if decision['action'] == "finish":
                            if progress_callback:
                                progress_callback(f"✅ Journey complete!", 100)
                            break
                        
                        elif decision['action'] == "click":
                            clicked = False
                            label = decision['label']
                            
                            # Try multiple click strategies
                            for strategy in [
                                lambda: page.get_by_text(label, exact=False).first,
                                lambda: page.get_by_role("button", name=label).first,
                                lambda: page.get_by_role("link", name=label).first,
                                lambda: page.locator(f"text={label}").first
                            ]:
                                try:
                                    element = strategy()
                                    await element.click(timeout=5000)
                                    clicked = True
                                    self.action_history.append(f"Clicked: {label}")
                                    await asyncio.sleep(2)
                                    break
                                except:
                                    continue
                            
                            if not clicked and progress_callback:
                                progress_callback(f"⚠️ Could not click: {label[:30]}", None)
                        
                        elif decision['action'] == "scroll":
                            try:
                                await page.evaluate("window.scrollBy(0, 500)")
                                await asyncio.sleep(1)
                            except:
                                pass
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"⚠️ Step {step} error: {str(e)[:40]}", None)
                        await asyncio.sleep(2)
                        continue
                
                await browser.close()
                
                if progress_callback:
                    progress_callback("✅ Analysis complete!", 100)
                
                return self.screenshots
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Fatal error: {str(e)[:50]}", 0)
                return []


# ==================== STREAMLIT UI ====================

st.set_page_config(
    page_title="AI Mystery Shopper Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
    }
    
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0 0 1rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: -1px;
    }
    
    .hero p {
        font-size: 1.3rem;
        opacity: 0.95;
        margin: 0.5rem 0;
        font-weight: 300;
    }
    
    .hero .subtitle {
        font-size: 1rem;
        opacity: 0.85;
        margin-top: 1rem;
        font-weight: 400;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 2rem 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
    }
    
    .metric-card h2 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card p {
        color: #718096;
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    /* Status Boxes */
    .status-success {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 5px solid #48bb78;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(72, 187, 120, 0.15);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fffaf0 0%, #feebc8 100%);
        border-left: 5px solid #ed8936;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(237, 137, 54, 0.15);
    }
    
    .status-info {
        background: linear-gradient(135deg, #ebf4ff 0%, #c3dafe 100%);
        border-left: 5px solid #4299e1;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(66, 153, 225, 0.15);
    }
    
    .status-error {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border-left: 5px solid #f56565;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(245, 101, 101, 0.15);
    }
    
    /* Issue Cards */
    .issue-high {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border-left: 5px solid #f56565;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
    }
    
    .issue-medium {
        background: linear-gradient(135deg, #fffaf0 0%, #feebc8 100%);
        border-left: 5px solid #ed8936;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
    }
    
    .issue-low {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 5px solid #48bb78;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
        cursor: not-allowed;
        opacity: 0.6;
    }
    
    /* Progress */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: white;
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    
    /* Screenshot Container */
    .screenshot-box {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    /* Hide Streamlit UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Expander */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 1rem;
    }
    
    /* Footer */
    .custom-footer {
        text-align: center;
        padding: 3rem 1rem;
        color: #718096;
        margin-top: 3rem;
        border-top: 2px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
<div class="hero">
    <h1>🔍 AI Mystery Shopper</h1>
    <p>Advanced Website UX Analysis & Conversion Optimization</p>
    <p class="subtitle">Powered by Google Gemini AI • Real User Simulation • Actionable Insights</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    
    # API Key Section
    st.markdown("### 🔑 API Settings")
    
    default_api = os.getenv("GEMINI_API_KEY", "AIzaSyD3nLbORp57TSjWh_wiMW-WRCtW0p1FWWs")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=default_api,
        placeholder="Enter your API key...",
        help="Get free API key from https://aistudio.google.com/app/apikey"
    )
    
    # API Status Indicator
    if api_key:
        st.markdown("""
        <div class="status-success">
            <strong>✅ API Key Active</strong><br>
            <small>Ready to analyze</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-warning">
            <strong>⚠️ API Key Required</strong><br>
            <small><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #ed8936; font-weight: 600;">Get Free Key →</a></small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Website Settings
    st.markdown("### 🌐 Website Settings")
    
    target_url = st.text_input(
        "Target URL",
        value="https://google.com",
        placeholder="https://example.com",
        help="Enter complete URL with https://"
    )
    
    goal = st.text_area(
        "Analysis Goal",
        value="Navigate to sign-up page and analyze user experience",
        height=80,
        help="What should the AI accomplish?"
    )
    
    max_steps = st.slider(
        "Max Steps",
        min_value=3,
        max_value=12,
        value=6,
        help="Number of steps to analyze"
    )
    
    st.markdown("---")
    
    # Features
    st.markdown("### ✨ Features")
    st.markdown("""
    <div class="status-info">
        🤖 AI Navigation<br>
        📸 Screenshots<br>
        🧠 UX Analysis<br>
        💡 Recommendations<br>
        📊 Scoring<br>
        📥 Export Reports
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Guide
    with st.expander("📚 Quick Guide"):
        st.markdown("""
        1. Enter API key
        2. Set target URL
        3. Define goal
        4. Click Start
        5. Review results
        6. Download report
        
        **Tip:** Use specific goals for best results
        """)
    
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; color: #a0aec0; font-size: 0.85rem; margin-top: 2rem;'>
        <strong>Made with ❤️</strong><br>
        Powered by Gemini AI
    </div>
    """, unsafe_allow_html=True)

# Main Control Panel
st.markdown("## 🎮 Control Panel")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    start_btn = st.button(
        "🚀 Start Analysis",
        disabled=not api_key,
        use_container_width=True
    )

with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        if 'results' in st.session_state:
            del st.session_state['results']
        st.rerun()

with col3:
    help_btn = st.button("❓ Help", use_container_width=True)
    if help_btn:
        st.info("Enter API key → Set URL → Click Start → View Results")

st.markdown("---")

# Progress Section
if not api_key:
    st.markdown("""
    <div class="status-warning">
        <h3>⚠️ API Key Required</h3>
        <p>Enter your Google Gemini API key in the sidebar to begin.</p>
        <p><strong>Get your free key:</strong></p>
        <ol>
            <li>Visit <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
            <li>Click "Create API Key"</li>
            <li>Copy and paste in sidebar</li>
        </ol>
        <p style="font-size: 0.9rem; color: #718096; margin-top: 1rem;">
            💡 Free tier includes generous quotas
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    progress_bar = st.progress(0)
    status_text = st.empty()

# Run Analysis
if start_btn and api_key:
    if not target_url or not target_url.startswith('http'):
        st.error("❌ Please enter a valid URL starting with http:// or https://")
    else:
        def update_progress(msg, prog):
            status_text.text(msg)
            if prog is not None:
                progress_bar.progress(min(int(prog), 100))
        
        try:
            with st.spinner("🔄 Initializing AI..."):
                shopper = MysteryShopperAI(api_key)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                shopper.run_journey(target_url, goal, max_steps, update_progress)
            )
            
            if results:
                st.session_state['results'] = results
                st.markdown("""
                <div class="status-success">
                    <h3>✅ Analysis Complete!</h3>
                    <p>Scroll down to view detailed insights</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            else:
                st.error("❌ Analysis failed. Please check the URL and try again.")
                
        except Exception as e:
            st.markdown(f"""
            <div class="status-error">
                <h3>❌ Error Occurred</h3>
                <p><strong>Details:</strong> {str(e)[:100]}</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Verify the URL is accessible</li>
                    <li>Check your API key</li>
                    <li>Try a different website</li>
                    <li>Reduce max steps</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# Display Results
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Dashboard")
    
    # Metrics
    st.markdown("### 📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{len(results)}</h2>
            <p>Total Steps</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_score = sum([r['ux_analysis'].get('conversion_score', 0) for r in results]) / len(results) if results else 0
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {'#48bb78' if avg_score >= 70 else '#ed8936' if avg_score >= 50 else '#f56565'};">
            <h2>{avg_score:.0f}%</h2>
            <p>Avg Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_issues = sum([len(r['ux_analysis'].get('ux_issues', [])) for r in results])
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ed8936;">
            <h2>{total_issues}</h2>
            <p>Issues Found</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        high_issues = sum([len([i for i in r['ux_analysis'].get('ux_issues', []) if i.get('severity') == 'high']) for r in results])
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f56565;">
            <h2>{high_issues}</h2>
            <p>High Priority</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Top Recommendations
    with st.expander("💡 Key Recommendations", expanded=True):
        all_suggestions = []
        for r in results:
            all_suggestions.extend(r['ux_analysis'].get('actionable_suggestions', []))
        
        if all_suggestions:
            for idx, sug in enumerate(all_suggestions[:5], 1):
                st.markdown(f"""
                <div class="status-info">
                    <strong>#{idx}: {sug.get('suggestion', 'N/A')}</strong><br>
                    <small>{sug.get('implementation', 'N/A')}</small><br>
                    <small><em>Impact: {sug.get('expected_impact', 'N/A')}</em></small>
                </div>
                """, unsafe_allow_html=True)
    
    # Step by Step
    st.markdown("---")
    st.markdown("### 🎬 Journey Details")
    
    for idx, result in enumerate(results):
        conv = result['ux_analysis'].get('conversion_score', 0)
        emoji = "🟢" if conv >= 70 else "🟡" if conv >= 50 else "🔴"
        
        with st.expander(f"{emoji} Step {result['step']}: {result['decision']['label'][:50]}...", expanded=(idx==0)):
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.markdown('<div class="screenshot-box">', unsafe_allow_html=True)
                st.image(result['path'], use_container_width=True)
                st.caption(f"🌐 {result['url']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                dec = result['decision']
                st.markdown(f"""
                <div class="status-info">
                    <strong>Action:</strong> {dec['action'].upper()}<br>
                    <strong>Target:</strong> {dec['label']}<br>
                    <strong>Reason:</strong> {dec['reason']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                ux = result['ux_analysis']
                
                # Scores
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2>{conv}%</h2>
                        <p>Conv. Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2>{ux.get('page_type', 'Unknown')}</h2>
                        <p>Page Type</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Issues
                if ux.get('ux_issues'):
                    st.markdown("**⚠️ Issues:**")
                    for issue in ux['ux_issues']:
                        sev = issue.get('severity', 'medium')
                        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
                        st.markdown(f"""
                        <div class="issue-{sev}">
                            <strong>{icon} {sev.upper()}</strong><br>
                            {issue.get('issue', 'N/A')}<br>
                            <small>📍 {issue.get('location', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Suggestions
                if ux.get('actionable_suggestions'):
                    st.markdown("**💡 Suggestions:**")
                    for sug in ux['actionable_suggestions']:
                        st.markdown(f"""
                        <div class="status-info">
                            <strong>{sug.get('suggestion', 'N/A')}</strong><br>
                            <small>{sug.get('implementation', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Downloads
    st.markdown("---")
    st.markdown("## 📥 Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report = {
            'url': target_url,
            'goal': goal,
            'timestamp': datetime.now().isoformat(),
            'steps': len(results),
            'data': results
        }
        
        st.download_button(
            "💾 Download JSON",
            json.dumps(report, indent=2),
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )
    
    with col2:
        summary = f"""AI Mystery Shopper Report
{'='*50}
URL: {target_url}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Steps: {len(results)}
Avg Score: {sum([r['ux_analysis'].get('conversion_score', 0) for r in results]) / len(results):.1f}%
"""
        st.download_button(
            "📝 Download Summary",
            summary,
            f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain",
            use_container_width=True
        )

# Footer
st.markdown("""
<div class="custom-footer">
    <p style="font-size: 1.2rem; font-weight: 600; color: #667eea;">
        🔍 AI Mystery Shopper Pro
    </p>
    <p style="margin: 0.5rem 0;">
        Advanced UX Analysis Platform
    </p>
    <p style="font-size: 0.9rem; color: #a0aec0;">
        Powered by Google Gemini AI • v1.0
    </p>
</div>
""", unsafe_allow_html=True)
