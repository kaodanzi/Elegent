# Codex-maxxing 中文润色增强版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一版术语统一、标题和正文读感更自然、且保留原始版式的 `Codex-maxxing` 中文润色增强版 PDF。

**Architecture:** 继续使用“提取文本块 -> 生成覆盖层 -> 合并回原 PDF”的现有流程，但在机器翻译缓存之上增加人工润色覆盖层。将术语表和重点段落覆盖映射从脚本中分离成独立数据文件，让润色规则可维护、可复用，并通过小范围自动化检查保障输出文件名、术语命中和 PDF 生成结果稳定。

**Tech Stack:** Python、pdfplumber、pypdf、reportlab、Pillow、Poppler、JSON

---

### Task 1: 建立术语表与人工润色覆盖数据

**Files:**
- Create: `D:\codex生成\scripts\cn_polish_overrides.json`
- Create: `D:\codex生成\tests\test_cn_polish_overrides.py`

- [ ] **Step 1: 写一个失败的测试，锁定核心术语和封面标题的目标译法**

```python
import json
from pathlib import Path


def load_overrides():
    path = Path(r"D:\codex生成\scripts\cn_polish_overrides.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_cover_and_terms_are_polished():
    overrides = load_overrides()

    assert overrides["direct_map"]["Codex-maxxing for\nlong-running work"] == "Codex 持续工作流实践"
    assert overrides["direct_map"]["How Codex helps work continue\nbeyond a single prompt"] == "Codex 如何让工作在单次提示之外持续推进"
    assert overrides["term_map"]["durable thread"] == "持久线程"
    assert overrides["term_map"]["vault"] == "记忆库"
    assert overrides["term_map"]["steering"] == "引导"
```

- [ ] **Step 2: 运行测试，确认当前缺少覆盖数据文件而失败**

Run: `& "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest "D:\codex生成\tests\test_cn_polish_overrides.py" -v`

Expected: FAIL with `FileNotFoundError` for `cn_polish_overrides.json`

- [ ] **Step 3: 新建润色覆盖数据文件，先落关键标题和术语**

```json
{
  "term_map": {
    "durable thread": "持久线程",
    "durable threads": "持久线程",
    "voice input": "语音输入",
    "steering": "引导",
    "memory": "记忆",
    "vault": "记忆库",
    "remote control": "远程控制",
    "computer and browser use": "计算机与浏览器操作",
    "thread automations": "线程自动化",
    "goals": "目标",
    "side panel": "侧边栏",
    "repository": "代码仓库",
    "repositories": "代码仓库",
    "repo": "代码仓库",
    "repos": "代码仓库",
    "open loops": "未闭环事项"
  },
  "direct_map": {
    "WHITE PAPER": "白皮书",
    "Codex-maxxing for\nlong-running work": "Codex 持续工作流实践",
    "How Codex helps work continue\nbeyond a single prompt": "Codex 如何让工作在单次提示之外持续推进",
    "Contents": "目录",
    "Durable threads": "持久线程",
    "Voice input": "语音输入",
    "Steering": "引导",
    "Memory": "记忆",
    "Computer and\nbrowser use": "计算机与浏览器操作",
    "Remote control": "远程控制",
    "Thread\nautomations": "线程自动化",
    "Three examples\nof loops": "三个循环示例",
    "Goals": "目标",
    "Side panel": "侧边栏"
  }
}
```

- [ ] **Step 4: 重新运行测试，确认关键术语和封面标题已固定**

Run: `& "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest "D:\codex生成\tests\test_cn_polish_overrides.py" -v`

Expected: PASS

- [ ] **Step 5: 记录本任务变更文件，供后续统一复核**

Run: `Get-ChildItem "D:\codex生成\scripts\cn_polish_overrides.json","D:\codex生成\tests\test_cn_polish_overrides.py" | Select-Object FullName,Length`

Expected: two files listed with non-zero `Length`

### Task 2: 让翻译脚本支持人工润色覆盖和术语统一

**Files:**
- Modify: `D:\codex生成\scripts\translate_pdf_preserve_layout.py`
- Test: `D:\codex生成\tests\test_translate_pdf_preserve_layout.py`

- [ ] **Step 1: 写一个失败的脚本级测试，验证覆盖层优先于机翻缓存**

```python
import importlib.util
from pathlib import Path


MODULE_PATH = Path(r"D:\codex生成\scripts\translate_pdf_preserve_layout.py")
spec = importlib.util.spec_from_file_location("translate_pdf_preserve_layout", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_apply_polish_prefers_direct_override():
    overrides = {
        "direct_map": {
            "Durable threads": "持久线程"
        },
        "term_map": {
            "durable thread": "持久线程"
        }
    }

    result = module.apply_polish("Durable threads", "耐用的螺纹", overrides)
    assert result == "持久线程"


def test_apply_polish_repairs_machine_translation_terms():
    overrides = {
        "direct_map": {},
        "term_map": {
            "vault": "记忆库"
        }
    }

    result = module.apply_polish("The vault holds rolling context around the work.", "拱顶保存着围绕工作的滚动背景。", overrides)
    assert "记忆库" in result
    assert "拱顶" not in result
```

- [ ] **Step 2: 运行测试，确认脚本里还没有润色入口函数而失败**

Run: `& "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest "D:\codex生成\tests\test_translate_pdf_preserve_layout.py" -v`

