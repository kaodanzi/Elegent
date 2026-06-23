# PDF 中文翻译与排版保留项目

这个仓库用于把英文 PDF 翻译为中文，并尽量保留原始版式、分页和视觉结构。

当前项目已经包含一份实际样例：

- 原文 PDF：`source_codex_maxxing26.pdf`
- 中文翻译版：`output/pdf/OAI_WhitePaper_Codex-maxxing26_中文翻译版.pdf`
- 中文润色增强版：`output/pdf/OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf`

## 项目目标

- 提取 PDF 中可选取的正文文字
- 不翻译图片中的文字
- 尽量保持原件排版、分页与结构
- 在机器翻译基础上叠加术语统一和人工润色规则

## 主要文件

- `scripts/translate_pdf_preserve_layout.py`
  - 主脚本，负责抽取文本块、生成翻译、应用润色规则、渲染覆盖层并合成最终 PDF
- `scripts/cn_polish_overrides.json`
  - 中文标题、术语统一和局部人工改写规则
- `tests/test_translate_pdf_preserve_layout.py`
  - 主脚本关键行为测试
- `tests/test_cn_polish_overrides.py`
  - 术语覆盖与润色规则测试

更详细的目录说明见 [docs/PROJECT_STRUCTURE.md](/D:/codex生成/docs/PROJECT_STRUCTURE.md)。

## 目录结构

```text
.
├─ docs/          设计说明、计划、目录说明
├─ output/        生成后的 PDF 成品
├─ scripts/       翻译与排版处理脚本、术语覆盖配置
├─ tests/         自动化测试
├─ tmp/           运行时中间文件与缓存
└─ source_codex_maxxing26.pdf
```

## 运行方式

项目当前的入口脚本是：

```powershell
python .\scripts\translate_pdf_preserve_layout.py
```

脚本会基于仓库根目录中的输入文件和配置，生成或更新：

- `tmp/pdfs/codex_cn/blocks.json`
- `tmp/pdfs/codex_cn/translations.json`
- `output/pdf/` 下的结果 PDF

## 当前流程说明

1. 从源 PDF 中抽取页面文字块
2. 对文本块执行翻译
3. 应用 `cn_polish_overrides.json` 中的标题与术语修正规则
4. 用覆盖层方式把中文文本写回对应版面位置
5. 输出中文 PDF

## 注意事项

- 当前脚本依赖本机可用的 PDF/字体环境与若干 Python 库
- `tmp/` 下内容属于中间产物，一般不需要提交
- 如果后续要扩展到其他 PDF，建议把输入文件名、输出文件名和字体路径参数化

## 后续可继续完善

- 把输入/输出路径改成命令行参数
- 增加批量处理多个 PDF 的能力
- 增加更系统的术语表与版面回归检查
- 为不同风格的中文润色方案提供独立配置
