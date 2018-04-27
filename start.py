from configparser import ConfigParser as parser
from threading import Thread
import pty
from os import waitpid, execv, read, write
from time import sleep
import random


class SSH(object):
    """
    Establish a SSH connection to the given host and Authenticate if password is required.
    """
    def __init__(self, host, execute, user, password, askpass=True):
        self.exec_ = execute
        self.host = host
        self.user = user
        self.password = password
        self.ask_pass = askpass

    def run(self):
        command = [
                '/usr/bin/ssh',
                self.user+'@'+self.host,
                '-o', 'NumberOfPasswordPrompts=1',
                self.exec_,
        ]
        pid, child_fd = pty.fork()
        if not pid:
            execv(command[0], command)

        while self.ask_pass:
            try:
                output = read(child_fd, 1024).strip()
            except Exception:
                break
            lower = output.lower()
            if b'password:' in lower:
                write(child_fd, self.password + b'\n')
                print('Logged in successfully')
                break
            elif b'are you sure you want to continue connecting' in lower:
                # Adding key to known_hosts
                write(child_fd, b'yes\n')
            else:
                print('Error:', output)

        output = []
        while True:
            try:
                output.append(read(child_fd, 1024).strip())
            except:
                break

        waitpid(pid, 0)
        output_str = [i.decode() for i in output]
        print(''.join(output_str))


class Robot(object):
    def __init__(self, ssh_host, ssh_user_name, ssh_password):
        self.host = ssh_host
        self.user_name = ssh_user_name
        self.password = ssh_password

    def run_command(self, command):
        ssh = SSH(self.host, execute=command, askpass=True, user=self.user_name, password=self.password.encode())
        ssh.run()


class ServerRobot(Robot):
    def run(self, port, max_access):
        Thread(target=self.run_command, args=("python3 server.py -p " + port + " -m " + max_access, )).start()


class ClientRobot(Robot):
    def __init__(self, client_type, server_host, server_port, ssh_host, ssh_user_name, ssh_password, name,
                 write_val=None):
        super().__init__(ssh_host, ssh_user_name, ssh_password)
        self.client_type = client_type
        self.server_host = server_host
        self.server_port = server_port
        self.write_val = write_val
        self.id = name

    def handle_operations(self, delays):
        command = "python3 client.py --type " + self.client_type + " --host " + self.server_host + \
                  " -p " + self.server_port + " --id " + self.id + " "
        if self.client_type and self.write_val is not None:
            command += " -w " + self.write_val
        self.run_command(command)
        for delay in delays:
            sleep(delay)
            self.run_command(command)

    def run(self, delays):
        Thread(target=self.handle_operations, args=(delays, )).start()


if __name__ == '__main__':
    prop = parser()
    prop.read('system.ini')
    ServerRobot(prop.get('server', 'server_host'), prop.get('server', 'server_username'),
                prop.get('server', 'server_password')).run(prop.get('server', 'server_port'),
                                                           prop.get('server', 'number_of_access'))
    for i in range(int(prop.get('server', 'number_of_readers'))):
        client = 'client'+str(i)
        # Create a new reader client
        ClientRobot('reader', prop.get('server', 'server_host'), prop.get('server', 'server_port'),
                    prop.get('readerClients', client+'_host'), prop.get('readerClients', client+'_username'),
                    prop.get('readerClients', client+'_password'), prop.get('readerClients', client+'_id')).\
            run(delays=random.sample(range(1, 10), int(prop.get('server', 'number_of_access'))))
        # Create a new writer client
        ClientRobot('writer', prop.get('server', 'server_host'), prop.get('server', 'server_port'),
                    prop.get('writerClients', client+'_host'), prop.get('writerClients', client+'_username'),
                    prop.get('writerClients', client+'_password'), prop.get('readerClients', client+'_id'),
                    write_val=str(random.sample(range(1, 10), 1)[0])).\
            run(delays=random.sample(range(1, 10), int(prop.get('server', 'number_of_access'))))
