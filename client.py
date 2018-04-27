import argparse
import xmlrpc.client
import os


class Client:
    def __init__(self, host, port, name):
        self.con = xmlrpc.client.ServerProxy('http://' + host + ':' + port, allow_none=True)
        self.id = name

    @staticmethod
    def store_log(log):
        if os.path.isfile('client_log.txt'):
            with open('client_log.txt', 'a+') as f:
                f.write(str(log) + '\n')
        else:
            with open('client_log.txt', 'w') as f:
                f.write(str(log) + '\n')


class Reader(Client):
    def run(self):
        rv = self.con.read(self.id)
        if rv:
            self.store_log(rv)


class Writer(Client):
    def run(self, new):
        rv = self.con.write(self.id, new)
        if rv:
            self.store_log(rv)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Rpc Client.')
    parser.add_argument(
        '-t', '--type',
        type=str,
        required=True,
        choices=['reader', 'writer'],
        help='Client type should be either reader or writer.'
    )
    parser.add_argument(
        '--host',
        type=str,
        help='Server Ip address.',
        required=True
    )
    parser.add_argument(
        '-p', '--port',
        type=str,
        required=True,
        help='Server port number.'
    )
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='Client id.'
    )
    parser.add_argument(
        '-w', '--write',
        type=str,
        default='',
        help='String required to be written in the server file.'
    )
    args = parser.parse_args()
    if args.type == "reader":
        Reader(args.host, args.port, args.id).run()
    else:
        Writer(args.host, args.port, args.id).run(args.write)
