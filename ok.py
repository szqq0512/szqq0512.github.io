import os
import re
from typing import List

# ---------------- 全局常量和预编译正则 ----------------

# 全角转半角映射表（仅针对英文、数字及指定符号）
FULLWIDTH_TO_HALFWIDTH = str.maketrans({
    'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I',
    'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R',
    'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i',
    'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r',
    'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
    '＃': '#', '＊': '*', '＜': '<', '！': '!', '＆': '&'
})

# 连接符规则，包含 -、--、—、一 及与空格组合
RANGE_CONNECTOR = r'(?:\s*(?:[-一—–]{1,2})\s*)'
PHONE_CONNECTOR = r'(?:\s*[-一—–]{1,2}\s*)'

# 日期范围预编译
RE_DATE_RANGE = re.compile(
    r'((?:\d{1,4}年)?(?:\d{1,2}月)?(?:\d{1,2}日?)?)' +
    RANGE_CONNECTOR +
    r'((?:\d{1,4}年)?(?:\d{1,2}月)?(?:\d{1,2}日?)?)'
)

# 保护区域正则（HTML链接、HTML实体、Markdown链接、图片链接、代码块）
PROTECT_PATTERN = re.compile(
    r'(<a\b[^>]*>.*?</a>)'                 # HTML 链接
    r'|(&[a-zA-Z0-9#]+;)'                   # HTML 实体
    r'|(\[[^\]]+\]\([^)]+\))'           # Markdown 链接
    r'|(!\[[^\]]*\]\([^)]+\))'          # Markdown 图片链接
    r'|(```[\s\S]*?```)'                  # Markdown 代码块（多行）
    , re.DOTALL
)

# 标点映射（中文转半角及反向转换）
PUNCT_FULL_TO_HALF = {
    '，': ',', '。': '.', '；': ';', '：': ':',
    '！': '!', '？': '?', '（': '(', '）': ')',
    '“': '"', '”': '"', '‘': "'", '’': "'"
}
PUNCT_HALF_TO_FULL = {v: k for k, v in PUNCT_FULL_TO_HALF.items()}

# ---------------- 处理文件和行 ----------------

def process_markdown_files(root_dir: str):
    """处理当前目录及子目录下所有 Markdown 文件"""
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    print(f"正在处理: {file_path}")
                    process_file(file_path)
                    print(f"处理成功: {file_path}")
                except Exception as e:
                    print(f"处理失败: {file_path}\n错误信息: {e}")

