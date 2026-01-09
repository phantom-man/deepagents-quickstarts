import streamlit as st # type: ignore
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent path to allow imports from DeepAgents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.gui.diagnostics_service import run_diagnostics
from DeepAgents.gui.history_manager import SessionManager, list_sessions
from DeepAgents.gui.agent_runner import AgentRunner
from DeepAgents.agent_brain import AgentConfig  # New Config Manager
# from DeepAgents.list_models import get_available_models # Removed to avoid conflict with local function
from DeepAgents.asset_manager import AssetManager
from DeepAgents.model_registry import REPLICATE_MODELS, get_model_options, get_model_info 
from DeepAgents.cost_calculator import estimate_cost # NEW Cost Service

# Initialize Config
config_manager = AgentConfig()
asset_manager = AssetManager()

st.set_page_config(page_title="DeepAgents HQ", layout="wide", page_icon="🎬")

# --- CSS / STYLING ---
st.markdown("""
<style>
    .agent-box {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .director { border-left: 5px solid #FF4B4B; background-color: #262730; }
    .researcher { border-left: 5px solid #1E88E5; background-color: #262730; }
    .confidence { border-left: 5px solid #00C853; background-color: #262730; }
    .cinematographer { border-left: 5px solid #FFD600; background-color: #262730; } 
    .stSelectbox label { font-size: 0.9em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_available_models():
    """
    Checks connections and returns available models for each provider.
    """
    models = {
        "Google": {"text": [], "image": [], "video": []},
        "Anthropic": {"text": []},
        "Other": {"image": [], "video": []}
    }
    
    # Check Google
    try:
        from google import genai
        # Try to use standard env var or fallback
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
        location = "us-central1"
        if project_id:
            client = genai.Client(vertexai=True, project=project_id, location=location)
            
            # Simple list
            g_models = list(client.models.list())
            for m in g_models:
                # Ensure name exists
                if not m.name: continue
                name = m.name.split('/')[-1] # simplified name
                # Categorize
                if "gemini" in name.lower():
                    models["Google"]["text"].append(name)
                elif "imagen" in name.lower():
                     models["Google"]["image"].append(name)
                elif "veo" in name.lower():
                     models["Google"]["video"].append(name)
            
            # Fallbacks if list is empty or specific models known
            if not models["Google"]["image"]:
                models["Google"]["image"] = [
                    "imagen-4.0-ultra-generate-001",
                    "imagen-4.0-generate-001",
                    "imagen-4.0-fast-generate-001",
                    "imagen-3.0-generate-001"
                ]
            if not models["Google"]["video"]:
                models["Google"]["video"] = [
                    "veo-3.1-generate-001",
                    "veo-3.1-fast-generate-001",
                    "veo-3.0-generate-001",
                    "veo-2.0-generate-001"
                ] # Future/Preview

        else:
             # Fallback if no project ID but maybe API key
             models["Google"]["text"] = ["gemini-1.5-pro", "gemini-1.5-flash"]
             models["Google"]["image"] = ["imagen-4.0-ultra-generate-001", "imagen-3.0-generate-001"]
             models["Google"]["video"] = ["veo-3.1-generate-001", "veo-2.0-generate-001"]
                 
    except Exception as e:
        # st.toast(f"Google Connection Failed: {e}", icon="⚠️")
        # Fallback defaults
        models["Google"]["text"] = ["gemini-1.5-pro", "gemini-1.5-flash"]
        models["Google"]["image"] = ["imagen-4.0-ultra-generate-001", "imagen-3.0-generate-001"]
        models["Google"]["video"] = ["veo-3.1-generate-001", "veo-2.0-generate-001"]

    # Check Anthropic
    try:
        # Anthropic doesn't have a simple "list models" API in the same way, using standard list
        models["Anthropic"]["text"] = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620"
        ]
    except Exception as e:
        pass

    return models

# --- SIDEBAR: CONTROLS & DIAGNOSTICS ---
st.sidebar.title("🎛️ Control Center")

# 1. Diagnostics & Pre-flight
st.sidebar.subheader("System Status")

if "connection_checked" not in st.session_state:
    st.session_state.connection_checked = False
if "available_models" not in st.session_state:
    st.session_state.available_models = {}

col_chk1, col_chk2 = st.sidebar.columns([2,1])
with col_chk1:
    if st.button("🚀 Check Connections", type="primary"):
        with st.sidebar.status("Running Pre-flight Checks...", expanded=True):
            # 1. Run Diagnostics
            results = run_diagnostics()
            all_ok = True
            for sys_name, res in results.items():
                if res["status"]:
                    st.write(f"✅ {sys_name}")
                else:
                    st.write(f"❌ {sys_name}: {res.get('message')}")
                    all_ok = False
            
            # 2. Fetch Models
            st.write("📡 Querying Providers...")
            st.session_state.available_models = get_available_models()
            st.write(f"Found {len(st.session_state.available_models['Google']['text'])} Google Models")
            
            st.session_state.connection_checked = True
            st.success("Ready for Launch!")

# 2. Configuration (Selectors)
st.sidebar.divider()
st.sidebar.subheader("Agent Configuration")

agents = ["Director", "Researcher", "Confidence", "Cinematographer", "Composer"]
# Load current config
current_conf = config_manager.config 

if not st.session_state.connection_checked:
    st.sidebar.info("👋 Click 'Check Connections' to unlock configuration.")
    for agent in agents:
        with st.sidebar.expander(f"{agent} Settings", expanded=False):
            st.caption("🔒 Locked")
else:
    # Render Selectors
    for agent in agents:
        with st.sidebar.expander(f"⚙️ {agent} Settings", expanded=False):
            # Load saved values
            saved_provider = current_conf.get(agent, {}).get("provider", "Google")
            saved_model = current_conf.get(agent, {}).get("model", "gemini-1.5-flash")
            
            # 1. Provider Selector
            # Cinematographer has different providers for now (Video/Image)
            providers = ["Google", "Anthropic"]
            if agent == "Composer":
                providers = ["Google", "Anthropic", "Replicate"]
                
            try: 
                prov_idx = providers.index(saved_provider) 
            except ValueError: 
                prov_idx = 0
                
            provider = st.selectbox(f"Provider ({agent})", providers, index=prov_idx, key=f"prov_{agent}")
            
            # 2. Model Selector
            if provider in ["Google", "Anthropic"]:
                model_list = st.session_state.available_models.get(provider, {}).get("text", [])
            elif provider == "Replicate":
                # === NEW: Dynamic Model Registry Integration ===
                if agent == "Composer":
                     # Audio Models
                     options = get_model_options("audio")
                     model_list = [k for n, k in options] # Key names
                     # Add legacy fallback just in case
                     if "minimax/music-01" not in model_list: model_list.append("minimax/music-01")
                else:
                    # Default
                    model_list = ["minimax/music-01", "meta/musicgen", "Other Audio..."]
                
                existing_token = os.getenv("REPLICATE_API_TOKEN")
                if existing_token:
                    st.success("✅ Replicate Token found in .env")
                else:
                    st.warning("⚠️ Token missing from environment.")
                    tok = st.text_input("Enter Replicate Token", type="password", key="repl_tok")
                    if tok: os.environ["REPLICATE_API_TOKEN"] = tok
            else:
                model_list = []
            
            if not model_list:
                model_list = [saved_model] # Fallback
                
            try:
                mod_idx = model_list.index(saved_model)
            except ValueError:
                if saved_model not in model_list:
                    model_list.append(saved_model)
                mod_idx = model_list.index(saved_model)
            
            model = st.selectbox(f"Model ({agent})", model_list, index=mod_idx, key=f"mod_{agent}")
            
            # SHOW DYNAMIC PARAMS (If Replicate)
            if provider == "Replicate":
                cat = "audio" if agent == "Composer" else None
                if cat: 
                    info = get_model_info(cat, model)
                    if info and "inputs" in info:
                        st.caption(f"🔧 {info['name']} Options")
                        for inp in info["inputs"]:
                            # Render widget based on type
                            key_name = f"param_{agent}_{inp['name']}"
                            # Try to get saved value from extras
                            saved_val = current_conf.get(agent, {}).get(inp["name"], inp.get("default"))
                            
                            new_val = saved_val
                            if inp["type"] == "text":
                                new_val = st.text_input(inp["label"], value=saved_val, key=key_name)
                            elif inp["type"] == "textarea":
                                new_val = st.text_area(inp["label"], value=saved_val, key=key_name)
                            elif inp["type"] == "number":
                                new_val = st.number_input(inp["label"], value=saved_val, min_value=inp.get("min"), max_value=inp.get("max"), start_value=inp.get("default"), key=key_name)
                            elif inp["type"] == "select":
                                opts = inp.get("options", [])
                                idx = 0
                                if saved_val in opts: idx = opts.index(saved_val)
                                new_val = st.selectbox(inp["label"], opts, index=idx, key=key_name)
                            
                            # Update Extras
                            extras[inp["name"]] = new_val
                            if new_val != current_conf.get(agent, {}).get(inp["name"]): needs_save = True

            # 3. Extra Selectors for Cinematographer (Image/Video)
            extras = {}
            needs_save = False

            # Check basic Text Model changes
            if provider != saved_provider or model != saved_model:
                needs_save = True

            if agent == "Director":
                st.markdown("---")
                st.caption("🎬 Production Settings")
                
                # Shot Quota
                saved_shots = current_conf.get(agent, {}).get("max_shots", 2)
                shots_val = st.number_input("Max Shots per Scene (Quota)", min_value=1, max_value=10, value=saved_shots, step=1, key="dir_max_shots")
                extras["max_shots"] = shots_val
                if shots_val != saved_shots: needs_save = True
                
                # Video Duration defaults
                saved_dur = current_conf.get(agent, {}).get("duration", 5)
                # Durations often model dependent (Veo 3: 4s, 8s etc). We'll give generic int.
                dur_val = st.number_input("Clip Duration (Seconds)", min_value=1, max_value=60, value=saved_dur, step=1, key="dir_dur_sec")
                extras["duration"] = dur_val
                if dur_val != saved_dur: needs_save = True

            if agent == "Cinematographer":
                st.markdown("---")
                
                # --- Image Generation ---
                st.caption("🎨 Image Generation")
                saved_img_prov = current_conf.get(agent, {}).get("image_provider", "Google")
                saved_img_mod = current_conf.get(agent, {}).get("image_model", "imagen-3.0-generate-001")
                
                img_providers = ["Google", "Other"]
                img_provider_val = st.selectbox("Image Provider", img_providers, index=0 if saved_img_prov=="Google" else 1, key="cine_img_prov")
                
                img_models = st.session_state.available_models.get(img_provider_val, {}).get("image", ["imagen-3.0"])
                # Handle fallback logic
                if saved_img_mod not in img_models: img_models.append(saved_img_mod)
                img_model_val = st.selectbox("Image Model", img_models, index=img_models.index(saved_img_mod) if saved_img_mod in img_models else 0, key="cine_img_mod")

                # --- Video Generation ---
                st.caption("🎥 Video Generation")
                saved_vid_prov = current_conf.get(agent, {}).get("video_provider", "Google")
                saved_vid_mod = current_conf.get(agent, {}).get("video_model", "veo-2.0-generate-001")
                
                vid_providers = ["Google", "Replicate", "Other"]
                vid_provider_val = st.selectbox("Video Provider", vid_providers, index=0 if saved_vid_prov=="Google" else (1 if saved_vid_prov=="Replicate" else 2), key="cine_vid_prov")
                
                if vid_provider_val == "Replicate":
                    # Get from Registry
                    options = get_model_options("video")
                    vid_models = [k for n, k in options]
                else:
                    vid_models = st.session_state.available_models.get(vid_provider_val, {}).get("video", ["veo-2.0"])
                
                if saved_vid_mod not in vid_models: vid_models.append(saved_vid_mod)
                vid_model_val = st.selectbox("Video Model", vid_models, index=vid_models.index(saved_vid_mod) if saved_vid_mod in vid_models else 0, key="cine_vid_mod")

                # Replicate Video Extras
                if vid_provider_val == "Replicate":
                    info = get_model_info("video", vid_model_val)
                    if info and "inputs" in info:
                        st.caption(f"🔧 {info['name']} Options")
                        for inp in info["inputs"]:
                             # Don't show Prompt here as that comes from Agent logic usually, but we can allow override?
                             if inp["name"] == "prompt": continue 

                             key_name = f"param_vid_{inp['name']}"
                             saved_val = current_conf.get(agent, {}).get(inp["name"], inp.get("default"))
                             new_val = saved_val
                             
                             if inp["type"] == "text": new_val = st.text_input(inp["label"], value=saved_val, key=key_name)
                             elif inp["type"] == "number": new_val = st.number_input(inp["label"], value=saved_val, min_value=inp.get("min"), max_value=inp.get("max"), start_value=inp.get("default"), key=key_name)
                             
                             extras[inp["name"]] = new_val
                             if new_val != saved_val: needs_save = True

                # Populate Extras and Check for Changes
                extras["image_provider"] = img_provider_val
                extras["image_model"] = img_model_val
                extras["video_provider"] = vid_provider_val
                extras["video_model"] = vid_model_val

                if img_provider_val != saved_img_prov or img_model_val != saved_img_mod: needs_save = True
                if vid_provider_val != saved_vid_prov or vid_model_val != saved_vid_mod: needs_save = True

            
            if needs_save:
                config_manager.set_agent_config(agent, provider, model, **extras)
                st.toast(f"Saved {agent} Configuration")


# 3. History / Session
st.sidebar.divider()
st.sidebar.subheader("Time Travel")
mode = st.sidebar.radio("Mode", ["Live Operation", "Review History"])

session_id = None
if mode == "Review History":
    sessions = list_sessions()
    if sessions:
        selected_session = st.sidebar.selectbox("Select Past Directive", sessions)
        session_id = selected_session
    else:
        st.sidebar.warning("No history found.")

# Initialize Manager
if not "current_session_id" in st.session_state:
    st.session_state.current_session_id = None

manager = SessionManager(session_id if mode == "Review History" else st.session_state.current_session_id)
runner = AgentRunner(manager)

# --- MAIN INTERFACE ---
st.title("🤖 DeepAgents Orchestrator")

# Tabs for Agents
tabs = st.tabs([
    "🎬 Director (Creative)", 
    "🔎 Research (Truth)", 
    "⚖️ Confidence (Audit)",
    "🎥 Cinematographer (Vision)",
    "🎻 Composer (Audio)",
    "📡 Inter-Agent Comms",
    "🎨 Asset Gallery",
    "⚙️ Canons"
])
tab_director, tab_research, tab_confidence, tab_cinematographer, tab_composer, tab_comms, tab_properties, tab_settings = tabs

# --- TAB 1: DIRECTOR ---
with tab_director:
    st.header("Creative Direction")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        directive = st.text_area("Enter Commercial Concept / Directive", height=100)
    with col2:
        st.write("## ")
        run_btn = st.button("ACTION!", type="primary", use_container_width=True, disabled=(mode == "Review History"))
        # Cost Estimator
        if st.button("💰 Estimate Project", key="est_dir"):
            est = estimate_cost("Director", config_manager.config)
            st.toast(f"Total Project Est: ${est['total']:.2f}")
            with st.expander("Project Cost Breakdown", expanded=True):
                 for d in est['details']: st.write(f"- {d}")
        
        # Load run-time overrides from Config
        dir_conf = config_manager.get_agent_config("Director")
        shots_cfg = dir_conf.get("max_shots", 2)
        dur_cfg = dir_conf.get("duration", 5)
        st.caption(f"Settings: {shots_cfg} Shots, {dur_cfg}s clips")
    
    # Output Containter
    output_container = st.container()

    if run_btn and directive:
        # Create new session if needed
        st.session_state.current_session_id = SessionManager().session_id
        manager = SessionManager(st.session_state.current_session_id)
        # Re-init runner with manager
        runner = AgentRunner(manager)
        
        with output_container:
            st.info(f"Session started: {manager.session_id}")
            
            # --- PHASE 1: DIRECTION ---
            director_result = ""
            for agent, type_, content in runner.stream_director(directive): 
                if type_ == "thinking":
                    with st.expander(f"💭 {agent} Thinking...", expanded=False):
                        st.markdown(content)
                elif type_ == "output":
                     st.markdown(f"### 🎬 {agent} Output")
                     st.markdown(content)
                     director_result += content
                elif type_ == "error":
                    st.error(content)
            
            # --- PHASE 2: CINEMATOGRAPHY (AUTO-HANDOFF) ---
            if director_result:
                st.divider()
                st.info("🎬 Director > 🎥 Handoff to Cinematographer...")
                # We use the configured quotas
                for agent, type_, content in runner.run_cinematographer(
                    director_result, 
                    mode="both", # Default to both for full production
                    max_shots=shots_cfg, 
                    duration_sec=dur_cfg
                ): 
                    if type_ == "thinking":
                        with st.expander(f"💭 {agent} Thinking...", expanded=False):
                             st.markdown(content)
                    elif type_ == "output":
                         st.markdown(f"### 🎥 Visual Output")
                         st.markdown(content)
                    elif type_ == "error":
                         st.error(content)

    elif mode == "Review History" and session_id:
        # Replay Log
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Director":
                with output_container:
                    if log['type'] == 'thinking':
                        with st.expander(f"💭 Director Thinking ({log['timestamp']})"):
                            st.write(log['content'])
                    elif log['type'] == 'output':
                        st.markdown("### 🎬 Director Output")
                        st.markdown(log['content'])
    
    # --- SESSION ASSETS SECTION ---
    st.divider()
    st.subheader("📂 Session Assets")
    cur_sess = manager.session_id
    if cur_sess:
        sess_assets = asset_manager.list_assets(session_id=cur_sess)
        if sess_assets:
            acols = st.columns(4)
            for idx, asset in enumerate(sess_assets):
                with acols[idx % 4]:
                     st.caption(asset['asset_type'])
                     if asset['asset_type'] in ['image', 'storyboard']: st.image(asset['path'])
                     elif asset['asset_type'] == 'video': st.video(asset['path'])
                     elif asset['asset_type'] == 'audio': st.audio(asset['path'])
        else:
            st.caption("No assets generated yet in this session.")

if "research_input" not in st.session_state: st.session_state.research_input = ""

# --- TAB 2: RESEARCH ---
with tab_research:
    st.header("Research Agent")
    st.info("The Researcher verifies facts and finds references.")
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        res_topic = st.text_input("Research Topic", key="research_input")
    with col_r2:
        st.write("## ")
        run_res = st.button("🔎 Research", type="primary", use_container_width=True)
        
    res_container = st.container()
    
    if run_res and res_topic:
        with res_container:
            # We use the generic runner method for direct research
             for agent, type_, content in runner.run_research_direct(res_topic):
                 if type_ == "info": st.caption(content)
                 elif type_ == "output": st.markdown(content)

    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Researcher" and not run_res: # Avoid dupe if just ran
                with st.expander(f"📚 Research Report ({log['timestamp']})"):
                    st.markdown(log['content'])

if "confidence_input" not in st.session_state: st.session_state.confidence_input = ""

# --- TAB 3: CONFIDENCE ---
with tab_confidence:
    st.header("Confidence / Audit Agent")
    st.info("The Audit Agent critiques the plan for feasibility.")
    
    col_cf1, col_cf2 = st.columns([3, 1])
    with col_cf1:
         # Default to last Director output if available
         def_text = ""
         if session_id or st.session_state.current_session_id:
             logs = manager.load_history()
             for log in reversed(logs):
                 if log['agent'] == "Director" and log['type'] == "output":
                     def_text = log['content']
                     break
         
         audit_plan = st.text_area("Plan to Audit", value=def_text, height=150, key="confidence_input")
         
    with col_cf2:
        st.write("## ")
        run_audit = st.button("🛡️ Audit Plan", type="primary", use_container_width=True)
        
    audit_container = st.container()
    
    if run_audit and audit_plan:
        # We need to implement run_confidence_direct in runner if not exists, 
        # or just instantiate here. The user asked for "prompting form GUI".
        # Let's assume runner has it or we add it? 
        # Checking runner file... it has create_confidence_agent but maybe not a direct run method.
        # I'll implement a quick inline runner pattern for now.
        from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
        
        with audit_container:
            with st.spinner("Auditing..."):
                conf = config_manager.get_agent_config("Confidence")
                # Need model config
                # Mocking the agent creation
                c_agent = create_confidence_agent() # Default args
                # Confidence agent usually takes a plan string
                # We need to check its signature. Assuming it's a Runnable or similar.
                # In current codebase, it's usually a compiled graph or chain.
                # Let's try invoking it.
                try: 
                    # Assuming standard invoke
                     res = c_agent.invoke({"messages": [("user", f"Audit this plan: {audit_plan}")]})
                     # Extract output
                     if hasattr(res, "content"): out = res.content
                     elif isinstance(res, dict) and "messages" in res: out = res["messages"][-1].content
                     else: out = str(res)
                     
                     st.markdown("### 🛡️ Audit Report")
                     st.markdown(out)
                     # Log it
                     manager.log_event("Confidence", "output", out)
                except Exception as e:
                    st.error(f"Audit Failed: {e}")

    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Confidence" and not run_audit:
                st.markdown(f"### 🛡️ Audit Report ({log['timestamp']})")
                st.markdown(log['content'])

if "cinematographer_input" not in st.session_state: st.session_state.cinematographer_input = ""

# --- TAB 4: CINEMATOGRAPHER (New) ---
with tab_cinematographer:
    st.header("Cinematographer Agent")
    st.info("Translates the Director's vision into visual descriptions and video.")
    
    col_cm1, col_cm2 = st.columns([3, 1])
    with col_cm1:
        # Default to director output
        def_vis = ""
        if session_id or st.session_state.current_session_id:
             logs = manager.load_history()
             for log in reversed(logs):
                 if log['agent'] == "Director" and log['type'] == "output":
                     def_vis = log['content']
                     break
        
        vis_req = st.text_area("Scene Description", value=def_vis, height=150, key="cinematographer_input")
        
        # Local controls for manual run
        c1, c2, c3 = st.columns(3)
        with c1: 
             man_mode = st.selectbox("Mode", ["storyboard", "video", "both"], index=0, key="cine_man_mode")
        with c2:
             man_shots = st.number_input("Shots", 1, 10, 1, key="cine_man_shots")
        with c3:
             man_dur = st.number_input("Duration (s)", 1, 60, 5, key="cine_man_dur")

    with col_cm2:
        st.write("## ")
        run_cine = st.button("🎥 Action", type="primary", use_container_width=True)
        # Cost Estimator
        if st.button("💰 Estimate", key="est_cine"):
            # Mock config for estimate
            temp_conf = config_manager.config.copy()
            # Override with local manual inputs
            temp_conf["Cinematographer"]["max_shots"] = man_shots
            temp_conf["Cinematographer"]["duration"] = man_dur
            # Mode specific?
            # If mode is storyboard, cost is low. If video, calculate.
            # We assume cost calc assumes video generation if configured.
            est = estimate_cost("Cinematographer", temp_conf)
            st.toast(f"Total Est: ${est['total']:.2f}")
            with st.expander("Cost Breakdown", expanded=True):
                for d in est['details']: st.write(f"- {d}")
                if man_mode == "storyboard": st.warning("(Note: Estimates assume Video Generation)")

    cine_container = st.container()

    if run_cine and vis_req:
        with cine_container:
            # Use runner
            for agent, type_, content in runner.run_cinematographer(
                    vis_req, 
                    mode=man_mode, 
                    max_shots=man_shots, 
                    duration_sec=man_dur
                ): 
                    if type_ == "thinking":
                        with st.expander(f"💭 {agent} Thinking...", expanded=False):
                             st.markdown(content)
                    elif type_ == "output":
                         st.markdown(f"### 🎥 Visual Output")
                         st.markdown(content)
                    elif type_ == "error":
                         st.error(content)

    
    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        found_cinema = False
        for log in logs:
            if log['agent'] == "Cinematographer" and not run_cine:
                found_cinema = True
                with cine_container:
                    if log['type'] == 'output':
                        st.markdown(f"### 🎥 Visual Treatment ({log['timestamp']})")
                        st.markdown(log['content'])
        
        if not found_cinema and not run_cine:
            st.write("Waiting for Director's instructions...")

if "composer_input" not in st.session_state: st.session_state.composer_input = ""

# --- TAB: COMPOSER ---
with tab_composer:
    st.header("Composer Agent")
    st.info("Generates Musical Scores and ABC Notation.")
    
    # Check for Director's output to use as default context
    director_context = ""
    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        for log in reversed(logs):
            if log['agent'] == "Director" and log['type'] == 'output':
                director_context = log['content']
                break
    
    col_c1, col_c2 = st.columns([3, 1])
    with col_c1:
        # Allow manual editing, default to director context if available and input empty
        val_to_show = director_context if not st.session_state.composer_input else st.session_state.composer_input
        if not val_to_show and director_context: val_to_show = director_context
        
        comp_req = st.text_area("Composition Directive / Scene Context", value=val_to_show, height=100, key="composer_input")
    with col_c2:
        st.write("## ")
        compose_btn = st.button("🎵 Compose Score", type="primary", use_container_width=True)
        # Cost Estimator
        if st.button("💰 Estimate", key="est_comp"):
            est = estimate_cost("Composer", config_manager.config)
            st.toast(f"Total Est: ${est['total']:.2f}")
            with st.expander("Cost Breakdown", expanded=True):
                 for d in est['details']: st.write(f"- {d}")

    # Output
    comp_container = st.container()

    if compose_btn and comp_req:
        with comp_container:
            for agent, type_, content in runner.run_composer(comp_req):
                if type_ == "thinking":
                    st.caption(f"💭 {content}")
                elif type_ == "output":
                     st.markdown(f"### 🎻 Composition")
                     st.markdown(content)
                elif type_ == "error":
                    st.error(content)

    if session_id or st.session_state.current_session_id and not compose_btn:
        logs = manager.load_history()
        found_composer = False
        for log in logs:
            if log['agent'] == "Composer":
               with comp_container:
                    found_composer = True
                    if log['type'] == 'output':
                        st.markdown(f"### 🎻 Musical Composition ({log['timestamp']})")
                        st.markdown(log['content'])
        
        if not found_composer and not director_context:
            st.write("Waiting for Director's cue or manual input...")

# --- TAB: ASSET GALLERY ---
with tab_properties: 
    st.header("🎨 Global Asset Gallery")
    st.info("Browse all generated artifacts across all sessions.")
    
    filter_type = st.selectbox("Filter by Type", ["All", "Images", "Videos", "Audio"])
    type_map = {"Images": "image", "Videos": "video", "Audio": "audio"}
    t_filter = type_map.get(filter_type)
    
    all_assets = asset_manager.list_assets(asset_type=t_filter)
    
    if not all_assets:
        st.caption("No assets found.")
    else:
        # Grid Layout
        cols = st.columns(4)
        for idx, asset in enumerate(all_assets):
            with cols[idx % 4]:
                st.caption(f"{asset['timestamp']} | {asset['metadata'].get('model', 'Unknown')}")
                if asset['asset_type'] == 'image' or asset['asset_type'] == 'storyboard':
                    st.image(asset['path'], use_container_width=True)
                elif asset['asset_type'] == 'video':
                    st.video(asset['path'])
                elif asset['asset_type'] == 'audio':
                    st.audio(asset['path'])
                with st.expander("Details"):
                    st.json(asset)

# --- TAB: CANONS ---
with tab_settings:
    st.header("Agent Constitutions (Ontologies)")
    try:
        # Dynamically load ontologies
        ontologies = {
            "Director": "DeepAgents/Canon/Director_Ontology.md",
            "Research": "DeepAgents/Canon/Research_Agent_Ontology.md",
            "Cinematographer": "DeepAgents/Canon/Cinematographer_Ontology.md",
            "Confidence": "DeepAgents/Canon/Confidence_Agent_Ontology.md"
        }
        
        cols = st.columns(2)
        idx = 0
        for name, path in ontologies.items():
            content = "Not found"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            
            with cols[idx % 2]:
                with st.expander(f"📜 {name} Ontology"):
                    st.markdown(content)
            idx += 1
                
    except Exception as e:
        st.error(f"Could not load ontologies: {e}")

st.sidebar.text(f"Session: {manager.session_id}")
