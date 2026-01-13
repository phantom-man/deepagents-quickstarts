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
from DeepAgents.agent_brain import AgentConfig
from DeepAgents.asset_manager import AssetManager
from DeepAgents.cost_calculator import estimate_cost

# Initialize Config
@st.cache_resource
def get_config_manager():
    return AgentConfig()

@st.cache_resource
def get_asset_manager():
    return AssetManager()

config_manager = get_config_manager()
asset_manager = get_asset_manager()

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
    .status-box {
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .status-ok { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .status-err { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .stButton button:disabled {
        background-color: #cccccc;
        color: #666666;
    }
</style>
""", unsafe_allow_html=True)

# --- AUTO-INITIALIZATION ---
if "diagnostics" not in st.session_state:
    st.session_state.diagnostics = run_diagnostics()

# Check global health
critical_systems = ["Internet", "GCP (LLM)", "Postgres (Nervous System)", "LanceDB (Memory)"]
system_health = True
failed_systems = []

# --- TOP DASHBOARD ---
st.title("🤖 DeepAgents Orchestrator")

with st.expander("🔌 System Status Board", expanded=True):
    # Dynamic Columns for Status
    diag_results = st.session_state.diagnostics
    cols = st.columns(len(diag_results))
    
    for idx, (sys_name, res) in enumerate(diag_results.items()):
        is_ok = res["status"]
        if sys_name in critical_systems and not is_ok:
            system_health = False
            failed_systems.append(sys_name)
            
        with cols[idx]:
            indicator = "🟢" if is_ok else "🔴"
            st.markdown(f"**{sys_name}**")
            st.markdown(f"### {indicator}")
            if not is_ok:
                st.caption(f"Error: {res['message']}")
            else:
                st.caption("Online")

    # Retry Logic
    st.divider()
    r_col1, r_col2 = st.columns([1, 4])
    with r_col1:
        # Retry Button: Disabled if everything is green
        retry_disabled = (len(failed_systems) == 0)
        if st.button("🔄 Re-Initialize System", disabled=retry_disabled, type="primary" if not retry_disabled else "secondary"):
            st.session_state.diagnostics = run_diagnostics()
            st.rerun()
    with r_col2:
        if not retry_disabled:
            st.warning("⚠️ Failures Detected. Fix issues and press Re-Initialize.")
        else:
            st.success("✅ All Systems Operational. Dashboard Unlocked.")

# --- SIDEBAR: CONFIGURATION ---
st.sidebar.title("🎛️ Control Center")

# History / Session
st.sidebar.subheader("Time Travel")
mode = st.sidebar.radio("Mode", ["Live Operation", "Review History"], disabled=not system_health)

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

# Configuration Selectors
st.sidebar.divider()
st.sidebar.subheader("System Configuration")
if not system_health:
    st.sidebar.error("🔒 Configuration Locked (System Check Failed)")
else:
    from DeepAgents.system_config import SystemConfiguration
    sys_config = SystemConfiguration().load_config()
    st.sidebar.info(f"✅ Loaded from LangSmith (Ver: {sys_config.get('version', 'Unknown')})")
    
    with st.sidebar.expander("Active Configuration Matrix"):
        st.json(sys_config)
    
    st.sidebar.caption("To modify capabilities or priorities, update 'deepagents-system-config' in LangSmith Hub.")

# --- MAIN INTERFACE (GATED) ---
if not system_health:
    st.error("🛑 System Lockdown Active. Please resolve diagnostic failures to proceed.")
    st.info(f"Critical Failures: {', '.join(failed_systems)}")
    st.stop() # HALT RENDERING HERE

# --- ABSOLUTELY ESSENTIAL: TABS RENDER ONLY IF HEALTHY ---

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
            st.toast(f"Total Project Est: ${est.get('total_max', 0.0):.2f}")
            with st.expander("Project Cost Breakdown", expanded=True):
                 for d in est['details']: st.write(f"- {d}")
        
        st.info("ℹ️ Director Mode: Autonomous. Results depend on your prompt.")
    
    # Output Containter
    output_container = st.container()

    if run_btn and directive:
        # Create new session if needed
        if not session_id or session_id == "New Session":
             if manager:
                session_id = manager.create_session("New Director Run")
                st.session_state.current_session_id = session_id
                st.rerun()
             else:
                session_id = str(int(time.time()))

    # Session State Persistence for Results
    if "director_result" not in st.session_state:
        st.session_state.director_result = ""
    if "final_asset_path" not in st.session_state:
        st.session_state.final_asset_path = None
    if "agent_logs" not in st.session_state:
        st.session_state.agent_logs = []

    if run_btn and directive:
        # Clear previous logs
        st.session_state.agent_logs = []
        st.session_state.director_result = ""
        st.session_state.final_asset_path = None
        
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
                # Log to state
                st.session_state.agent_logs.append({"agent": agent, "type": type_, "content": content})
                
                if type_ == "thinking":
                    with st.expander(f"💭 {agent} Thinking...", expanded=False):
                        st.markdown(content)
                elif type_ == "output":
                     st.markdown(f"### 🎬 {agent} Output")
                     st.markdown(content)
                     director_result += content
                elif type_ == "error":
                    st.error(content)
            
            st.session_state.director_result = director_result

            # --- PHASE 2: CINEMATOGRAPHY (AUTO-HANDOFF) ---
            if director_result:
                st.divider()
                st.info("🎬 Director > 🎥 Handoff to Cinematographer...")
                # Autonomous mode: Agent decides shots/duration based on prompt or defaults
                # We pass defaults to ensure safety, but Agent is autonomous
                for agent, type_, content in runner.run_cinematographer(
                    director_result, 
                    mode="storyboard",  # Default mode
                    max_shots=1,        # Logic moved to agent, but runner needs valid int
                    duration_sec=4
                ): 
                    st.session_state.agent_logs.append({"agent": agent, "type": type_, "content": content})
                    if type_ == "thinking":
                        with st.expander(f"💭 {agent} Thinking...", expanded=False):
                             st.markdown(content)
                    elif type_ == "output":
                         st.markdown(f"### 🎥 Visual Output")
                         st.markdown(content)
                    elif type_ == "error":
                         st.error(content)

                # --- PHASE 3: COMPOSER (AUTO-HANDOFF) ---
                st.divider()
                st.info("🎬 Director > 🎻 Handoff to Composer...")
                for agent, type_, content in runner.run_composer(director_result): 
                    st.session_state.agent_logs.append({"agent": agent, "type": type_, "content": content})
                    if type_ == "thinking":
                        with st.expander(f"💭 {agent} Thinking...", expanded=False):
                             st.markdown(content)
                    elif type_ == "output":
                         st.markdown(f"### 🎻 Audio Output")
                         st.markdown(content)
                    elif type_ == "error":
                         st.error(content)

                # --- PHASE 4: EDITING (MERGE) ---
                st.divider()
                st.info("✂️ Bringing it all together (Merging)...")
                # Automatically attempt merge
                merge_result = runner.run_editor_merge(manager.session_id)
                if merge_result:
                     st.success(f"🎬 FINAL CUT COMPLETE!")
                     st.video(merge_result)
                     st.markdown(f"**Path**: `{merge_result}`")
                     st.session_state.final_asset_path = merge_result
                else:
                     st.warning("Could not merge assets (Missing video or audio?)")
    
    # RENDER PERSISTED RESULTS (If not running now, but have results)
    elif st.session_state.get("agent_logs") and mode == "Live Operation":
        with output_container:
            for log in st.session_state.agent_logs:
                agent, type_, content = log['agent'], log['type'], log['content']
                if type_ == "thinking":
                    with st.expander(f"💭 {agent} Thinking...", expanded=False):
                        st.markdown(content)
                elif type_ == "output":
                     st.markdown(f"### {agent} Output")
                     st.markdown(content)
                elif type_ == "error":
                    st.error(content)
            
            if st.session_state.get("final_asset_path"):
                st.divider()
                st.success(f"🎬 FINAL CUT COMPLETE!")
                st.video(st.session_state.final_asset_path)
                st.markdown(f"**Path**: `{st.session_state.final_asset_path}`")

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
        
        # MERGE BUTTON FOR HISTORICAL CONTEXT
        st.divider()
        if st.button("✂️ Merge Session Assets"):
             with output_container:
                 st.info(f"Starting Manual Merge for Session: {session_id}...")
                 merge_result = runner.run_editor_merge(session_id)
                 if merge_result:
                     st.success(f"🎬 FINAL CUT COMPLETE!")
                     st.video(merge_result)
                     st.markdown(f"**Path**: `{merge_result}`")
                 else:
                     st.error("Could not merge assets (Missing video or audio?)")
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