def process_file(file_path: str):
    """处理单个 Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    processed_lines = [process_line(line) for line in content]
    processed_lines = process_consecutive_empty_lines(processed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)

def process_line(line: str) -> str:
    """
    对一行文本进行处理：
      1. 若行中不含 HTML 保护区域，则直接整体处理；
      2. 若包含保护区域，则按保护区域分段处理（跳过行尾处理），
         然后合并后对整行进行一次 final_quote_cleanup（删除引号前后多余空格），
         最后统一应用行尾处理。
    """
    if not PROTECT_PATTERN.search(line):
        processed = apply_all_rules(line, skip_trailing=True)
    else:
        parts = []
        last_index = 0
        for m in PROTECT_PATTERN.finditer(line):
            parts.append(apply_all_rules(line[last_index:m.start()], skip_trailing=True))
            parts.append(m.group(0))
            last_index = m.end()
        parts.append(apply_all_rules(line[last_index:], skip_trailing=True))
        processed = ''.join(parts)
        # 对合并后的整行做一次针对引号空格的后处理
        processed = final_quote_cleanup(processed)
    processed = rule12_trailing_spaces(processed)
    return processed

def apply_all_rules(line: str, skip_trailing: bool = False) -> str:
    """
    按顺序对一行文本应用所有规则（可通过 skip_trailing 跳过 rule12_trailing_spaces，
    以便后续统一处理行尾换行符）。
    """
    if not line.strip():
        return line

    line = rule1_fullwidth_to_halfwidth(line)
    line = rule2_remove_punctuation_between_quotes(line)
    line = rule3_remove_spaces(line)
    line = rule4_punctuation_in_english(line)
    line = rule5_punctuation_in_numbers(line)
    line = rule6_chinese_punctuation(line)
    line = rule7_time_format(line)
    line = rule8_number_range(line)
    line = rule9_date_range(line)
    line = rule10_phone_number(line)
    line = rule11_heading_spaces(line)
    if not skip_trailing:
        line = rule12_trailing_spaces(line)
    line = rule13_convert_punctuation(line)
    return line

def final_quote_cleanup(line: str) -> str:
    """
    对整行文本做一次后处理：删除开引号（“、‘）后面紧跟中文前的空格，
    删除中文后紧跟闭引号（”、’）前的空格。
    """
    line = re.sub(r'([“‘])\s+(?=[\u4e00-\u9fff])', r'\1', line)
    line = re.sub(r'(?<=[\u4e00-\u9fff])\s+([”’])', r'\1', line)
    return line

# ---------------- 各规则实现 ----------------

def rule1_fullwidth_to_halfwidth(line: str) -> str:
    """规则1: 全角英文、数字及特定符号转换为半角"""
    return line.translate(FULLWIDTH_TO_HALFWIDTH)

def rule2_remove_punctuation_between_quotes(line: str) -> str:
    """规则2: 删除右书名号与左书名号之间的顿号、逗号和空格"""
    return re.sub(r'([》>])([、，\s]+)([《<])', r'\1\3', line)

def rule3_remove_spaces(line: str) -> str:
    """规则3: 删除多余空格，分步骤处理"""

    # 0. 先保护表格行（避免处理表格中的|）
    if line.strip().startswith('|') and '|' in line[1:]:
        return line
    
    # 1. 先处理连续两个半角空格
    while '  ' in line:
        line = line.replace('  ', ' ')

    # 删除指定标点前的空格
    punct_before = '#*<-—!&：:。.；;，,？?！)）》>”"《、（(“'
    line = re.sub(r'([\s　]+)([' + re.escape(punct_before) + r'])', r'\2', line)
    
    # 删除指定标点后面的空格
    punct_after = '-—。.”:：（(《<“'
    line = re.sub(r'([' + re.escape(punct_after) + r'])([\s　]+)', r'\1', line)

    # 处理行首格式
    if line.lstrip().startswith('-') or line.lstrip().startswith('–'):
        # 特殊情况：行首的"-"处理
        line = line.lstrip()  # 先删除所有行首空格
        if not line.startswith('　-') or line.startswith('　–'):  # 如果没有全角空格
            line = '　' + line  # 添加全角空格
        line = line.replace('-', '–', 1)  # 替换第一个"-"为"–"
        if len(line) > 1 and not line[2:3].isspace():  # 如果后面没有空格
            line = line[:2] + ' ' + line[2:]  # 添加半角空格
    else:
        # 普通情况：直接删除行首空格
        line = line.lstrip()
    
    # 删除开引号后（“、‘）紧跟中文前的空格
    line = re.sub(r'([“‘])\s+(?=[\u4e00-\u9fff])', r'\1', line)
    # 删除中文后紧跟闭引号（”、’）前的空格
    line = re.sub(r'(?<=[\u4e00-\u9fff])\s+([”’])', r'\1', line)
    
    # 删除中文与中文、数字间的空格（全角或半角）
    # Step 1: 确保"条"、"章"后有全角空格
    line = re.sub(
        r'([条章])([\s　]+)([\u4e00-\u9fff])',
        lambda m: m.group(1) + '　' + m.group(3),
        line
    )

    # Step 2: 删除其他中文间的空格（但保留"条"、"章"后的空格）
    line = re.sub(
        r'([\u4e00-\u9fff])([\s　]+)([\u4e00-\u9fff])',
        lambda m: m.group(1) + m.group(3) if not (m.group(1) in {'条', '章'}) else m.group(1) + '　' + m.group(3),
        line
    )

    line = re.sub(r'(\d)[\s　]+([\u4e00-\u9fff])', r'\1\2', line)
    line = re.sub(r'([\u4e00-\u9fff])[\s　]+(\d)', r'\1\2', line)
    line = re.sub(r'(\d)[\s　]+(\d)', r'\1\2', line)
    
    # 处理 "*" 后面与 "【" 之间的空格，以及 "*" 后与字符之间的空格
    line = re.sub(r'\*[\s　]+【', '* 【', line)
    line = re.sub(r'\*[\s　]+([A-Za-z0-9\u4e00-\u9fff])', r'*\1', line)
    line = re.sub(r'\*\*\*([^\*]+)\*\*', '▸ \\1', line)

    return line

def rule4_punctuation_in_english(line: str) -> str:
    """规则4: 如果整行仅包含英文、数字及标点，则全部标点统一为半角"""
    if re.fullmatch(r'^[a-zA-Z0-9\s,.;:?!()"\'“”‘’]+$', line.strip()):
        for cn, en in [('，', ','), ('。', '.'), ('；', ';'), ('：', ':'), ('！', '!'),
                       ('？', '?'), ('（', '('), ('）', ')'), ('“', '"'), ('”', '"'),
                       ('‘', "'"), ('’', "'")]:
            line = line.replace(cn, en)
    return line

def rule5_punctuation_in_numbers(line: str) -> str:
    """
    规则5: 如果一行仅由数字和标点构成，则删除空白后，
    内部（数字间）的标点统一转换为半角，但行尾（最后一个字符）若为标点，
    则转换为全角（依据映射表），以满足数字行末尾用全角的要求。
    """
    allowed_punct = set(list(',.!?;:\'"()[]{}<>‘’“”，。；：！？'))
    if all(ch.isdigit() or ch in allowed_punct or ch.isspace() for ch in line if ch != '\n'):
        line = re.sub(r'\s+', '', line)
        new_chars = []
        length = len(line)
        for idx, ch in enumerate(line):
            if ch in allowed_punct and ch in PUNCT_FULL_TO_HALF:
                if idx == length - 1:
                    new_chars.append(PUNCT_HALF_TO_FULL.get(ch, ch))
                else:
                    new_chars.append(PUNCT_FULL_TO_HALF.get(ch, ch))
            else:
                new_chars.append(ch)
        return ''.join(new_chars)
    return line

def rule6_chinese_punctuation(line: str) -> str:
    """规则6: 针对包含中文的行处理标点及特殊符号"""
    if not contains_chinese(line):
        return line


    # 将常见标点转换为全角
    punct_map = {
        ',': '，', '.': '。', ';': '；', ':': '：',
        '--': '—', '!': '！', '?': '？', '(': '（', ')': '）',
        '"': '“', "'": '‘'
    }
    line = ''.join(punct_map.get(ch, ch) for ch in line)

    # 重复的逗号或句号只保留一个
    line = re.sub(r'([，。：>])\1+', r'\1', line)

    # 中文字符之间的连接符统一为—（两边无空格）
    line = re.sub(r'([\u4e00-\u9fff])[-－—]+([\u4e00-\u9fff])', r'\1—\2', line)

    # 数字或英文之间的标点（逗号、句号、分号、冒号）若为全角则转换为半角
    pattern = r'([A-Za-z0-9]+)([，。；：])([A-Za-z0-9]+)'
    while re.search(pattern, line):
        line = re.sub(pattern, lambda m: f"{m.group(1)}{PUNCT_FULL_TO_HALF.get(m.group(2), m.group(2))}{m.group(3)}", line)

    # 调整引号配对：第一个遇到的引号为左引号，第二个为右引号，以此循环
    line = fix_quotes(line)

    # 括号、引号、书名号内内容若不含中文，则内部标点替换为半角
    line = process_punctuation_in_brackets(line)

    # 连续三点或更多点统一替换为“……”
    line = re.sub(r'\.{3,}|。{3,}|…{2,}', '……', line)

    # 规则1：1-3位数字开头+标点（非.）+中英文 → 数字后改为.
    line = re.sub(
        r'^(\d{1,3})([，、,．。]+)([a-zA-Z\u4e00-\u9fff])',
        lambda m: f"{m.group(1)}.{m.group(3)}",
        line
    )
    
    # 规则2："第一"、"第二"等开头+标点（非，）+中英文 → 改为，
    line = re.sub(
        r'^(第[一二三四五六七八九十]+)([、,\.．。]+)([a-zA-Z\u4e00-\u9fff])',
        lambda m: f"{m.group(1)}，{m.group(3)}",
        line
    )
    
    # 规则3："一"、"二"等单字开头+标点（非、）+中英文 → 改为、
    line = re.sub(
        r'^([一二三四五六七八九十]+)([，,\.．。]+)([a-zA-Z\u4e00-\u9fff])',
        lambda m: f"{m.group(1)}、{m.group(3)}",
        line
    )

    # 新增规则4：把”“替换成”、“
    line = re.sub(r'”“', '”、“', line)
    line = re.sub(r"GDP:", "GDP：", line)
    line = re.sub(r"▸\*\*", "▸ **", line)

    return line

def rule7_time_format(line: str) -> str:
    """规则7: 处理时间格式为 HH:MM（补零），并统一时间范围连接符为—"""
    line = re.sub(r'(\d{1,2}):(00|15|30|45)', lambda m: f"{int(m.group(1)):02d}:{m.group(2)}", line)
    line = re.sub(r'(\d{2}:\d{2})\s*[-一—–]+\s*(\d{2}:\d{2})', r'\1—\2', line)
    return line

def rule8_number_range(line: str) -> str:
    """规则8: 数字范围处理，若两数字位数相同，则统一连接符为—"""
    def repl(match):
        num1, conn, num2 = match.group(1), match.group(2), match.group(3)
        return f"{num1}—{num2}" if len(num1) == len(num2) else match.group(0)
    line = re.sub(r'(\d+)\s*([-－—])\s*(\d+)', repl, line)
    return line

def rule9_date_range(line: str) -> str:
    """规则9: 日期范围处理，统一连接符为—"""
    def repl(m):
        part1 = m.group(1).strip()
        part2 = m.group(2).strip()
        if part1 and part2:
            return f"{part1}—{part2}"
        return m.group(0)
    return RE_DATE_RANGE.sub(repl, line)

def rule10_phone_number(line: str) -> str:
    """规则10: 电话号码格式化，区号与主号码间统一使用短横线 -（两边无空格）"""
    return re.sub(r'(0\d{2,3})\s*[-一—–]+\s*(\d{7,8})', r'\1–\2', line)

def rule11_heading_spaces(line: str) -> str:
    """规则11: 行首标题（#级）后保留一个半角空格，其余空格删除"""
    if line.startswith('#'):
        level = 0
        while level < len(line) and line[level] == '#':
            level += 1
        content = line[level:].lstrip()
        return f"{'#' * level} {content}"
    return line

