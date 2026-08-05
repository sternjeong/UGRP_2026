"""Render patch.jsonl (session-by-session data change log) as a browsable
patch.html, mirroring the visual style of PROJECT_DESIGN.html so the two
docs feel like one system.
"""
import html
import json

IN = "patch.jsonl"
OUT = "patch.html"

HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>3분커리 — 데이터 변경 로그 (patch.jsonl)</title>
<style>
  :root {
    --paper: #f5f6f5; --paper-raised: #ffffff; --ink: #17212b; --ink-soft: #57626f; --ink-faint: #8992a0;
    --line: #dfe3e2; --line-soft: #ebeeec; --accent: #1f6f6b; --accent-soft: #e4efee;
    --decided: #2f7a4f; --decided-bg: #e6f2ea; --open: #a8721f; --open-bg: #f6ecd9;
    --hold: #6c5c9c; --hold-bg: #ece7f5; --memo: #2a5f8f; --memo-bg: #e4edf5; --code-bg: #eef1f0;
    --shadow: 0 1px 2px rgba(23,33,43,.05), 0 8px 24px -12px rgba(23,33,43,.12);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --paper: #12171c; --paper-raised: #1a2129; --ink: #e8ecef; --ink-soft: #a7b1bb; --ink-faint: #6d7883;
      --line: #2a333c; --line-soft: #212a31; --accent: #4fb3ac; --accent-soft: #16302e;
      --decided: #5cb583; --decided-bg: #17301f; --open: #d9a552; --open-bg: #332711;
      --hold: #a996de; --hold-bg: #241f38; --memo: #7bb0e0; --memo-bg: #16232f; --code-bg: #202a31;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -12px rgba(0,0,0,.5);
    }
  }
  :root[data-theme="dark"] {
    --paper: #12171c; --paper-raised: #1a2129; --ink: #e8ecef; --ink-soft: #a7b1bb; --ink-faint: #6d7883;
    --line: #2a333c; --line-soft: #212a31; --accent: #4fb3ac; --accent-soft: #16302e;
    --decided: #5cb583; --decided-bg: #17301f; --open: #d9a552; --open-bg: #332711;
    --hold: #a996de; --hold-bg: #241f38; --memo: #7bb0e0; --memo-bg: #16232f; --code-bg: #202a31;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -12px rgba(0,0,0,.5);
  }
  :root[data-theme="light"] {
    --paper: #f5f6f5; --paper-raised: #ffffff; --ink: #17212b; --ink-soft: #57626f; --ink-faint: #8992a0;
    --line: #dfe3e2; --line-soft: #ebeeec; --accent: #1f6f6b; --accent-soft: #e4efee;
    --decided: #2f7a4f; --decided-bg: #e6f2ea; --open: #a8721f; --open-bg: #f6ecd9;
    --hold: #6c5c9c; --hold-bg: #ece7f5; --memo: #2a5f8f; --memo-bg: #e4edf5; --code-bg: #eef1f0;
    --shadow: 0 1px 2px rgba(23,33,43,.05), 0 8px 24px -12px rgba(23,33,43,.12);
  }
  * { box-sizing: border-box; }
  html { color-scheme: light dark; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
      "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", sans-serif;
    font-size: 15.5px; line-height: 1.65; -webkit-font-smoothing: antialiased;
  }
  .mono { font-family: ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", Consolas, monospace; }
  .wrap { max-width: 880px; margin: 0 auto; padding: 40px 24px 96px; }
  header.top { margin-bottom: 28px; }
  header.top h1 { font-size: 24px; margin: 0 0 6px; }
  header.top p { color: var(--ink-soft); margin: 0; font-size: 14px; }
  .kpi-row { display: flex; gap: 10px; margin: 20px 0 32px; flex-wrap: wrap; }
  .kpi { background: var(--paper-raised); border: 1px solid var(--line); border-radius: 10px; padding: 10px 16px; box-shadow: var(--shadow); }
  .kpi .n { font-size: 20px; font-weight: 700; }
  .kpi .l { font-size: 12px; color: var(--ink-faint); }
  .entry {
    background: var(--paper-raised); border: 1px solid var(--line); border-radius: 14px;
    padding: 20px 22px; margin-bottom: 18px; box-shadow: var(--shadow);
  }
  .entry .date { font-family: ui-monospace, monospace; font-size: 12px; color: var(--accent); font-weight: 600; }
  .entry h2 { font-size: 16px; margin: 6px 0 14px; line-height: 1.5; }
  .block-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--ink-faint); margin: 16px 0 8px; }
  .block-title:first-of-type { margin-top: 0; }
  .change { border-left: 3px solid var(--accent); background: var(--accent-soft); border-radius: 0 8px 8px 0; padding: 10px 14px; margin-bottom: 8px; }
  .change .target { font-family: ui-monospace, monospace; font-size: 12.5px; font-weight: 600; color: var(--accent); }
  .change p { margin: 6px 0 0; font-size: 13.5px; }
  .sample-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }
  .sample-table code { font-family: ui-monospace, monospace; }
  .sample-table td { border-top: 1px solid var(--line-soft); padding: 5px 8px; vertical-align: top; }
  .decision { border-left: 3px solid var(--decided); background: var(--decided-bg); border-radius: 0 8px 8px 0; padding: 10px 14px; margin-bottom: 8px; }
  .decision .claim { font-size: 13.5px; font-weight: 600; }
  .decision .why { font-size: 13px; color: var(--ink-soft); margin-top: 4px; }
  .decision .who { display: inline-block; font-size: 10.5px; margin-top: 6px; padding: 1px 8px; border-radius: 999px; background: var(--paper-raised); border: 1px solid var(--line); color: var(--ink-faint); }
  .open-list { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ink-soft); }
  .open-list li { margin-bottom: 4px; }
  a { color: var(--accent); }
