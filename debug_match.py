"""调试匹配问题"""
from pathlib import Path
import re
from difflib import SequenceMatcher

ref_dir = Path(r'f:\OneDrive\文档\笔记\旅游\综合介绍\综合旅游景点线路信息\国家级风景名胜\全国重点文物保护单位')

# 检查参考文件
print('=== 参考文件 ===')
for path in ref_dir.glob('全国重点文物保护单位（*批）.md'):
    print(f'文件: {path.stem}')
    text = path.read_text(encoding='utf-8')
    if '图片' in text or ('！[]' in text and len(text) < 200):
        print('  -> 跳过（图片文件）')
        continue
    m = re.search(r'（(第[一二三四五六七八]批)）', path.stem)
    if m:
        batch = m.group(1)
        print(f'  -> 批次: {batch}')
    
    # 提取名称
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
    
    print(f'  -> 前5个名称:')
    for n in names[:5]:
        norm = re.sub(r'[^\w\u4e00-\u9fff]', '', n)
        print(f'    原始: "{n}" -> 标准化: "{norm}"')
    break  # 只检查第一个文件

# 检查目标文件中的标题
print('\n=== 目标文件中的标题样本 ===')
root = Path(r'f:\OneDrive\文档\笔记\旅游\中国各地旅游资源')
for p in root.rglob('*.md'):
    if any(x in p.parts for x in {'vx_recycle_bin','vx_notebook'}):
        continue
    t = p.read_text(encoding='utf-8')
    for l in t.splitlines():
        if '全国重点文物保护单位' in l and not re.search(r'全国重点文物保护单位（[一二三四五六七八]）', l):
            m = re.search(r'【([^】]+)】', l)
            if m:
                title = m.group(1)
                norm = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
                print(f'  原始: "{title}" -> 标准化: "{norm}"')
                # 计算与参考名的相似度
                ref_sample = '丽江古城'  # 假设参考文件中有这个
                score = SequenceMatcher(None, norm, re.sub(r'[^\w\u4e00-\u9fff]', '', ref_sample)).ratio()
                print(f'     -> 与"{ref_sample}"相似度: {score:.2f}')
                break
    break  # 只检查第一个文件
