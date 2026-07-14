import urllib.request, re, json
from pathlib import Path
url='http://www.ncha.gov.cn/col/col2266/index.html'
req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
html=urllib.request.urlopen(req, timeout=20).read().decode('utf-8','ignore')
print('len', len(html))
print('i_columnid', re.findall(r'i_columnid', html)[:10])
print('field_1433', re.findall(r'field_1433', html)[:10])
print('li items')
for m in re.finditer(r'<li[^>]*>([^<]+)</li>', html):
    txt=m.group(1).strip()
    if txt:
        print(txt)
print('--- form snippets ---')
for m in re.finditer(r'<form[^>]*name="FormSearch0"[^>]*>(.*?)</form>', html, re.S):
    text=m.group(1)
    print(text[:2000])
    print('====')
    break
print('--- all hidden values ---')
for m in re.finditer(r'<input[^>]+name=["\']([^"\']+)["\'][^>]+value=["\']([^"\']*)["\']', html):
    print(m.group(1), '=', m.group(2))