def rule12_trailing_spaces(line: str) -> str:
    """
    规则12: 每行末尾保留两个半角空格后换行；
    如果行尾已有换行符，则仅保证末尾有两个半角空格（不会插入多余换行）。
    """
    line = line.rstrip('\n')
    if line:
        line = line.rstrip() + '  \n'
    return line

def rule13_convert_punctuation(line: str) -> str:
    def replace_specific_punctuation(match):
        # 仅对前后的标点进行替换
        parts = []
        for i in range(1, len(match.groups()) + 1):
            part = match.group(i)
            if part and part in PUNCT_HALF_TO_FULL:
                parts.append(PUNCT_HALF_TO_FULL[part])
            else:
                parts.append(part)
        return ''.join(parts)

    # 替换电话号码前后的标点
    line = re.sub(r'([,.;]?)(0\d{2,3}–\d{7,8})([,.;]?)', replace_specific_punctuation, line)
    # 替换手机号码前后的标点
    line = re.sub(r'([,.;]?)(1\d{10})([,.;]?)', replace_specific_punctuation, line)
    # 替换时间前后的标点
    line = re.sub(r'([,.;]?)(\d{2}:\d{2})([,.;]?)', replace_specific_punctuation, line)

    # 统计 | 的数量
    pipe_count = line.count('|')
    if pipe_count == 1:
        line = re.sub(r'\s*\|\s*', '｜', line)
    elif pipe_count > 1:
        # 处理多于一条 | 的行，把 |+数字。 改成 |+数字.
        line = re.sub(r'(\| *)(\d+)。', r'\1\2.', line)
    return line

