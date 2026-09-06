"""
Regression: AgentRunner.run_cinematographer must create and drive the cinematographer
agent EXACTLY ONCE per call.

Finding (colibri review 2026-09-05, .colibri_reviews/DeepAgents__gui__agent_runner.py__bug__11752ad4.md,
HIGH): the method ran the agent synchronously, yielded its events, and then unconditionally ran a
SECOND copy of the agent in a worker thread and yielded those events too - every call
double-spent the paid generation and double-logged the session.

The test drives the real method with a counting stub in place of create_cinematographer_agent and
a minimal session/config/comms so no model, database or network is touched.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import DeepAgents.gui.agent_runner as agent_runner_module  # noqa: E402


class _Session:
    session_id = "test-session"

    def __init__(self):
        self.events = []

    def log_event(self, agent, kind, content):
        self.events.append((agent, kind, content))


class _Config:
    def get_agent_config(self, name):
        return {"model": "stub-model"}


class _Comms:
    def __init__(self):
        self.sent = []

    def send_message(self, sender, recipient, content):
        self.sent.append((sender, recipient, content))


def _runner_without_init():
    runner = agent_runner_module.AgentRunner.__new__(agent_runner_module.AgentRunner)
    runner.session = _Session()
    runner.config = _Config()
    runner.brain = None
    runner.comms = _Comms()
    return runner


def test_run_cinematographer_creates_and_runs_the_agent_exactly_once(monkeypatch):
    factory_calls = []
    generator_runs = []

    def fake_create_cinematographer_agent(model_config=None, brain=None, session_id=None):
        factory_calls.append((model_config, session_id))

        def run_agent(director_output, mode="both", max_shots=None, duration_sec=None,
                      resume_history=None, user_feedback=None):
            generator_runs.append(director_output)
            yield ("thinking", "planning shots")
            yield ("output", "shot-1.mp4")
            yield ("done", "ok")

        return run_agent

    monkeypatch.setattr(
        agent_runner_module, "create_cinematographer_agent", fake_create_cinematographer_agent
    )
    runner = _runner_without_init()

    events = list(runner.run_cinematographer("A dragon over Whiterun", mode="both", max_shots=1))

    assert len(factory_calls) == 1, f"agent created {len(factory_calls)} times (paid work runs per creation)"
    assert len(generator_runs) == 1, f"agent generator driven {len(generator_runs)} times"
    outputs = [e for e in events if e[1] == "output"]
    assert outputs == [("Cinematographer", "output", "shot-1.mp4")], events
    logged_outputs = [e for e in runner.session.events if e[1] == "output"]
    assert len(logged_outputs) == 1, runner.session.events
    assert runner.comms.sent == [("Cinematographer", "Director", "Received script. Beginning visualization.")]


def test_run_cinematographer_with_no_context_yields_one_error_and_nothing_else():
    runner = _runner_without_init()
    events = list(runner.run_cinematographer(None))
    assert events == [("Cinematographer", "error", "No context to visualize.")]
