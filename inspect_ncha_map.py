import urllib.request, re
url='http://www.ncha.gov.cn/col/col2266/index.html'
html=urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=20).read().decode('utf-8','ignore')
items=['中国世界文化遗产名录','全国重点文物保护单位','国家历史文化名城名录','国家历史文化名镇名录','国家历史文化名村名录','中国历史文化街区名录']
for item in items:
    idx=html.find(item)
    print('ITEM', item, 'idx', idx)
    if idx!=-1:
        start=max(0, idx-800)
        end=min(len(html), idx+2500)
        print(html[start:end])
        print('---')
