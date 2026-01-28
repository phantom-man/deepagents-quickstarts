"""
GUI Agent Runner Module.
Provides the entry point and execution logic for running agents via the GUI.
"""

import asyncio
import contextlib
import io
import os
import queue
import sys

# pylint: disable=line-too-long, missing-module-docstring, import-error, wrong-import-position
# pylint: disable=no-name-in-module, missing-class-docstring, unused-argument, unused-variable
# pylint: disable=import-outside-toplevel, too-many-locals, broad-exception-caught
# pylint: disable=too-many-branches, too-many-statements, missing-function-docstring
# pylint: disable=broad-exception-raised

# Import Agents directly creates dependency issues if we not careful with paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.agent_brain import AgentComms, AgentConfig, AgentMemory
from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
    create_cinematographer_agent,
)
from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task

# NEW: Import The Studio Graph
from DeepAgents.graphs.agency_graph import app as studio_graph
from DeepAgents.persistence import get_postgres_checkpointer


class AgentRunner:
    def __init__(self, session_manager):
        self.session = session_manager
        self.config = AgentConfig()  # Load config
        self.brain = AgentMemory()  # Load memory for Composer

        # Init Neural Fabric Comms
        self.comms = AgentComms()
        self.comms.connect()

        # OTLP Configuration removed to favor standard LangChain Tracing (HTTP)
        # This prevents ConnectionRefusedError if no local OTLP collector is running.

    def stream_agency_graph(self, directive: str, agency_config: dict = None):
        """
        Runs the full LangGraph Studio Pipeline (Director->Research->Validation->Prod).
        Yields standard GUI events: (AgentName, Type, Content).
        Uses AgentComms polling for real-time progress updates.

        Args:
            directive: The creative directive from the user
            agency_config: Optional dict with agent configuration from GUI:
                - cinematographer: {active, model_id, params, storyboard_active, storyboard_model_id}
                - composer: {active, model_id, params, voice_source, voice_file, voice_model_id}
        """
        self.session.log_event(
            "System", "info", f"Starting Studio Graph for: {directive}"
        )

        import threading
        import time as time_module

        event_queue = queue.Queue()
        stop_polling = threading.Event()
        last_message_id = [0]  # Use list to allow modification in nested function

        # Get the start time to filter messages
        run_start_time = time_module.time()

        def poll_agent_comms():
            """Poll AgentComms database for new messages to update progress bar."""
            while not stop_polling.is_set():
                try:
                    if self.comms and self.comms.conn:
                        with self.comms.conn.cursor() as cur:
                            # Get messages newer than last seen AND from current session (timestamp filter)
                            # Only fetch messages created after this run started
                            from datetime import datetime

                            start_datetime = datetime.fromtimestamp(run_start_time)
                            cur.execute(
                                """SELECT id, sender, content, timestamp 
                                   FROM agent_messages 
                                   WHERE id > %s AND timestamp >= %s
                                   ORDER BY timestamp ASC, id ASC 
                                   LIMIT 10""",
                                (last_message_id[0], start_datetime),
                            )
                            rows = cur.fetchall()
                            for row in rows:
                                msg_id, sender, content, timestamp = row
                                last_message_id[0] = msg_id

                                # Map sender to GUI agent name
                                agent_map = {
                                    "Director": "Director",
                                    "Researcher": "Researcher",
                                    "Confidence": "Confidence",
                                    "Validator": "Confidence",
                                    "Cinematographer": "Cinematographer",
                                    "Composer": "Composer",
                                    "Editor": "Editor",
                                    "System": "System",
                                }
                                gui_name = agent_map.get(sender, sender)

                                # Only emit progress updates (not full content)
                                if content and len(content) < 200:
                                    event_queue.put((gui_name, "progress", content))
                except Exception:
                    pass  # Silently ignore polling errors

                time_module.sleep(0.5)  # Poll every 500ms

        async def run_loop():
            try:
                # Use Persistence
                async with get_postgres_checkpointer() as checkpointer:
                    # Note: Our studio_graph is pre-compiled. To use checkpointer,
                    # we should have compiled it with checkpointer.
                    # Re-compiling or using the global one if configured for Postgres.
                    # Current `agency_graph.py` uses MemorySaver or None by default.

                    # For now, we run it as is, or pass checkpointer if refactored.
                    # We will use the standard invoke for simplicity in this version,
                    # mapping graph events to UI events.

                    # Build configurable dict with agency settings
                    configurable = {
                        "thread_id": f"studio_{self.session.session_id}",
                        "require_validation": True,
                        "merge_output": True,
                    }

                    # Inject agency configuration from GUI
                    if agency_config:
                        # Cinematographer settings
                        cinema_cfg = agency_config.get("cinematographer", {})
                        configurable["cinematographer_active"] = cinema_cfg.get(
                            "active", True
                        )
                        configurable["cinematographer_model"] = cinema_cfg.get(
                            "model_id"
                        )
                        configurable["cinematographer_params"] = cinema_cfg.get(
                            "params", {}
                        )
                        configurable["cinematographer_source"] = cinema_cfg.get(
                            "source", "model"
                        )
                        configurable["cinematographer_files"] = cinema_cfg.get(
                            "file_paths", []
                        )
                        configurable["cinematographer_file_metadata"] = cinema_cfg.get(
                            "file_metadata", []
                        )
                        configurable["storyboard_active"] = cinema_cfg.get(
                            "storyboard_active", False
                        )
                        configurable["storyboard_model"] = cinema_cfg.get(
                            "storyboard_model_id"
                        )

                        # Composer settings
                        composer_cfg = agency_config.get("composer", {})
                        configurable["composer_active"] = composer_cfg.get(
                            "active", True
                        )
                        configurable["composer_model"] = composer_cfg.get("model_id")
                        configurable["composer_params"] = composer_cfg.get("params", {})
                        configurable["composer_source"] = composer_cfg.get(
                            "source", "model"
                        )
                        configurable["composer_files"] = composer_cfg.get(
                            "file_paths", []
                        )
                        configurable["composer_file_metadata"] = composer_cfg.get(
                            "file_metadata", []
                        )
                        configurable["composer_voice_source"] = composer_cfg.get(
                            "voice_source"
                        )
                        configurable["composer_voice_file"] = composer_cfg.get(
                            "voice_file"
                        )
                        configurable["composer_voice_model"] = composer_cfg.get(
                            "voice_model_id"
                        )

                    config = {
                        "configurable": configurable,
                        "tags": ["deep-agents-studio", "gui-triggered"],
                    }

                    # We use astream to get node outputs as they complete
                    # Track which nodes we've sent "starting" events for
                    started_nodes = set()

                    async for event in studio_graph.astream(
                        {"messages": [("user", directive)]},
                        config=config,
                    ):
                        # Event Format: {'node_name': {'key': val, ...}}
                        for node_name, state_update in event.items():
                            # Map Node -> GUI Agent Name
                            agent_map = {
                                "director": "Director",
                                "researcher": "Researcher",
                                "validator": "Confidence",
                                "cinematographer": "Cinematographer",
                                "composer": "Composer",
                                "editor": "Editor",
                            }
                            gui_name = agent_map.get(node_name, node_name.capitalize())

                            # FIX: Send "starting" event FIRST before any output
                            # This allows progress bar to update at the START of each agent
                            if node_name not in started_nodes:
                                started_nodes.add(node_name)
                                # Use "progress" type so it updates the bar immediately without adding to log
                                event_queue.put(
                                    (
                                        gui_name,
                                        "progress",
                                        f"Initializing {gui_name}...",
                                    )
                                )
                                event_queue.put(
                                    (
                                        gui_name,
                                        "info",
                                        f"Starting {gui_name} processing...",
                                    )
                                )

                            # Extract Content
                            # Our graph nodes return 'messages', 'director_plan', etc.

                            # 1. Look for AI Messages (Chat Output)
                            if "messages" in state_update:
                                msgs = state_update["messages"]
                                if msgs:
                                    last_msg = msgs[-1]
                                    if (
                                        hasattr(last_msg, "content")
                                        and last_msg.content
                                    ):
                                        content = last_msg.content
                                        event_queue.put((gui_name, "output", content))

                            # 2. Look for specific structured updates (Thinking/Status)
                            if "validation_status" in state_update:
                                status = state_update["validation_status"]
                                event_queue.put(
                                    (
                                        gui_name,
                                        "output",
                                        f"**Validation Status**: {status}",
                                    )
                                )

                            if "final_output" in state_update:
                                path = state_update["final_output"]
                                event_queue.put(
                                    (gui_name, "output", f"**FINAL MERGE**: {path}")
                                )

            except Exception as e:
                import traceback

                event_queue.put(
                    (
                        "System",
                        "error",
                        f"Graph Error: {str(e)}\n{traceback.format_exc()}",
                    )
                )
            finally:
                event_queue.put(None)

        # Sync-to-Async Bridge
        try:
            # Win32 Policy fix
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            def start_loop():
                try:
                    asyncio.run(run_loop())
                except Exception as ex:
                    event_queue.put(("System", "error", f"Async Thread Error: {ex}"))
                    event_queue.put(None)

            # Start the polling thread for AgentComms
            poll_thread = threading.Thread(target=poll_agent_comms, daemon=True)
            poll_thread.start()

            thread = threading.Thread(target=start_loop)
            thread.start()

            # Consumer
            while True:
                try:
                    # Use timeout to allow checking for progress events more frequently
                    item = event_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if item is None:
                    break

                agent_name, evt_type, content = item

                # Log events (skip progress events to avoid spam)
                # NOTE: Don't broadcast via send_message here - _emit_progress in agency_graph.py already does it
                # Double-emitting causes duplicate messages in the UI
                if evt_type != "progress":
                    self.session.log_event(agent_name, evt_type, content)

                yield item

            # Stop polling thread
            stop_polling.set()

        except Exception as e:
            stop_polling.set()
            yield ("System", "error", str(e))

    async def _run_agent_async(self, agent_factory, inputs, config):
        """Helper to run agents async with persistence."""
        async with get_postgres_checkpointer() as checkpointer:
            # Re-compile the agent with the checkpointer
            # This is tricky because create_director_agent returns a compiled graph usually.
            # We might need to refactor create_director_agent to accept checkpointer,
            # OR we need to attach it here if possible (LangGraph usually requires it at compile time).

            # Fortunately, we updated create_director_agent to accept checkpointer!
            # But here `agent_factory` is a function call.
            pass

    def stream_director(self, directive):
        """Runs director and streams events to the session log."""

        # Load Config for Director
        dir_conf = self.config.get_agent_config("Director")
        provider = dir_conf["provider"]
        model = dir_conf["model"]

        self.session.log_event(
            "Director",
            "info",
            f"Starting directive: {directive} (Provider: {provider}, Model: {model})",
        )

        # ASYNC WRAPPER FOR GUI
        # Streamlit is synchronous, but our new architecture is Async.
        # We process events in a separate thread/loop and yield them via a Queue to allow usage of generators in UI.
        import threading

        event_queue = queue.Queue()

        async def run_loop():
            try:
                # Use Persistence
                async with get_postgres_checkpointer() as checkpointer:
                    agent = create_director_agent(
                        provider=provider, model_name=model, checkpointer=checkpointer
                    )

                    # LangSmith Tracing Context
                    tags = ["deep-agents-system", "gui-triggered", "agent:director"]
                    metadata = {
                        "session_id": self.session.session_id,
                        "model_name": model,
                        "provider": provider,
                        "user_intent": "director_directive",
                    }

                    config = {
                        "configurable": {"thread_id": f"gui_{self.session.session_id}"},
                        "tags": tags,
                        "metadata": metadata,
                    }

                    async for event in agent.astream(
                        {"messages": [("user", directive)]},
                        config=config,  # type: ignore
                    ):
                        # Parsing Logic
                        # Check if event is the raw messages dict (SimpleReActExecutor case)
                        if "messages" in event and isinstance(event["messages"], list):
                            msgs = event["messages"]
                            msg = msgs[-1]

                            # Ensure we only capture AI output, not input echoes
                            is_ai = False
                            if hasattr(msg, "type") and msg.type == "ai":
                                is_ai = True
                            elif (
                                hasattr(msg, "__class__")
                                and "AIMessage" in msg.__class__.__name__
                            ):
                                is_ai = True

                            if is_ai and hasattr(msg, "content") and msg.content:
                                # Handle Anthropic List Content
                                content = msg.content
                                if isinstance(content, list):
                                    # Extract text blocks
                                    text_parts = [
                                        c.get("text", "")
                                        for c in content
                                        if isinstance(c, dict)
                                        and c.get("type") == "text"
                                    ]
                                    content = "\n".join(text_parts)

                                event_queue.put(("Director", "output", content))

                        else:
                            # LangGraph case: {"node": {"messages": ...}}
                            for key in event:
                                val = event[key]
                                msgs = []

                                if isinstance(val, dict) and "messages" in val:
                                    msgs = val["messages"]
                                    if hasattr(msgs, "value"):
                                        msgs = msgs.value
                                elif hasattr(val, "messages"):
                                    msgs = getattr(val, "messages", [])

                                if msgs and isinstance(msgs, list):
                                    msg = msgs[-1]

                                    # Ensure we only capture AI output
                                    is_ai = False
                                    if hasattr(msg, "type") and msg.type == "ai":
                                        is_ai = True
                                    elif (
                                        hasattr(msg, "__class__")
                                        and "AIMessage" in msg.__class__.__name__
                                    ):
                                        is_ai = True

                                    if (
                                        is_ai
                                        and hasattr(msg, "content")
                                        and msg.content
                                    ):
                                        # Handle Anthropic List Content
                                        content = msg.content
                                        if isinstance(content, list):
                                            # Extract text blocks
                                            text_parts = [
                                                c.get("text", "")
                                                for c in content
                                                if isinstance(c, dict)
                                                and c.get("type") == "text"
                                            ]
                                            content = "\n".join(text_parts)

                                        event_queue.put(("Director", "output", content))

                                    if (
                                        is_ai
                                        and hasattr(msg, "tool_calls")
                                        and msg.tool_calls
                                    ):
                                        for tc in msg.tool_calls:
                                            log_entry = f"Calling Tool: {tc['name']} with args {tc['args']}"
                                            event_queue.put(
                                                ("Director", "thinking", log_entry)
                                            )

            except Exception as e:
                event_queue.put(("Director", "error", str(e)))
            finally:
                event_queue.put(None)  # Sentinel

        # Create Sync-to-Async Bridge with Threading
        try:
            # Win32 Policy fix for Streamlit
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            # Run asyncio loop in a separate thread
            def start_loop():
                try:
                    asyncio.run(run_loop())
                except Exception as ex:
                    event_queue.put(("Director", "error", f"Async Thread Error: {ex}"))
                    event_queue.put(None)

            thread = threading.Thread(target=start_loop)
            thread.start()

            # Consume queue in main thread and yield
            while True:
                item = event_queue.get()
                if item is None:
                    break

                agent_name, evt_type, content = item

                # Broadcast to Neural Fabric (Comms Tab)
                if evt_type == "output":
                    self.comms.send_message(
                        agent_name, "All", f"Global Update: {content[:100]}..."
                    )
                elif evt_type == "thinking" and "Calling Tool" in content:
                    self.comms.send_message(agent_name, "System", f"Action: {content}")

                # Log and Yield
                if evt_type == "output":
                    self.session.log_event("Director", "output", content)
                elif evt_type == "thinking":
                    self.session.log_event("Director", "thinking", content)
                elif evt_type == "error":
                    self.session.log_event("Director", "error", content)

                yield item

                # Optional: Join thread if done, but queue sentinel is enough

        except Exception as e:
            self.session.log_event("Director", "error", f"Async Loop Failed: {e}")
            yield ("Director", "error", f"System Error: {e}")

    # Legacy Sync Method (kept for reference, but shadowed by above logic)
    def _stream_director_sync(self, directive):
        pass

    def run_research_direct(self, topic):
        """Runs the research agent directly (not via Director)."""
        # Load Config for Researcher
        res_conf = self.config.get_agent_config("Researcher")
        # Research agent factory likely doesn't support provider yet, so we default to what keys allow
        # Ideally we update run_research_task to accept model too, but avoiding deep refactor of Researcher for now unless requested.

        # Defensive config loading
        model = res_conf.get("model", "claude-3-haiku-20240307")
        self.session.log_event(
            "Researcher", "info", f"Starting research on: {topic} (Model: {model})"
        )
        yield ("Researcher", "info", f"Starting research on: {topic} (Model: {model})")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            tags = ["deep-agents-system", "gui-triggered", "agent:researcher"]
            metadata = {
                "session_id": self.session.session_id,
                "model_name": model,
                "user_intent": "research_direct",
            }
            extra_config = {"tags": tags, "metadata": metadata}

            # Assuming run_research_task accepts model_name
            res = run_research_task(topic, extra_config=extra_config, model_name=model)

        output = f.getvalue()

        # Deduplication Strategy:
        # run_research_task often prints its final result to stdout AND returns it.
        # This causes the 'double output' issue in the GUI.
        # We check if the returned 'res' is effectively contained in the captured 'output'.
        # If 'res' is just a string summary, we log it.
        # But if 'output' is the full report, we prefer that.

        if output:
            # Clean ANSI codes if any (though StringIO usually clean)
            self.session.log_event("Researcher", "output", output)
            yield ("Researcher", "output", output)

        # Only yield 'res' if it's substantially different or output was empty
        # and 'res' is not None/Empty
        if res and str(res).strip() not in output:
            self.session.log_event("Researcher", "output", str(res))
            yield ("Researcher", "output", str(res))

    def run_confidence_task(self, content):
        """Runs the confidence audit agent."""
        from DeepAgents.CommercialAgents.confidence_agent.agent import (
            run_confidence_audit,
        )

        conf = self.config.get_agent_config("Confidence")
        self.session.log_event("Confidence", "info", "Starting Audit...")
        yield ("Confidence", "thinking", "Auditing content for accuracy and safety...")

        # Capture Stdout again?
        # Confidence agent prints a lot, but returns final string.
        # We can just run it.
        try:
            # Just run synchronously for now as it's a simple chain usually,
            # though it calls research internally.
            # Ideally we run in thread if it blocks for long.
            res = run_confidence_audit(content)
            if res:
                self.session.log_event("Confidence", "output", res)
                yield ("Confidence", "output", res)
            else:
                yield ("Confidence", "error", "No report generated.")
        except Exception as e:
            yield ("Confidence", "error", str(e))

    def run_composer(self, director_output):
        """Runs the composer agent."""
        if not director_output:
            yield ("Composer", "error", "No context to compose for.")
            return

        conf = self.config.get_agent_config("Composer")
        self.session.log_event(
            "Composer", "info", f"Composing Score... (Model: {conf['model']})"
        )
        yield (
            "Composer",
            "thinking",
            "Analyzing Director's Vision and checking Memory for musical motifs...",
        )

        try:
            agent_func = create_composer_agent(
                model_config=conf, brain=self.brain, session_id=self.session.session_id
            )
            if not agent_func:
                raise Exception("Failed to init Composer Agent")

            # Run
            # LangGraph / Runnable Support: .invoke vs direct call
            if hasattr(agent_func, "invoke"):
                # LangGraph compiled state graph needs a dict input usually
                res = agent_func.invoke({"messages": [("user", director_output)]})
                # Output parsing: usually in keys "messages" or just str if it's a simple chain
                if isinstance(res, dict) and "messages" in res:
                    result = res["messages"][-1].content
                else:
                    result = str(res)
            else:
                # Standard function
                result = agent_func(director_output)

            # Comms Update
            self.comms.send_message("Composer", "Director", "Soundtrack Complete.")

            self.session.log_event("Composer", "output", result)
            yield ("Composer", "output", result)

        except Exception as e:
            self.session.log_event("Composer", "error", str(e))
            yield ("Composer", "error", str(e))

    def run_editor_merge(self, session_id, audio_override=None):
        """Merges all video and audio assets from the session."""
        from DeepAgents.asset_manager import AssetManager
        from DeepAgents.editor_tools import merge_video_audio

        am = AssetManager()
        # Force refresh of assets might be needed if FS is slow?
        # Usually list_assets hits the DB or FS directly.
        assets = am.list_assets(session_id)

        # Filter Assets
        # Ensure we filter for THIS specific run's assets if possible,
        # or just ALL assets for this session ID.
        videos = [a["path"] for a in assets if a["asset_type"] == "video"]
        audio_assets = [a["path"] for a in assets if a["asset_type"] == "audio"]

        if not videos:
            print("Editor: No video clips found to merge.")
            return None

        # Audio Selection Strategy
        # 1. Use Override (Composer's latest output)
        # 2. Use first audio asset found
        # 3. Silent
        best_audio = "SILENT"
        if audio_override and os.path.exists(audio_override):
            best_audio = audio_override
        elif audio_assets:
            best_audio = audio_assets[0]

        # Sort videos ensuring consistent order (e.g. by filename or DB timestamp)
        videos.sort()

        print(f"Editor: Merging {len(videos)} clips with audio: {best_audio}")

        try:
            merged_path = merge_video_audio.invoke(
                {
                    "video_paths": videos,
                    "audio_path": best_audio,
                    "output_name": f"Final_Cut_{session_id}.mp4",
                }
            )
            if "Error" in merged_path:
                print(f"Editor Error: {merged_path}")
                return None
            return merged_path
        except Exception as e:
            print(f"Merge Failed: {e}")
            return None

    def run_cinematographer(
        self,
        director_output,
        mode="both",
        max_shots=None,
        duration_sec=None,
        resume_history=None,
        user_feedback=None,
    ):
        if not director_output and not resume_history:
            yield ("Cinematographer", "error", "No context to visualize.")
            return

        conf = self.config.get_agent_config("Cinematographer")
        self.session.log_event(
            "Cinematographer",
            "info",
            f"Visualizing Scene... (Modes: {mode}, Shots: {max_shots})",
        )
        yield (
            "Cinematographer",
            "thinking",
            f"Translating textual vision into visual prompts and assets ({max_shots} shots)...",
        )

        try:
            # Create Generator directly (Sync wrapper)
            # Ensure we pass the session_id correcty
            agent_gen_func = create_cinematographer_agent(
                model_config=conf, brain=self.brain, session_id=self.session.session_id
            )

            # Comms Check-in
            self.comms.send_message(
                "Cinematographer",
                "Director",
                "Received script. Beginning visualization.",
            )

            # Execute Generator
            # Note: run_agent signature updated to accept resume_history/user_feedback
            gen = agent_gen_func(
                director_output,
                mode=mode,
                max_shots=max_shots,
                duration_sec=duration_sec,
                resume_history=resume_history,
                user_feedback=user_feedback,
            )

            for event_type, payload in gen:
                # payload might be tuple or string
                # Map to Runner format: (AgentName, Type, Content)

                if event_type == "review_required":
                    # Payload is the asset path/string
                    yield ("Cinematographer", "review_required", payload)
                elif event_type == "state_dump":
                    # Payload is the messages list
                    yield ("Cinematographer", "state_dump", payload)
                elif event_type == "output":
                    self.session.log_event("Cinematographer", "output", payload)
                    yield ("Cinematographer", "output", payload)
                elif event_type == "thinking":
                    yield ("Cinematographer", "thinking", payload)
                elif event_type == "error":
                    self.session.log_event("Cinematographer", "error", payload)
                    yield ("Cinematographer", "error", payload)
                else:
                    # 'done' etc
                    yield ("Cinematographer", event_type, payload)

        except Exception as e:
            self.session.log_event("Cinematographer", "error", str(e))
            yield ("Cinematographer", "error", str(e))
        # Similar to Director, Cinematographer likely uses async calls or heavy I/O (Replicate polling).
        import threading

        cine_queue = queue.Queue()

        # async def cine_loop():
        #     try:
        #         # Assuming Cinematographer uses sync HTTP calls mostly (requests lib in agent.py)
        #         # But creating agent might need async context if it touches DB/Brain
        #         # However, run_agent in Cinematographer is decorated with @traceable and is synchronous def run_agent
        #         # EXCEPT: We want to stream partial results if possible. Currently it returns a big string report.
        #         # To support "streaming" updates like "Generated Image 1...", we need to modify the agent to yield
        #         # or we just run it in thread and return final.
        #
        #         # Given current agent.py structure (it returns a string report), we can't easily stream *internal* progress
        #         # without refactoring the agent. For now, let's just offload the blocking call from the main GUI thread.
        #
        #         agent_func = create_cinematographer_agent(
        #             model_config=conf,
        #             brain=self.brain,
        #             session_id=self.session.session_id,
        #         )
        #         if not agent_func:
        #             raise Exception("Failed to init Cinematographer Agent")
        #
        #         # Run (Blocking)
        #         # NOTE: The user noted "cinematographer only produced two images" despite 3 shots requested.
        #         # The GUI passes max_shots to this function.
        #         result = agent_func(
        #             director_output,
        #             mode=mode,
        #             max_shots=max_shots,
        #             duration_sec=duration_sec,
        #         )
        #
        #         cine_queue.put(("Cinematographer", "output", result))
        #
        #     except Exception as e:
        #         cine_queue.put(("Cinematographer", "error", str(e)))
        #     finally:
        #         cine_queue.put(None)

        # Threading Bridge
        try:
            # thread = threading.Thread(
            #     target=lambda: (
            #         asyncio.run(cine_loop())
            #         if sys.platform == "win32"
            #         else asyncio.run(cine_loop())
            #     )
            # )
            # Note: asyncio.run might fail if loop already running in this thread?
            # Streamlit runs script in a specific way.
            # Actually, because `agent_func` is synchronous logic wrapped in async def here,
            # we can just run it in a normal thread without asyncio IF `create_cinematographer_agent` is sync.
            # Checking agent.py ... `create_cinematographer_agent` is sync. `run_agent` is sync.
            # So we don't need asyncio for Cinematographer unless we want to use async DB checkpointer.

            # SIMPLER THREADING FOR SYNC AGENT
            def sync_cine_worker():
                try:
                    agent_func = create_cinematographer_agent(
                        model_config=conf,
                        brain=self.brain,
                        session_id=self.session.session_id,
                    )
                    # Get generator reference
                    generator = agent_func(
                        director_output,
                        mode=mode,
                        max_shots=max_shots,
                        duration_sec=duration_sec,
                    )

                    # Iterate and convert
                    for item in generator:
                        # Agent yields ("type", "content")
                        if item[0] == "thinking":
                            cine_queue.put(("Cinematographer", "thinking", item[1]))
                        elif item[0] == "output":
                            cine_queue.put(("Cinematographer", "output", item[1]))
                        elif item[0] == "done":
                            # We can log done or just finish
                            pass
                        elif item[0] == "error":
                            cine_queue.put(("Cinematographer", "error", item[1]))

                except Exception as e:
                    cine_queue.put(("Cinematographer", "error", str(e)))
                finally:
                    cine_queue.put(None)

            t = threading.Thread(target=sync_cine_worker)
            t.start()

            while True:
                item = cine_queue.get()
                if item is None:
                    break

                if item[1] == "output":
                    self.session.log_event("Cinematographer", "output", item[2])
                elif item[1] == "error":
                    self.session.log_event("Cinematographer", "error", item[2])

                yield item

        except Exception as e:
            self.session.log_event("Cinematographer", "error", f"Thread Failed: {e}")
            yield ("Cinematographer", "error", str(e))
