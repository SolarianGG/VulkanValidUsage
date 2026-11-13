"""Builds and executes `notebooks/report.ipynb` (Stage 8 figures and tables).

Run: `uv run --group report python notebooks/make_report_notebook.py`. The notebook only reads frozen run
outputs through `vkrag.report`; nothing calls a model or a paid API.
"""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent

md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell

cells = [
    md("# Vulkan VU: RAG vs model memory — report figures\n\n"
       "Companion to `reports/report.md`. Final run = pilot (`runs/pilot`), exploratory analysis "
       "(PLAN §10, 2026-11-10). All numbers come from `vkrag.report`, the same code that writes "
       "`reports/report_tables.md`."),
    code("import json\nimport pandas as pd\nfrom IPython.display import Image, Markdown, display\n"
         "from vkrag.config import ROOT\nfrom vkrag import report\n\n"
         "R = report.Run('pilot', 'pilot')\n"
         "data = {'table1': report.table1(R), 'table2': report.table2(R), 'by_stratum': report.by_stratum(R),\n"
         "        'table4': report.table4(R)}\n"
         "paths = report.figures(data, ROOT / 'reports' / 'figures')\n[p.name for p in paths]"),
    md("## Generation: score by configuration (answerable questions, n = 45 per cell)"),
    code("rows = []\nfor k, v in data['table2'].items():\n    a, c = k.split('|')\n"
         "    rows.append({'answerer': a, 'config': c, 'score': v['score'], 'ci_lo': v['score_ci']['ci95'][0],\n"
         "                 'ci_hi': v['score_ci']['ci95'][1], 'correct': v['correct'], 'hallucination': v['hallucination'],\n"
         "                 'fabricated_vuid': v['fabricated_vuid']})\n"
         "pd.DataFrame(rows).pivot(index='config', columns='answerer', values='score').loc[list(report.GEN_CONFIGS)]"),
    md("## Score by stratum (H1)\n\nn = 9 questions per bar; the intervals are wide and overlap, so the "
       "stratum pattern is descriptive only."),
    code("display(Image(filename=str(ROOT / 'reports/figures/score_by_stratum.png')))"),
    md("## Retrieval: Recall@k by equivalence class (H2, H3a)"),
    code("pd.DataFrame({c: {k: data['table1'][c]['all'][f'class@{k}'] for k in (1, 3, 5, 10, 20)}\n"
         "              for c in ('bm25', 'dense', 'rrf', 'rrf_rerank', 'hyde_rrf', 'rewrite_rrf')}).T"),
    code("display(Image(filename=str(ROOT / 'reports/figures/recall_at_k.png')))"),
    md("## Cost (H5): remote answerer, score vs cost per question"),
    code("pd.DataFrame(data['table4']['remote']).T[['score', 'cost_per_question', 'cost_per_correct', 'tokens_in_mean', "
         "'tokens_out_mean']]"),
    code("display(Image(filename=str(ROOT / 'reports/figures/pareto_cost_remote.png')))"),
    md("## Score vs answer latency\n\nLatency of the generation call only (no phase L, no retrieval time); "
       "qwen ran locally and sequentially, remote through OpenRouter."),
    code("display(Image(filename=str(ROOT / 'reports/figures/score_vs_latency.png')))"),
    md("## Hypothesis tests (exploratory)"),
    code("h = json.loads((ROOT / 'runs/pilot/hypotheses.json').read_text(encoding='utf-8'))\n"
         "pd.DataFrame({k: {f: v.get(f) for f in ('comparison', 'mean_a', 'mean_b', 'diff', 'ci95', 'p', 'p_holm')}\n"
         "              for k, v in h['tests'].items()}).T"),
]

nb = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(HERE.parent)}}).execute()
nbformat.write(nb, HERE / "report.ipynb")
print("wrote", HERE / "report.ipynb")
