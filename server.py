import argparse
from xmlrpc.server import SimpleXMLRPCServer
from sys import exit
from threading import Lock
import os


class Server(object):
    dataLock = Lock()
    sn_lock = Lock()
    rn_lock = Lock()
    reader_log_lock = Lock()
    writer_log_lock = Lock()
    sn = 0
    rn = 0

    def __init__(self, port, max_access):
        self.history = dict()
        self.max_access = max_access
        self.running = True
        with SimpleXMLRPCServer(("", port)) as server:
            self.sock = server.socket
            server.register_introspection_functions()
            server.register_function(self.read)
            server.register_function(self.write)
            print('Server started on localhost on port:', port)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received, exiting.")
                exit(0)

    def read(self, name):
        if self.add_reader(name):
            rn = self.increment_rn()
            data = self.read_file()
            sn = self.increment_sn()
            self.store_reader_log(sn, data, name, rn)
            return rn, sn, data
        return False

    def write(self, name, new):
        if self.add_writer(name):
            rn = self.increment_rn()
            self.write_file(new)
            sn = self.increment_sn()
            self.store_writer_log(sn, new, name, rn)
            return rn, sn
        return False

    @staticmethod
    def read_file():
        with open('news.txt', "r") as f:
            return f.read()

    @staticmethod
    def write_file(new):
        with open('news.txt', "w") as f:
            return f.write(new)

    def increment_sn(self):
        with self.sn_lock:
            n = self.sn
            self.sn += 1
            return n

    def increment_rn(self):
        with self.rn_lock:
            n = self.rn
            self.rn += 1
            return n

    def store_reader_log(self, sn, val, name, rn):
        with self.reader_log_lock:
            if os.path.exists('server_reader_log.txt'):
                with open('server_reader_log.txt', 'a+') as f:
                    f.write(str(sn) + " " + str(val) + " " + str(name) + " " + str(rn) + '\n')
            else:
                with open('server_reader_log.txt', 'w') as f:
                    f.write(str(sn) + " " + str(val) + " " + str(name) + " " + str(rn) + '\n')

    def store_writer_log(self, sn, val, name, rn):
        with self.writer_log_lock:
            if os.path.exists('server_writer_log.txt'):
                with open('server_writer_log.txt', 'a+') as f:
                    f.write(str(sn) + " " + str(val) + " " + str(name) + " " + str(rn) + '\n')
            else:
                with open('server_writer_log.txt', 'w') as f:
                    f.write(str(sn) + " " + str(val) + " " + str(name) + " " + str(rn) + '\n')

    def add_reader(self, name):
        if (name, 'read') not in self.history:
            self.history[(name, 'read')] = 1
            return True
        elif self.history.get((name, 'read')) < self.max_access:
            self.history[(name, 'read')] += 1
            return True
        return False

    def add_writer(self, name):
        if (name, 'write') not in self.history:
            self.history[(name, 'write')] = 1
            return True
        elif self.history.get((name, 'write')) < self.max_access:
            self.history[(name, 'write')] += 1
            return True
        return False

    def stop(self):
        self.running = False
        self.sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Rpc Client.')
    parser.add_argument(
        '-p', '--port',
        type=int,
        required=True,
        help='Server port number.'
    )
    parser.add_argument(
        '-m', '--max_access',
        type=int,
        required=True,
        help='Maximum access per client.'
    )
    args = parser.parse_args()
    Server(args.port, args.max_access)
