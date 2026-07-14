import urllib.request, urllib.parse, re
from pathlib import Path

url='http://www.ncha.gov.cn/module/search/index.jsp'
for title in ['丽江古城','阿房宫','安阳殷墟','勐旺塔','金沙江岩画']:
    data=urllib.parse.urlencode({
        'i_columnid':'2273',
        'field':'field_1433:1',
        'currentplace':'',
        'splitflag':'',
        'fullpath':'0',
        'field_1433':'云南省',
        'download':'查询',
        'keyword': title,
    }).encode()
    req=urllib.request.Request(url, data=data, headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/x-www-form-urlencoded'})
    html=urllib.request.urlopen(req, timeout=20).read().decode('utf-8','ignore')
    print('TITLE', title)
    print('len', len(html))
    print(html[:4000])
    print('--- matches ---')
    for m in re.finditer(r'([\u4e00-\u9fff]{2,20})', html):
        txt=m.group(1)
        if '批' in txt or '文物' in txt or title in txt:
            print(txt)
            break
    print('====')
