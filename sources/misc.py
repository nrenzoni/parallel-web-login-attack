import threading
import socket
from contextlib import closing
from termcolor import colored


# https://stackoverflow.com/a/35370008
def is_port_open(ip, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(3)
        if sock.connect_ex((ip, int(port))) == 0:  # host:port is open
            return True
        return False


def print_colored(msg, color):
    print(colored(msg, color))


def print_error(msg):
    print_colored('[-] {}'.format(msg), 'red')


def print_stat(msg, color='blue'):
    print_colored('[*] {}'.format(msg), color)


def print_positive(msg):
    print_colored('[+] {}'.format(msg), 'green')


def all_threads_still_running(thread_list):
    for t in thread_list:
        if not t.is_alive():
            return False
    return True


"""An atomic, thread-safe incrementing counter."""
#  https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
class AtomicCounter:
    """An atomic, thread-safe incrementing counter.
    >>> counter = AtomicCounter()
    >>> counter.increment()
    1
    >>> counter.increment(4)
    5
    >>> counter = AtomicCounter(42.5)
    >>> counter.value
    42.5
    >>> counter.increment(0.5)
    43.0
    >>> counter = AtomicCounter()
    >>> def incrementor():
    ...     for i in range(100000):
    ...         counter.increment()
    >>> threads = []
    >>> for i in range(4):
    ...     thread = threading.Thread(target=incrementor)
    ...     thread.start()
    ...     threads.append(thread)
    >>> for thread in threads:
    ...     thread.join()
    >>> counter.value
    400000
    """
    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value += num
            return self.value