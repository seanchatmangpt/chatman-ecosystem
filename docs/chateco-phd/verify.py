from pathlib import Path
import re,sys
root=Path(__file__).parent/'src'
s=(root/'SUMMARY.md').read_text(encoding='utf-8')
links=re.findall(r'\[[^\]]+\]\(([^)]+\.md)\)',s)
missing=[x for x in links if not (root/x).exists()]
if missing: raise SystemExit(f'missing targets: {missing}')
chapters=list((root/'chapters').glob('*.md'))
apps=list((root/'appendices').glob('*.md'))
if len(chapters)!=141: raise SystemExit(f'expected 141 chapters, got {len(chapters)}')
if len(apps)!=26: raise SystemExit(f'expected 26 appendices, got {len(apps)}')
short=[]
for p in chapters:
    words=len(re.findall(r"\b\w+[\w'-]*\b",p.read_text(encoding='utf-8')))
    if words<450: short.append((p.name,words))
if short: raise SystemExit(f'non-full chapters: {short[:10]}')
print(f'validated {len(links)} SUMMARY targets, {len(chapters)} full chapters, {len(apps)} appendices')
