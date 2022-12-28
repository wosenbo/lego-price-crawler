import requests
import time
import json
from datetime import datetime

base_url = 'https://www.bricklink.com/'


def search(q):

	start_time = time.time()

	headers = {
		'User-Agent': 'Paw/3.3.0 (Macintosh; OS X/11.6.1) GCDHTTPRequest'
	}

	query = f"q={q}&st=0&cond&type&cat&yf=0&yt=0&loc&reg=0&ca=0&ss&pmt&nmp=0&color=-1&min=0&max=0&minqty=0&nosuperlot=1&incomplete=0&showempty=1&rpp=25&pi=1&ci=0"

	url = f"{base_url}ajax/clone/search/searchproduct.ajax?{query}"

	r = requests.get(url, headers=headers)
	data = r.json()

	print("--- %s seconds ---" % (time.time() - start_time))

	for row in data['result']['typeList']:
		if row['type'] == 'S':
			for item in row['items']:
				if 'idItem' in item:
					detail_url = f"{base_url}v2/catalog/catalogitem.page?S={item['strItemNo']}"
					result = {
						'name': item['strItemName'],
						'new_price': item['mNewMinPrice'],
						'new_qty': item['n4NewQty'],
						'new_sellers': item['n4NewSellerCnt'],
						'url': detail_url
					}
					return result


if __name__ == '__main__':
	result = search('10655')
	print(json.dumps(result))
