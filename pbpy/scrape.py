import requests
import lxml.html as lh

def get_table(url) -> list:
    return lh.fromstring(requests.get(url).content).xpath('//tr')