def process_consecutive_empty_lines(lines: List[str]) -> List[str]:
    """规则13: 多余的连续空行合并为一行空行，删除空行中所有空格"""
    processed = []
    prev_empty = False
    for line in lines:
        if not line.strip():
            if not prev_empty:
                processed.append('\n')
                prev_empty = True
        else:
            processed.append(line)
            prev_empty = False
    return processed

# ---------------- 辅助函数 ----------------

def contains_chinese(text: str) -> bool:
    """判断字符串中是否包含中文字符"""
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

def fix_quotes(line: str) -> str:
    """
    简单处理引号配对：遇到的第一个引号转换为左引号，第二个为右引号，
    以此循环，确保例如 …名城”  专项督察… 经处理后成为 …名城“专项督察…。
    """
    quote_chars = ['"', '“', '”']
    result = []
    open_quote = True
    for ch in line:
        if ch in quote_chars:
            result.append('“' if open_quote else '”')
            open_quote = not open_quote
        else:
            result.append(ch)
    return ''.join(result)

def process_punctuation_in_brackets(line: str) -> str:
    """
    处理括号、引号、书名号内非中文内容的标点替换为半角，
    同时保持括号、引号、书名号本身不变。
    """
    bracket_pairs = [
        ('（', '）'), ('(', ')'),
        ('“', '”'), ('"', '"'),
        ('《', '》'), ('<', '>')
    ]
    for left, right in bracket_pairs:
        pattern = re.compile(f'{re.escape(left)}(.*?){re.escape(right)}')
        def replacer(m):
            content = m.group(1)
            if not contains_chinese(content):
                for full, half in PUNCT_FULL_TO_HALF.items():
                    content = content.replace(full, half)
            return f"{left}{content}{right}"
        line = pattern.sub(replacer, line)
    return line




# ---------------- 主入口 ----------------

if __name__ == '__main__':
    current_dir = os.getcwd()
    process_markdown_files(current_dir)
    print("Markdown 文件处理完成！")
