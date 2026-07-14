from pathlib import Path
import re
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

root = Path(r'f:\OneDrive\文档\笔记\旅游\中国各地旅游资源')
ref_dir = Path(r'f:\OneDrive\文档\笔记\旅游\综合介绍\综合旅游景点线路信息\国家级风景名胜\全国重点文物保护单位')

# Collect reference names from local batch files that are text-readable
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
        if '|' not in line:
            continue
        if not line.strip().startswith('|'):
            continue
        if line.strip().startswith('| 编号') or line.strip().startswith('| 序号') or line.strip().startswith('| :----') or line.strip().startswith('| ----'):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) >= 3:
            name = cols[2]
            if name and name not in {'名称', '分类号'} and not re.fullmatch(r'[:\-]+', name):
                names.append(name)
    batch_names[batch] = names

# Normalize names for matching
batch_names_norm = {}
for batch, names in batch_names.items():
    batch_names_norm[batch] = [re.sub(r'[^\w\u4e00-\u9fff]', '', n) for n in names]

BATCH_LABELS = ['第一批', '第二批', '第三批', '第四批', '第五批', '第六批', '第七批', '第八批']
BATCH_SUFFIXES = {'第一批': '一', '第二批': '二', '第三批': '三', '第四批': '四', '第五批': '五', '第六批': '六', '第七批': '七', '第八批': '八'}


def normalize_name(value: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fff]', '', value)


def normalize_batch_name(value: str) -> str:
    if not value:
        return ''
    value = value.strip()
    if value in BATCH_SUFFIXES:
        return value
    if value in BATCH_SUFFIXES.values():
        return next(label for label, suffix in BATCH_SUFFIXES.items() if suffix == value)
    if re.fullmatch(r'[一二三四五六七八]', value):
        return next(label for label, suffix in BATCH_SUFFIXES.items() if suffix == value)
    return value


def batch_to_suffix(value: str) -> str:
    value = normalize_batch_name(value)
    return BATCH_SUFFIXES.get(value, value)


cache_path = Path(r'f:\OneDrive\文档\笔记\.pwpb_batch_cache.json')
cache = {}
if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text(encoding='utf-8'))
    except Exception:
        cache = {}


def search_ncha_title(title: str):
    try:
        url = 'http://www.ncha.gov.cn/module/search/index.jsp'
        category_ids = ['2273', '2274', '2269', '2270', '2271', '2272']
        for i_columnid in category_ids:
            data = urllib.parse.urlencode({
                'i_columnid': i_columnid,
                'field': 'field_1433:1',
                'currentplace': '',
                'splitflag': '',
                'fullpath': '0',
                'field_1433': '云南省',
                'download': '查询',
                'keyword': title,
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode('utf-8', 'ignore')
            if title in html:
                return True
    except Exception:
        return False
    return False


def search_web_batch(title: str):
    if title in cache:
        return cache[title]
    # Prefer the official NCHA search endpoint as a verification step.
    if search_ncha_title(title):
        cache[title] = None
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
        return None

    queries = [
        f'{title} 第几批全国重点文物保护单位',
        f'{title} 全国重点文物保护单位第几批',
        f'{title} 国保第几批',
    ]
    for query in queries:
        try:
            url = 'https://cn.bing.com/search?format=rss&q=' + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read().decode('utf-8', 'ignore')
            root = ET.fromstring(data)
            for item in root.findall('.//item'):
                combined = ' '.join([
                    item.findtext('title') or '',
                    item.findtext('description') or '',
                ])
                if '全国重点文物保护单位' not in combined and '国保' not in combined:
                    continue
                m = re.search(r'第([一二三四五六七八九十]+)批', combined)
                if m:
                    num = m.group(1)
                    mapping = {'一': '一', '二': '二', '三': '三', '四': '四', '五': '五', '六': '六', '七': '七', '八': '八', '九': '九', '十': '十'}
                    batch = mapping.get(num, None)
                    if batch:
                        cache[title] = batch
                        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
                        return batch
        except Exception:
            pass
        time.sleep(0.5)
    cache[title] = None
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    return None


def find_batch(title: str):
    norm_title = normalize_name(title)
    if not norm_title:
        return None
    best_batch = None
    best_score = 0.0
    for batch, names in batch_names_norm.items():
        for ref_name in names:
            if not ref_name:
                continue
            if norm_title == ref_name:
                return batch
            if norm_title in ref_name or ref_name in norm_title:
                return batch
            score = SequenceMatcher(None, norm_title, ref_name).ratio()
            if score > best_score:
                best_score = score
                best_batch = batch
    if best_score >= 0.78:
        return best_batch
    return None

updated_files = 0
updated_lines = 0
unmatched = []
changed = []

for path in root.rglob('*.md'):
    if any(part in {'vx_recycle_bin', 'vx_notebook'} for part in path.parts):
        continue
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8')
    new_lines = []
    changed_in_file = False
    for line in text.splitlines():
        if '全国重点文物保护单位' in line and not re.search(r'全国重点文物保护单位（[一二三四五六七八]）', line):
            m = re.search(r'【([^】]+)】', line)
            title = m.group(1) if m else ''
            if title:
                found_batch = find_batch(title)
                if not found_batch:
                    found_batch = search_web_batch(title)
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

print(f'updated_files={updated_files}')
print(f'updated_lines={updated_lines}')
print('sample_updates:')
for item in changed[:60]:
    print(item)
print(f'unmatched_count={len(unmatched)}')
print('sample_unmatched:')
for item in unmatched[:40]:
    print(item)
