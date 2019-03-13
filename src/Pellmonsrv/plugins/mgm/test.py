import requests
import xml.etree.ElementTree as et

resp = requests.get('http://localhost:8081/test.xml')

root = et.fromstring(resp.text)

for element in root:
    print element.tag, element.text


