from lxml import html
import requests


URL = 'https://whitepark.ru'
LIST_URLS = ["/catalog/ryukzaki/",
                    "/catalog/obuv/",
                    "/catalog/odezhda/",
                    "/catalog/snou/",
                    "/catalog/skeyt/",
                    "/catalog/aksessuary/"]

def pars_shop(name_item):
    for url_catalog in LIST_URLS:
        r = requests.get(URL + url_catalog + '?PAGEN_1=1&pp=1000')
        tree = html.fromstring(r.text)
        items_list_lxml = tree.xpath('.//div[@class="grid catalog_grid"]')[0]
        for item in items_list_lxml:
            if name_item == str(item.xpath('.//footer[@class="goods_desc"]/a/text()')[0]):
                url_item = str(item.xpath('.//footer[@class="goods_desc"]/a/@href')[0])
                resp = requests.get(URL + url_item)
                tree_item = html.fromstring(resp.text)
                return list(set(tree_item.xpath('.//div[@class="wrapper__radiobutton_size"]/label/div/text()')))










