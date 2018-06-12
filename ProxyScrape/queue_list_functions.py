import _io
from queue import Queue


def generate_list_from_file(file):
    if type(file) == str:
        with open(file) as f:
            lines = (line.strip() for line in f)
            lines = [line for line in lines if line]  # skip blank lines
    elif type(file) == _io.TextIOWrapper:
        lines = (line.strip() for line in file)
        lines = [line for line in lines if line]  # skip blank lines
        file.close()
    else:
        raise Exception('file must be either a filename or file object')
    return lines

def list_to_queue(in_list):
    q = Queue()
    for item in in_list:
        q.put(item)
    return q
