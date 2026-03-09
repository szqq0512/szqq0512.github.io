import os
import re

def convert_headers_in_file(filepath):
    """处理单个Markdown文件，替换二级和三级标题标记"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 先替换三级标题（避免二级标题干扰）
    new_content = re.sub(r'^### ', '▸ ', content, flags=re.MULTILINE)
    new_content = re.sub(r'^## ', '⏩ ', new_content, flags=re.MULTILINE)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                if convert_headers_in_file(filepath):
                    print(f'已修改: {filepath}')
                    count += 1
    print(f'处理完成，共修改 {count} 个文件。')

if __name__ == '__main__':
    main()