Expected: FAIL with `AttributeError: module 'translate_pdf_preserve_layout' has no attribute 'apply_polish'`

- [ ] **Step 3: 修改脚本，补齐覆盖数据加载、术语修正和文件名修复逻辑**

```python
POLISH_OVERRIDES_JSON = ROOT / "scripts" / "cn_polish_overrides.json"
OUTPUT_PDF = OUTPUT_DIR / "OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf"


def load_polish_overrides():
    if not POLISH_OVERRIDES_JSON.exists():
        return {"term_map": {}, "direct_map": {}}
    return json.loads(POLISH_OVERRIDES_JSON.read_text(encoding="utf-8"))


def replace_terms(text: str, term_map: dict[str, str]) -> str:
    result = text
    for source, target in sorted(term_map.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(re.escape(source), re.IGNORECASE)
        result = pattern.sub(target, result)
    return result


def apply_polish(source_text: str, translated_text: str, overrides: dict) -> str:
    direct_map = overrides.get("direct_map", {})
    term_map = overrides.get("term_map", {})

    normalized_source = source_text.strip()
    normalized_translated = translated_text.strip()

    if normalized_source in direct_map:
        return direct_map[normalized_source]

    polished = replace_terms(normalized_translated, term_map)
    polished = polished.replace("法典", "Codex")
    polished = polished.replace("螺纹", "线程")
    polished = polished.replace("拱顶", "记忆库")
    polished = re.sub(r"\s+", " ", polished).strip()
    return polished


def build_translations(block_pages):
    cache = load_translation_cache()
    overrides = load_polish_overrides()
    updated = False
    for page in block_pages:
        for block in page["blocks"]:
            text = block["text"]
            if text not in cache:
                if mostly_non_letters(text):
                    cache[text] = text
                else:
                    cache[text] = google_translate(text)
                    time.sleep(0.12)
                updated = True
            cache[text] = apply_polish(text, cache[text], overrides)
    if updated:
        save_translation_cache(cache)
    return cache
```

- [ ] **Step 4: 重新运行测试，确认覆盖层优先级和术语修复都生效**

Run: `& "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest "D:\codex生成\tests\test_translate_pdf_preserve_layout.py" -v`

Expected: PASS

- [ ] **Step 5: 做一次脚本静态冒烟，确认输出文件名和入口函数无语法问题**

Run: `@'`nimport importlib.util`nfrom pathlib import Path`npath = Path(r"D:\codex生成\scripts\translate_pdf_preserve_layout.py")`nspec = importlib.util.spec_from_file_location("translate_pdf_preserve_layout", path)`nmodule = importlib.util.module_from_spec(spec)`nassert spec.loader is not None`nspec.loader.exec_module(module)`nprint(module.OUTPUT_PDF.name)`nprint(hasattr(module, "apply_polish"))`n'@ | & "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -`

Expected:
- first line is `OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf`
- second line is `True`

### Task 3: 生成润色增强版 PDF 并做关键页面验收

**Files:**
- Modify: `D:\codex生成\tmp\pdfs\codex_cn\translations.json`
- Create: `D:\codex生成\output\pdf\OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf`
- Verify: `D:\codex生成\tmp\pdfs\translated_preview\page-01.png`
- Verify: `D:\codex生成\tmp\pdfs\translated_preview\page-02.png`
- Verify: `D:\codex生成\tmp\pdfs\translated_preview\page-05.png`

- [ ] **Step 1: 运行脚本生成润色增强版 PDF**

Run: `& "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "D:\codex生成\scripts\translate_pdf_preserve_layout.py"`

Expected: prints `D:\codex生成\output\pdf\OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf`

- [ ] **Step 2: 验证 PDF 文件存在且页数保持 27 页**

Run: `@'`nfrom pathlib import Path`nfrom pypdf import PdfReader`npath = Path(r"D:\codex生成\output\pdf\OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf")`nprint(path.exists())`nprint(len(PdfReader(str(path)).pages))`n'@ | & "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -`

Expected:
- first line is `True`
- second line is `27`

- [ ] **Step 3: 渲染关键页面做人工验收**

Run: `New-Item -ItemType Directory -Force -Path "D:\codex生成\tmp\pdfs\translated_preview" | Out-Null; & "C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe" -f 1 -l 5 -png "D:\codex生成\output\pdf\OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf" "D:\codex生成\tmp\pdfs\translated_preview\page"`

Expected: generated PNG files `page-01.png` through `page-05.png`

- [ ] **Step 4: 核对封面、目录和章节页的关键文案**

```text
page-01.png:
- “Codex 持续工作流实践”
- “Codex 如何让工作在单次提示之外持续推进”

page-02.png:
- “目录”
- “持久线程 / 语音输入 / 引导 / 记忆 / 计算机与浏览器操作 / 远程控制 / 线程自动化 / 三个循环示例 / 目标 / 侧边栏”

page-05.png:
- “持久线程”
- “给工作一个安身之处”
- 不再出现“螺纹”“法典”“拱顶”等错误术语
```

- [ ] **Step 5: 记录交付文件并输出文件信息**

Run: `Get-Item "D:\codex生成\output\pdf\OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf" | Select-Object FullName,Length,LastWriteTime`

Expected: one row with the final PDF path, non-zero `Length`, and current `LastWriteTime`
