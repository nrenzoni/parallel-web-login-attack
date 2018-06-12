import re

from requests import get, request
from random import shuffle
from sources.globals import global_req_timeout
from sources.misc import is_port_open
from sources.queue_list_functions import generate_list_from_file

user_agent = 'smarty pants 1.0'


def parse_proxy_from_str(in_str, ignore_resolve=False):
    protocol_ip_port_re_match = re.findall(r'(\w+)://([\d.]+):(\d+)', in_str)
    ip_port_re_match = re.findall(r'([\d.]+):([\d]+)', in_str)
    if len(protocol_ip_port_re_match) > 0:
        protocol, ip, port = protocol_ip_port_re_match[0]
        return Proxy(ip=ip, port=port, proxy_type=protocol, ignore_resolve=ignore_resolve)
    elif len(ip_port_re_match) > 0:
        ip, port = ip_port_re_match[0]
        return Proxy(ip=ip, port=port, ignore_resolve=ignore_resolve)
    else:
        print('unable to parse proxy from string: {}'.format(in_str))


def parse_proxy_list_from_file(file, randomize=False, ignore_resolve=False):
    file_line_list = generate_list_from_file(file)
    proxy_list = []
    for line in file_line_list:
        proxy_list.append(parse_proxy_from_str(line, ignore_resolve))
    if randomize:
        shuffle(proxy_list)
    return proxy_list


class Proxy:
    def __init__(self, ip, port, proxy_type=None, ignore_resolve=False):
        self.ip = ip
        self.port = port
        if ignore_resolve:
            if not proxy_type:
                self.proxy_type = 'unresolved'
        elif not proxy_type:  # proxy type not set, and ignore_resolve=False
            self.proxy_type = self.resolve_proxy_type()
        else:
            if proxy_type in ['socks5', 'socks4', 'http']:  # only keeps one proxy type although multiple are
                # possible for same ip:port
                self.proxy_type = proxy_type
            else:
                raise Exception('proxy_type: {} is not valid'.format(proxy_type))
        self.proxy_url = self.proxy_type + '://' + self.ip + ':' + self.port

    def __str__(self):
        return self.proxy_url

    def resolve_proxy_type(self):
        """
        :param ip_host: string of ip:port of proxy. e.g. 100.100.100.100:7777
        :return: string: "http" or "socks4" or "socks5"
        """

        if not is_port_open(self.ip, self.port):
            raise Exception('dead proxy')

        def is_alive(proxy_type):
            try:
                get(url='http://api.ipify.org', proxies={'http': proxy_type + '://' + self.ip + ':' + self.port},
                    timeout=global_req_timeout)
                return True
            except Exception as e:
                return False

        for proxyType in ["socks5", "socks4", "http"]:
            if is_alive(proxyType):
                return proxyType
        raise Exception('proxy type for {}:{} could not be determine'.format(self.ip, self.port))

    def get_proxy_dict(self):
        return {'http': self.proxy_url, 'https': self.proxy_url}

    def make_req(self, req_method, url, params_data: dict=None, extra_header_dict={}):
        """
        raises exception on bad url / request timeout / bad proxy / bad ssl certificate / other reasons?.
        """
        if req_method not in ['post', 'get']:
            raise Exception('bad request method in proxy.make_req()')
        return request(method=req_method,
                       url=url,
                       proxies=self.get_proxy_dict(),
                       data=params_data,
                       headers={'User-Agent': user_agent, **extra_header_dict},
                       timeout=global_req_timeout)
