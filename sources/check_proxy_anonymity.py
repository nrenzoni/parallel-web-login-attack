import threading
import time
import sources.proxy as proxy
import sources.misc as misc
from sources.queue_list_functions import generate_list_from_file

begin_time = time.time()


# check if proxy uses 'X-Forwarded-For' HTTP header
def check_proxy(proxy_list: list):
    while proxy_list:
        next_proxy = proxy_list.pop(0)
        try:
            p = proxy.parse_proxy_from_str(next_proxy)
            r = p.make_req('get', 'http://api.ipify.org')
            print('proxy: {:<15} detected with ip of {:<15}'.format(p.ip, r.text))
            # alive_proxies_list.append(next_proxy)
            # print('[+]', next_proxy)
        except Exception as e:
            pass
            # dead_proxies_list.append(next_proxy)
            # print('[-]', next_proxy)


def print_proxy_check_stats():
    pass
    # print('proxy check stats:\n'
    #       '  alive proxies: {}, dead proxies: {}\n'
    #       '  average rate: {:.1f} proxies / second\n'
    #       '  total runtime: {:.1f} seconds'
    #       .format(len(alive_proxies_list),
    #               len(dead_proxies_list),
    #               (len(alive_proxies_list) + len(dead_proxies_list)) / (time.time() - begin_time),
    #               time.time() - begin_time))


def main():
    proxy_list = generate_list_from_file('../data/proxylisten.de.txt')
    threads = []

    print('[*]', 'starting proxy checker')

    for i in range(5):
        t = threading.Thread(target=check_proxy, args=(proxy_list,))
        threads.append(t)
        t.start()

    while True:
        time.sleep(5)
        if misc.all_threads_still_running(threads):
            print_proxy_check_stats()
        else:
            break

    print_proxy_check_stats()


if __name__ == '__main__':
    main()
