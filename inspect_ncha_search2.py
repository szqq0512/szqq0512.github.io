import urllib.request, urllib.parse, re

url='http://www.ncha.gov.cn/module/search/index.jsp'
params={
    'i_columnid':'2273',
    'field':'field_1433:1',
    'currentplace':'',
    'splitflag':'',
    'fullpath':'0',
    'field_1433':'云南省',
    'download':'查询',
    'keyword':'丽江古城',
}
data=urllib.parse.urlencode(params).encode()
req=urllib.request.Request(url, data=data, headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/x-www-form-urlencoded'})
html=urllib.request.urlopen(req, timeout=30).read().decode('utf-8','ignore')
print('len', len(html))
for marker in ['丽江', '古城', '共', '记录', '第', '批', '文物', 'title', 'href', 'field']:
    print(marker, html.lower().find(marker.lower()))
print(html[:6000])