</style>
</head>
<body>
<div class="wrap">
"""

TAIL = """
</div>
</body>
</html>
"""


def esc(s):
    return html.escape(str(s), quote=False)


def render_sample(row):
    parts = []
    for k, v in row.items():
        parts.append(f"<b>{esc(k)}</b>: {esc(v)}")
    return " · ".join(parts)


def render_change(c):
    out = [f'<div class="change"><div class="target">{esc(c.get("target", ""))}</div>']
    if c.get("change"):
        out.append(f"<p>{esc(c['change'])}</p>")
    for key in ("sample_rows", "sample_joined_text"):
        rows = c.get(key)
        if rows:
            out.append(f'<div style="font-size:11.5px;color:var(--ink-faint);margin-top:8px;">{esc(key)}</div>')
            out.append('<table class="sample-table">')
            for row in rows:
                out.append(f"<tr><td>{render_sample(row)}</td></tr>")
            out.append("</table>")
    out.append("</div>")
    return "".join(out)


def render_decision(d):
    who = d.get("made_by", "")
    out = [f'<div class="decision"><div class="claim">{esc(d.get("decision", ""))}</div>']
    if d.get("rationale"):
        out.append(f'<div class="why">{esc(d["rationale"])}</div>')
    if who:
        out.append(f'<div class="who">{esc(who)}</div>')
    out.append("</div>")
    return "".join(out)


def render_entry(e):
    out = [f'<div class="entry"><span class="date">{esc(e.get("date", ""))}</span>']
    out.append(f'<h2>{esc(e.get("session_summary", ""))}</h2>')

    changes = e.get("changes") or []
    if changes:
        out.append('<div class="block-title">변경된 파일</div>')
        for c in changes:
            out.append(render_change(c))

    decisions = e.get("decisions") or []
    if decisions:
        out.append('<div class="block-title">결정 사항</div>')
        for d in decisions:
            out.append(render_decision(d))

    open_items = e.get("open_items") or []
    if open_items:
        out.append('<div class="block-title">열린 항목</div>')
        out.append("<ul class='open-list'>")
        for item in open_items:
            out.append(f"<li>{esc(item)}</li>")
        out.append("</ul>")

    out.append("</div>")
    return "".join(out)


def main():
    entries = [json.loads(l) for l in open(IN, encoding="utf-8") if l.strip()]
    entries.sort(key=lambda e: e.get("date", ""))

    n_changes = sum(len(e.get("changes") or []) for e in entries)
    n_decisions = sum(len(e.get("decisions") or []) for e in entries)
    n_open = sum(len(e.get("open_items") or []) for e in entries)

    body = [HEAD]
    body.append(
        '<header class="top"><h1>데이터 변경 로그</h1>'
        '<p>patch.jsonl을 그대로 렌더링한 브라우저용 뷰 — 세션별로 무엇을 바꿨고 왜 그렇게 결정했는지 기록. '
        '<a href="PROJECT_DESIGN.html">PROJECT_DESIGN.html</a>과 함께 본다.</p></header>'
    )
    body.append(
        f'<div class="kpi-row">'
        f'<div class="kpi"><div class="n">{len(entries)}</div><div class="l">세션 기록</div></div>'
        f'<div class="kpi"><div class="n">{n_changes}</div><div class="l">파일 변경</div></div>'
        f'<div class="kpi"><div class="n">{n_decisions}</div><div class="l">결정 사항</div></div>'
        f'<div class="kpi"><div class="n">{n_open}</div><div class="l">열린 항목</div></div>'
        f"</div>"
    )
    for e in reversed(entries):
        body.append(render_entry(e))
    body.append(TAIL)

    open(OUT, "w", encoding="utf-8").write("".join(body))
    print(f"wrote {OUT}: {len(entries)} entries, {n_changes} changes, {n_decisions} decisions, {n_open} open items")


if __name__ == "__main__":
    main()
