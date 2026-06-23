import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OVERRIDES_PATH = REPO_ROOT / "scripts" / "cn_polish_overrides.json"
EXPECTED_TERM_KEYS = {
    "durable thread",
    "durable threads",
    "voice input",
    "steering",
    "memory",
    "vault",
    "remote control",
    "computer and browser use",
    "thread automations",
    "goals",
    "side panel",
    "repository",
    "repositories",
    "repo",
    "repos",
    "open loops",
}
EXPECTED_DIRECT_KEYS = {
    "WHITE PAPER",
    "Codex-maxxing for\nlong-running work",
    "How Codex helps work continue\nbeyond a single prompt",
    "Contents",
    "Durable threads",
    "Voice input",
    "Steering",
    "Memory",
    "Computer and\nbrowser use",
    "Remote control",
    "Thread\nautomations",
    "Three examples\nof loops",
    "Goals",
    "Side panel",
}


def load_overrides():
    return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))


def test_cover_and_terms_are_polished():
    overrides = load_overrides()

    assert overrides["direct_map"]["Codex-maxxing for\nlong-running work"] == "Codex 持续工作流实践"
    assert (
        overrides["direct_map"]["How Codex helps work continue\nbeyond a single prompt"]
        == "Codex 如何让工作在单次提示之外持续推进"
    )
    assert overrides["term_map"]["durable thread"] == "持久线程"
    assert overrides["term_map"]["vault"] == "记忆库"
    assert overrides["term_map"]["steering"] == "引导"


def test_overrides_shape_is_script_friendly():
    overrides = load_overrides()

    assert set(overrides) == {"term_map", "direct_map"}
    assert all(isinstance(key, str) and isinstance(value, str) for key, value in overrides["term_map"].items())
    assert all(
        isinstance(key, str) and isinstance(value, str) for key, value in overrides["direct_map"].items()
    )


def test_overrides_include_required_keys_and_minimum_coverage():
    overrides = load_overrides()
    term_map = overrides["term_map"]
    direct_map = overrides["direct_map"]

    assert EXPECTED_TERM_KEYS <= set(term_map)
    assert EXPECTED_DIRECT_KEYS <= set(direct_map)
    assert len(term_map) >= 16
    assert len(direct_map) >= 14
