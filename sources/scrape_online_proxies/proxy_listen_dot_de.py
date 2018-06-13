"""
scrape https, socks4, and socks5 proxies from https://www.proxy-listen.de/Proxy/Proxyliste.html
in same format / api as this file (parse() function), can create scrapers for other websites which list proxies
"""


from requests import request
from lxml import html
import proxy
import re

from globals import global_req_timeout


class Proxy:
    def __init__(self, ip, port, reaction_time, online_percent, proxy_type, is_gateway=None):
        self.ip = ip
        self.port = port
        self.reaction_time = reaction_time
        self.online_percent = online_percent
        if 'http' in proxy_type:
            self.proxy_type = 'http'
        else:
            self.proxy_type = proxy_type
        self.is_gateway = is_gateway
        self.proxy_url = self.proxy_type + "://" + ip + ":" + port

    def __str__(self):
        return self.proxy_url + " react time: " + self.reaction_time + " online: " + self.online_percent


def parse_html_tree(tree, proxy_type):
    result_list = []
    if 'socks' in proxy_type:
        for html_element in tree:
            children = html_element.getchildren()
            if len(children) != 7:
                raise Exception('unexpected count of children html elements')
            ip_address = children[0].text_content()
            port = children[1].text_content()
            response_time = children[2].text_content()
            alive_percent = children[4].text_content()
            result_list.append(Proxy(ip_address, port, response_time, alive_percent, proxy_type))
    # http proxy
    else:
        for html_element in tree:
            children = html_element.getchildren()
            if len(children) != 10:
                raise Exception('unexpected count of children html elements')
            ip_address = children[0].text_content()
            port = children[1].text_content()
            response_time = children[4].text_content()
            alive_percent = children[6].text_content()
            result_list.append(Proxy(ip_address, port, response_time, alive_percent, proxy_type))
    return result_list


def get_proxy_list_from_response(response_text, proxy_type, *xpath_selectors):
    html_parsed = html.fromstring(response_text)
    xpath_elements = []
    for xpath_selector in xpath_selectors:
        xpath_elements.extend(html_parsed.xpath(xpath_selector))
    return parse_html_tree(xpath_elements, proxy_type)


def extract_hidden_post_data():
    # get secret post data
    r = request('get', 'https://www.proxy-listen.de/Proxy/Proxyliste.html',
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                       'like Gecko) Chrome/67.0.3396.79 Safari/537.36'}, verify=False)
    matches = re.findall(r'<input\s+name="(.+?)"\s+value="(.+?)" .+?"hidden"/>', r.text)
    if len(matches) != 1 or len(matches[0] != 2):
        raise Exception("mismatch in finding hidden post data")
    return matches[0]  # (hidden_post_key, hidden_post_data)


def make_request(proxy_type, next_page, hidden_post_data_tuple):
    custom_headers = {'Origin': 'https://www.proxy-listen.de',
                      'Upgrade-Insecure-Requests': '1',
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,'
                                '*/*;q=0.8',
                      'Referer': 'https://www.proxy-listen.de/Proxy/Proxyliste.html',
                      'Accept-Encoding': 'gzip, deflate, br',
                      'Accept-Language': 'en-US,en',
                      'Cookie': ''}

    post_data = {'filter_country': '',
                 'filter_http_anon': '',
                 'filter_http_gateway': '',
                 'filter_port': '',
                 'filter_response_time_http': '7',
                 'filter_timeouts1': '50',
                 'liststyle': 'info',
                 'proxies': '300'}

    post_data['type'] = proxy_type
    post_data[hidden_post_data_tuple[0]] = hidden_post_data_tuple[1]
    if next_page:
        post_data['submit'] = 'next page'
    else:
        post_data['submit'] = 'Show'

    return request('post', url='https://www.proxy-listen.de/Proxy/Proxyliste.html', headers=custom_headers,
                   data=post_data, verify=False, timeout=global_req_timeout)


def scrape(get_global_proxy_type_list=False):
    hidden_post_data_tuple = extract_hidden_post_data()
    proxy_types = ['https', 'socks4', 'socks5']
    xpath_selectors = ['//*[@class="proxyListOdd"]', '//*[@class="proxyListEven"]']
    scraped_proxy_list = []
    for proxy_type in proxy_types:
        try:
            r = make_request(proxy_type, False, hidden_post_data_tuple)
            scraped_proxy_list.extend(get_proxy_list_from_response(r.text, proxy_type, *xpath_selectors))
        except Exception as e:
            pass

    if get_global_proxy_type_list:
        temp_proxy_list = []
        for curr_proxy in scraped_proxy_list:
            temp_proxy_list.append(proxy.Proxy(ip=curr_proxy.ip, port=curr_proxy.port,
                                               proxy_type=curr_proxy.proxy_type))
        return temp_proxy_list
    return scraped_proxy_list


# for testing
if __name__ == '__main__':
    res = scrape()
    with open('../../data/proxylisten.de.txt', 'w') as f:
        for proxy in res:
            print(proxy)
            f.write('{}\n'.format(proxy.proxy_url))
