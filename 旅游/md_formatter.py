import os
import re

def full_to_half_char(match):
    """精确转换全角字母、数字和句号为半角（保留其他全角符号）"""
    char = match.group()
    code = ord(char)
    
    # 全角句号（． -> .）
    if code == 0xFF0E:
        return '.'
    # 全角字母（A-Z, a-z）
    elif 0xFF21 <= code <= 0xFF3A:  # 大写字母
        return chr(code - 0xFEE0)
    elif 0xFF41 <= code <= 0xFF5A:  # 小写字母
        return chr(code - 0xFEE0)
    # 全角数字（０-９）
    elif 0xFF10 <= code <= 0xFF19:
        return chr(code - 0xFEE0)
    # 其他字符（包括全角空格）保持原样
    return char

def process_line(line):
    """处理单行文本"""
    # 分离内容主体和换行符
    content_part = line.rstrip('\r\n')
    line_ending = line[len(content_part):]

    # 处理纯空格行：删除空格但保留换行符
    if not content_part.strip():
        return line_ending

    # Step 1: 转换全角字符（字母/数字/句号）
    processed_content = re.sub(r'([０-９Ａ-Ｚａ-ｚ．])', full_to_half_char, content_part)
    
    # Step 2: 移除行尾所有空格（包括全角空格）并添加两个半角空格
    processed_content = processed_content.rstrip(' \t　') + '  '
    
    # Step 3: 替换半角逗号为全角
    processed_content = processed_content.replace(',', '，')

    return processed_content + line_ending

def remove_extra_empty_lines(lines):
    """删除多余空行，保留最多一个连续空行"""
    cleaned = []
    prev_empty = False
    for line in lines:
        current_empty = not line.strip()
        if current_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = current_empty
    return cleaned

def process_file(file_path):
    """处理单个文件"""
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()

    processed_lines = [process_line(line) for line in lines]
    processed_lines = remove_extra_empty_lines(processed_lines)

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(processed_lines)

def main():
    """处理当前目录及其子目录中的所有Markdown文件"""
    root_dir = os.getcwd()
    print(f'Working directory: {root_dir}')
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                print(f'Processing: {path}')
                process_file(path)

if __name__ == '__main__':
    main()