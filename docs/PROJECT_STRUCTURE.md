# 项目目录说明

## 根目录

- `source_codex_maxxing26.pdf`
  - 当前样例的英文原始 PDF
- `.gitignore`
  - Git 忽略规则，排除缓存、中间文件和临时目录
- `README.md`
  - 项目总览、运行方式与主要产物说明

## `scripts/`

- `translate_pdf_preserve_layout.py`
  - 项目主处理脚本
  - 负责文本抽取、翻译、术语修正、覆盖层绘制和 PDF 合成
- `translate_pdf_cli.py`
  - 命令行入口脚本
  - 负责接收输入/输出/缓存等参数，并调用主处理脚本
- `cn_polish_overrides.json`
  - 术语映射、标题替换、重点页面人工润色配置
- `__pycache__/`
  - Python 执行缓存，不属于源码

## `tests/`

- `test_translate_pdf_preserve_layout.py`
  - 校验主脚本输出路径、润色逻辑与关键替换行为
- `test_cn_polish_overrides.py`
  - 校验术语表结构、覆盖率与固定映射
- `__pycache__/`
  - Python 测试缓存

## `output/`

- `pdf/`
  - 放置最终导出的 PDF 文件
  - 当前包含普通中文翻译版和润色增强版

## `tmp/`

- `pdfs/codex_cn/`
  - 文本块抽取结果、翻译缓存、覆盖层等处理中间文件
- `pdfs/source_preview/`
  - 原始 PDF 预览渲染图
- `pdfs/translated_preview/`
  - 翻译结果预览图，用于人工检查版面
- `pytest_deps/`
  - 为临时测试准备的依赖目录

这个目录整体属于运行中间态，通常不建议纳入版本管理。

## `docs/`

- `PROJECT_STRUCTURE.md`
  - 当前这份目录说明
- `superpowers/specs/`
  - 中文润色方案设计文档
- `superpowers/plans/`
  - 对应执行计划文档

## 其他历史与临时内容

- `.git.bak/`
  - 早先损坏的 Git 元数据备份目录
- `pytest-cache-files-*`
  - 之前测试流程遗留的临时目录，已通过忽略规则排除

如果后续继续整理仓库，建议优先把“输入文件”“脚本”“配置”“测试”“输出产物”维持为这几个清晰分层。
