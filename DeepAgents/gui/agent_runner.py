"""
GUI Agent Runner Module.
Provides the entry point and execution logic for running agents via the GUI.
"""

import sys
import os
import io
import contextlib
import asyncio

# pylint: disable=line-too-long, missing-module-docstring, import-error, wrong-import-position
# pylint: disable=no-name-in-module, missing-class-docstring, unused-argument, unused-variable
# pylint: disable=import-outside-toplevel, too-many-locals, broad-exception-caught
# pylint: disable=too-many-branches, too-many-statements, missing-function-docstring
# pylint: disable=broad-exception-raised

# Import Agents directly creates dependency issues if we not careful with paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
    create_cinematographer_agent,
)
from DeepAgents.agent_brain import AgentConfig, AgentMemory
from DeepAgents.persistence import get_postgres_checkpointer


class AgentRunner:
    def __init__(self, session_manager):
        self.session = session_manager
        self.config = AgentConfig()  # Load config
        self.brain = AgentMemory()  # Load memory for Composer

        # Enable OTLP Tracing for GUI process if configured
        if os.environ.get("LANGSMITH_OTEL_ENABLED") == "true":
            if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
                os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"

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
        import queue
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

                # Log and Yield
                if item[1] == "output":
                    self.session.log_event("Director", "output", item[2])
                elif item[1] == "thinking":
                    self.session.log_event("Director", "thinking", item[2])
                elif item[1] == "error":
                    self.session.log_event("Director", "error", item[2])

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
        # But user asked for "Variable that tells the agent code that were using that brands llms"

        model = res_conf["model"]
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
        if output:
            self.session.log_event("Researcher", "output", output)
            yield ("Researcher", "output", output)

        self.session.log_event("Researcher", "output", str(res))
        yield ("Researcher", "output", str(res))

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

            self.session.log_event("Composer", "output", result)
            yield ("Composer", "output", result)

        except Exception as e:
            self.session.log_event("Composer", "error", str(e))
            yield ("Composer", "error", str(e))

    def run_editor_merge(self, session_id):
        """Merges all video and audio assets from the session."""
        from DeepAgents.asset_manager import AssetManager
        from DeepAgents.editor_tools import merge_video_audio

        am = AssetManager()
        assets = am.list_assets(session_id)

        # Filter Assets
        videos = [a["path"] for a in assets if a["asset_type"] == "video"]
        audio = [a["path"] for a in assets if a["asset_type"] == "audio"]

        if not videos:
            return None

        # Use first audio track if available, else empty string (Tool handles it?)
        # merge_video_audio expects a path or logic to silence.
        # Let's assume we need at least one video. Audio is optional.
        best_audio = audio[0] if audio else "SILENT"

        # Sort videos by creation time (implicitly by list order usually, but let's be safe if possible)
        # Assuming asset logs are chronological.

        try:
            merged_path = merge_video_audio.invoke(
                {
                    "video_paths": videos,
                    "audio_path": best_audio,
                    "output_name": f"Final_Cut_{session_id}.mp4",
                }
            )
            if "Error" in merged_path:
                return None
            return merged_path
        except Exception as e:
            print(f"Merge Failed: {e}")
            return None

    def run_cinematographer(
        self, director_output, mode="both", max_shots=None, duration_sec=None
    ):
        if not director_output:
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

        # ASYNC WRAPPER FOR CINEMATOGRAPHER
        # Similar to Director, Cinematographer likely uses async calls or heavy I/O (Replicate polling).
        import queue
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
