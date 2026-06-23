import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "translate_pdf_cli.py"
SPEC = importlib.util.spec_from_file_location("translate_pdf_cli", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_default_output_pdf_uses_source_stem():
    source_pdf = Path("D:/work/demo.pdf")
    output_dir = Path("D:/work/out")

    result = MODULE.default_output_pdf(source_pdf, output_dir)

    assert result == output_dir / "demo_中文润色增强版.pdf"


def test_parse_args_accepts_core_cli_options():
    args = MODULE.parse_args(
        [
            "-i",
            "input.pdf",
            "-o",
            "output.pdf",
            "--tmp-dir",
            "tmp/job1",
            "--overrides-json",
            "overrides.json",
            "--pdftoppm",
            "pdftoppm.exe",
            "--refresh-translations",
        ]
    )

    assert args.source_pdf == "input.pdf"
    assert args.output_pdf == "output.pdf"
    assert args.tmp_dir == "tmp/job1"
    assert args.overrides_json == "overrides.json"
    assert args.pdftoppm == "pdftoppm.exe"
    assert args.refresh_translations is True


def test_apply_runtime_overrides_rebinds_pipeline_paths():
    class DummyModule:
        TRANSLATIONS_JSON = Path("missing.json")

    args = MODULE.parse_args(
        [
            "-i",
            str(REPO_ROOT / "source_codex_maxxing26.pdf"),
            "--tmp-dir",
            str(REPO_ROOT / "tmp" / "job-x"),
        ]
    )

    output_pdf = MODULE.apply_runtime_overrides(DummyModule, args)

    assert DummyModule.SOURCE_PDF.name == "source_codex_maxxing26.pdf"
    assert DummyModule.TMP_DIR.name == "job-x"
    assert DummyModule.PREVIEW_DIR == DummyModule.TMP_DIR / "rendered_pages"
    assert DummyModule.BLOCKS_JSON == DummyModule.TMP_DIR / "blocks.json"
    assert DummyModule.TRANSLATIONS_JSON == DummyModule.TMP_DIR / "translations.json"
    assert DummyModule.OVERLAY_PDF == DummyModule.TMP_DIR / "overlay.pdf"
    assert DummyModule.OUTPUT_PDF == output_pdf
    assert output_pdf.name.endswith("_中文润色增强版.pdf")
