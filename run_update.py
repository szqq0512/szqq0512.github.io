"""
批量更新全国重点文物保护单位批次标注
用法: py -3 run_update.py
"""
from pathlib import Path
import re
import json
import time
import sys

root = Path(r'f:\OneDrive\文档\笔记\旅游\中国各地旅游资源')
ref_dir = Path(r'f:\OneDrive\文档\笔记\旅游\综合介绍\综合旅游景点线路信息\国家级风景名胜\全国重点文物保护单位')

# ===== 1. 加载本地参考数据 =====
batch_names = {}
for path in ref_dir.glob('全国重点文物保护单位（*批）.md'):
    text = path.read_text(encoding='utf-8')
    if '图片' in text or ('！[]' in text and len(text) < 200):
        continue
    m = re.search(r'（(第[一二三四五六七八]批)）', path.stem)
    if not m:
        continue
    batch = m.group(1)
    names = []
    for line in text.splitlines():
        if '|' not in line or not line.strip().startswith('|'):
            continue
        if line.strip().startswith('| 编号') or line.strip().startswith('| 序号') or line.strip().startswith('| :----') or line.strip().startswith('| ----'):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) >= 3:
            name = cols[2]
            if name and name not in {'名称', '分类号'} and not re.fullmatch(r'[:\-]+', name):
                names.append(name)
    batch_names[batch] = names

batch_names_norm = {}
for batch, names in batch_names.items():
    batch_names_norm[batch] = [re.sub(r'[^\w\u4e00-\u9fff]', '', n) for n in names]

BATCH_SUFFIXES = {
    '第一批': '一', '第二批': '二', '第三批': '三', '第四批': '四',
    '第五批': '五', '第六批': '六', '第七批': '七', '第八批': '八'
}

def normalize_name(value: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fff]', '', value)

def normalize_batch_name(value: str) -> str:
    if not value: return ''
    value = value.strip()
    if value in BATCH_SUFFIXES: return value
    if value in BATCH_SUFFIXES.values():
        return next(l for l, s in BATCH_SUFFIXES.items() if s == value)
    if re.fullmatch(r'[一二三四五六七八]', value):
        return next(l for l, s in BATCH_SUFFIXES.items() if s == value)
    return value

def batch_to_suffix(value: str) -> str:
    return BATCH_SUFFIXES.get(normalize_batch_name(value), value)

# ===== 2. 缓存 =====
cache_path = Path(r'f:\OneDrive\文档\笔记\.pwpb_batch_cache.json')
cache = {}
if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text(encoding='utf-8'))
    except Exception:
        cache = {}

# ===== 3. 核心匹配逻辑 =====
def find_batch(title: str):
    norm_title = normalize_name(title)
    if not norm_title:
        return None
    best_batch = None
    best_score = 0.0
    for batch, names in batch_names_norm.items():
        for ref_name in names:
            if not ref_name: continue
            if norm_title == ref_name:
                return batch
            if norm_title in ref_name or ref_name in norm_title:
                return batch
            score = SequenceMatcher(None, norm_title, ref_name).ratio()
            if score > best_score:
                best_score = score
                best_batch = batch
    return best_batch if best_score >= 0.78 else None

# ===== 4. 执行更新 =====
from difflib import SequenceMatcher

updated_files = 0
updated_lines = 0
unmatched = []
changed = []
start_time = time.time()

file_count = 0
for path in root.rglob('*.md'):
    if any(part in {'vx_recycle_bin', 'vx_notebook'} for part in path.parts):
        continue
    if not path.is_file():
        continue
    
    file_count += 1
    if file_count % 100 == 0:
        elapsed = time.time() - start_time
        print(f'进度: {file_count} 文件, 已更新 {updated_lines} 行, 耗时 {elapsed:.0f}s')
    
    text = path.read_text(encoding='utf-8')
    new_lines = []
    changed_in_file = False
    
    for line in text.splitlines():
        if '全国重点文物保护单位' in line and not re.search(r'全国重点文物保护单位（[一二三四五六七八]）', line):
            m = re.search(r'【([^】]+)】', line)
            title = m.group(1) if m else ''
            if title:
                found_batch = find_batch(title)
                if found_batch:
                    batch_num = batch_to_suffix(found_batch)
                    line = re.sub(r'全国重点文物保护单位', f'全国重点文物保护单位（{batch_num}）', line, count=1)
                    updated_lines += 1
                    changed.append((str(path.relative_to(root)), title, batch_num))
                    changed_in_file = True
                else:
                    unmatched.append((str(path.relative_to(root)), title))
            else:
                unmatched.append((str(path.relative_to(root)), line.strip()))
        new_lines.append(line)
    
    if changed_in_file:
        path.write_text('\n'.join(new_lines) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
        updated_files += 1

elapsed = time.time() - start_time
print(f'\n=== 完成 ===')
print(f'处理文件: {file_count}')
print(f'更新行数: {updated_lines}')
print(f'更新文件: {updated_files}')
print(f'耗时: {elapsed:.0f}秒')
print(f'未匹配数: {len(unmatched)}')
print(f'\n更新样本:')
for item in changed[:30]:
    print(item)
print(f'\n未匹配样本:')
for item in unmatched[:30]:
    print(item)
