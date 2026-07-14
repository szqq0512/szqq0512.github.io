from pathlib import Path
import re

root = Path(r'f:\OneDrive\文档\笔记\旅游\中国各地旅游资源')
cnt = 0
samples = []

for p in root.rglob('*.md'):
    if any(x in p.parts for x in {'vx_recycle_bin','vx_notebook'}):
        continue
    t = p.read_text(encoding='utf-8')
    for l in t.splitlines():
        if '全国重点文物保护单位' in l and not re.search(r'全国重点文物保护单位（[一二三四五六七八]）', l):
            cnt += 1
            if len(samples) < 10:
                m = re.search(r'【([^】]+)】', l)
                title = m.group(1) if m else l.strip()
                samples.append((str(p.relative_to(root)), title))

print(f'unannotated_count={cnt}')
print('--- sample titles ---')
for s in samples:
    print(s)
