import urllib.request, re, json
url='http://www.ncha.gov.cn/col/col2266/index.html'
req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
html=urllib.request.urlopen(req, timeout=20).read().decode('utf-8','ignore')
print('len', len(html))
for pat in [r'FormSearch0', r'module/search/index.jsp', r'field_1433', r'全国重点文物保护单位', r'name="field_\d+"', r'field_1433']:
    print(pat, bool(re.search(pat, html)))
print('--- snippet ---')
for m in re.finditer(r'FormSearch0', html):
    start=max(0, m.start()-600)
    end=min(len(html), m.end()+1800)
    print(html[start:end])
    print('====')
    break
