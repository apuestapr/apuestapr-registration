import requests


username = 'apuesta'
password = 'VNS88J0ze0bTC2zv5jmQwexwssn2Q7'

proxy = f'http://{username}:{password}@138.99.36.10:20000'
proxy = {
    'http': proxy,
    'https': proxy
}

response = requests.get('https://eop7nfspmtd1meu.m.pipedream.net', proxies=proxy)

print(response.status_code)
print(response.text)