import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "scripts" / "translate_pdf_preserve_layout.py"
DEFAULT_SOURCE_PDF = ROOT / "source_codex_maxxing26.pdf"
DEFAULT_TMP_DIR = ROOT / "tmp" / "pdfs" / "codex_cn"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "pdf"
DEFAULT_OVERRIDES_JSON = ROOT / "scripts" / "cn_polish_overrides.json"
DEFAULT_PDFTOPPM = Path(
    r"C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
)


def load_pipeline_module():
    spec = importlib.util.spec_from_file_location("translate_pdf_preserve_layout", PIPELINE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def default_output_pdf(source_pdf: Path, output_dir: Path) -> Path:
    return output_dir / f"{source_pdf.stem}_中文润色增强版.pdf"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the PDF translation pipeline with configurable input, output, and cache paths."
    )
    parser.add_argument("-i", "--source-pdf", default=str(DEFAULT_SOURCE_PDF), help="Path to the source PDF.")
    parser.add_argument(
        "-o",
        "--output-pdf",
        default=None,
        help="Path to the generated PDF. Defaults to output/pdf/<source_stem>_中文润色增强版.pdf.",
    )
    parser.add_argument(
        "--tmp-dir",
        default=str(DEFAULT_TMP_DIR),
        help="Directory for blocks.json, translations.json, previews, and overlay artifacts.",
    )
    parser.add_argument(
        "--overrides-json",
        default=str(DEFAULT_OVERRIDES_JSON),
        help="Path to the terminology and polish override JSON file.",
    )
    parser.add_argument(
        "--pdftoppm",
        default=str(DEFAULT_PDFTOPPM),
        help="Path to the pdftoppm executable used to render preview pages.",
    )
    parser.add_argument(
        "--refresh-translations",
        action="store_true",
        help="Delete translations.json before running so translations are rebuilt from scratch.",
    )
    return parser.parse_args(argv)


def apply_runtime_overrides(module, args):
    source_pdf = Path(args.source_pdf).expanduser().resolve()
    tmp_dir = Path(args.tmp_dir).expanduser().resolve()
    output_pdf = (
        Path(args.output_pdf).expanduser().resolve()
        if args.output_pdf
        else default_output_pdf(source_pdf, DEFAULT_OUTPUT_DIR)
    )

    module.SOURCE_PDF = source_pdf
    module.TMP_DIR = tmp_dir
    module.PREVIEW_DIR = tmp_dir / "rendered_pages"
    module.BLOCKS_JSON = tmp_dir / "blocks.json"
    module.TRANSLATIONS_JSON = tmp_dir / "translations.json"
    module.POLISH_OVERRIDES_JSON = Path(args.overrides_json).expanduser().resolve()
    module.OVERLAY_PDF = tmp_dir / "overlay.pdf"
    module.OUTPUT_DIR = output_pdf.parent
    module.OUTPUT_PDF = output_pdf
    module.PDFTOPPM = Path(args.pdftoppm).expanduser().resolve()

    if args.refresh_translations and module.TRANSLATIONS_JSON.exists():
        module.TRANSLATIONS_JSON.unlink()

    return output_pdf


def main(argv=None):
    args = parse_args(argv)
    module = load_pipeline_module()
    apply_runtime_overrides(module, args)
    module.main()


if __name__ == "__main__":
    main()
