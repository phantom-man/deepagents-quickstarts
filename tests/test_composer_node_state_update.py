"""Gated finding 2026-09-05 (colibri review of DeepAgents/graphs/agency_graph.py, HIGH):
`composer_node` built its state_update twice and appended the single-track asset
outside the `if match`.

- Single-track with no path in the result: `assets.append(audio_path)` ran with
  `audio_path` unbound -> UnboundLocalError -> the node's own `except` reported
  "Audio Error" and threw the real result away.
- Single-track with a path: the asset was appended twice.
- Multi-track: the unconditional trailing re-assignment overwrote the
  "Multi-Track Generation Complete" update with "Audio Created: {last result}",
  and with every track lacking a prompt `result` was unbound there too.

Idiom follows tests/test_agent_runner_cinematographer.py: stub the paid call at
its module, silence progress comms, drive the node directly.
"""

import asyncio

import pytest

import DeepAgents.CommercialAgents.composer_agent.agent as composer_agent_module
import DeepAgents.graphs.agency_graph as ag


def _run(state, configurable):
    return asyncio.run(ag.composer_node(state, {"configurable": configurable}))


def _content(cmd) -> str:
    return cmd.update["messages"][0].content


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(ag, "_emit_progress", lambda *a, **k: None)


@pytest.fixture
def composer_calls(monkeypatch):
    """Stub run_composer_task; each call returns the string queued for it."""
    calls: list = []
    queue: list = []

    def fake_run_composer_task(*args, **kwargs):
        calls.append((args, kwargs))
        return queue.pop(0) if queue else "Composition finished with no file written"

    monkeypatch.setattr(composer_agent_module, "run_composer_task", fake_run_composer_task)
    return calls, queue


class TestSingleTrack:
    def test_a_result_without_a_path_is_not_an_error(self, quiet, composer_calls):
        calls, queue = composer_calls
        queue.append("Composition finished but the model returned no file")
        cmd = _run({"director_plan": "make a jingle", "video_assets": []}, {})
        assert len(calls) == 1
        assert _content(cmd).startswith("Audio Created:"), _content(cmd)
        assert cmd.update["audio_assets"] == []
        assert cmd.goto == "director"

    def test_a_result_with_a_path_yields_the_asset_exactly_once(self, quiet, composer_calls):
        calls, queue = composer_calls
        queue.append("Saved track to Artifacts/audio/jingle.wav for review")
        cmd = _run({"director_plan": "make a jingle", "video_assets": []}, {})
        assets = cmd.update["audio_assets"]
        assert len(assets) == 1, assets
        assert assets[0].endswith("jingle.wav")
        assert _content(cmd).startswith("Audio Created:")


class TestMultiTrack:
    def test_multi_track_update_survives_to_the_command(self, quiet, composer_calls):
        calls, queue = composer_calls
        queue.extend(["Track saved Artifacts/audio/t1.wav", "Track saved Artifacts/audio/t2.wav"])
        cmd = _run(
            {"director_plan": "two tracks", "video_assets": []},
            {"composer_multi_mode": True, "composer_tracks": [{"prompt": "drums"}, {"prompt": "bass"}]},
        )
        assert len(calls) == 2
        assert _content(cmd).startswith("Multi-Track Generation Complete (2 tracks)"), _content(cmd)
        assert [a[-6:] for a in cmd.update["audio_assets"]] == ["t1.wav", "t2.wav"]

    def test_all_tracks_without_a_prompt_is_reported_not_raised(self, quiet, composer_calls):
        calls, _queue = composer_calls
        cmd = _run(
            {"director_plan": "two tracks", "video_assets": []},
            {"composer_multi_mode": True, "composer_tracks": [{"lyrics": "la"}, {"lyrics": "di"}]},
        )
        assert calls == []
        assert _content(cmd) == "Multi-track generation produced no assets", _content(cmd)
        assert cmd.update["audio_assets"] == []
