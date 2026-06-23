import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "translate_pdf_preserve_layout.py"
SPEC = importlib.util.spec_from_file_location("translate_pdf_preserve_layout", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_output_pdf_uses_polished_filename():
    assert MODULE.OUTPUT_PDF.name == "OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf"


def test_load_polish_overrides_reads_expected_maps():
    overrides = MODULE.load_polish_overrides()

    assert set(overrides) == {"term_map", "direct_map"}
    assert overrides["direct_map"]["Durable threads"] == "持久线程"
    assert overrides["term_map"]["vault"] == "记忆库"


def test_apply_polish_prefers_direct_override():
    overrides = {
        "direct_map": {
            "Durable threads": "持久线程",
        },
        "term_map": {
            "durable thread": "持久线程",
        },
    }

    result = MODULE.apply_polish("Durable threads", "耐用的螺纹", overrides)
    assert result == "持久线程"


def test_apply_polish_repairs_machine_translation_terms():
    overrides = {
        "direct_map": {},
        "term_map": {
            "vault": "记忆库",
            "steering": "引导",
        },
    }

    result = MODULE.apply_polish(
        "The vault and steering features help Codex.",
        "拱顶和转向功能帮助法典。",
        overrides,
    )

    assert "记忆库" in result
    assert "引导" in result
    assert "Codex" in result
    assert "拱顶" not in result
    assert "法典" not in result


def test_apply_polish_uses_term_map_to_replace_common_wrong_chinese_variants():
    overrides = {
        "direct_map": {},
        "term_map": {
            "repository": "代码仓库",
            "open loops": "未闭环事项",
            "remote control": "远程控制",
        },
    }

    result = MODULE.apply_polish(
        "Open loops live in the repository. Remote control matters.",
        "开环保存在存储库中。遥控很重要。",
        overrides,
    )

    assert "代码仓库" in result
    assert "未闭环事项" in result
    assert "远程控制" in result
    assert "代码仓库库" not in result
    assert "存储库" not in result
    assert "开环" not in result
    assert "遥控" not in result


def test_apply_polish_triggers_term_map_for_source_english_variants():
    overrides = {
        "direct_map": {},
        "term_map": {
            "repository": "代码仓库",
        },
    }

    result = MODULE.apply_polish(
        "These repos stay organized.",
        "这些存储库保持有序。",
        overrides,
    )

    assert "代码仓库" in result
    assert "存储库" not in result


def test_apply_polish_does_not_replace_when_source_term_is_unrelated():
    overrides = {
        "direct_map": {},
        "term_map": {
            "repository": "代码仓库",
        },
    }

    result = MODULE.apply_polish(
        "The library stays organized.",
        "这些存储库保持有序。",
        overrides,
    )

    assert result == "这些存储库保持有序。"
