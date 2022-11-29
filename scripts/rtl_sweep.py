import socket
import select
import time
import sys
import struct
# from multiprocessing.dummy import Pool as ThreadPool
import threading

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.00001
forward_to = ('127.0.0.1', 1235)

db_limit = -10.0

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            print(e)
            return False

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port):

        self.SET_FREQUENCY = 0x01

        self.top_Freq = {
            "freq" : 400000000,
            "dBm" : "0"
        }

        self.forward = 0

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)


    def main_loop(self):

        self.input_list.append(self.server)

        while 1:
            # time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])


            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()

                    get_args = threading.Thread(target=self.inject, name="Inject")
                    get_args.start()

                    break

                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:

                    # tasks = [self.inject, self.data_f]
                    self.on_recv()

    def inject(self):


        low_freq = 0

        for i in sys.stdin:
            input = (i.split(', '))

            start_freq = input[2]
            step = input[4]
            db = input[6:]

            max_index = db.index(max(db))
            max_value = max(db)
            freq = int(start_freq) + max_index * float(step)


            # print(max_value)


                # print(self.top_Freq["freq"], self.top_Freq["dBm"])

            if float(start_freq) >= low_freq:
                # print(low_freq)
                low_freq = float(start_freq)



                set_freq = str(freq).split(".")[0]
                print(self.top_Freq["freq"], self.top_Freq["dBm"])


                self.send_command(self.SET_FREQUENCY, int(self.top_Freq["freq"]))

                self.top_Freq["dBm"] = str(db_limit)

            if max_value > self.top_Freq["dBm"] :
                self.top_Freq["freq"] = freq
                self.top_Freq["dBm"] = max_value


    def on_accept(self):
        self.forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if self.forward:
            print(clientaddr, "has connected")
            self.input_list.append(clientsock)
            self.input_list.append(self.forward)
            self.channel[clientsock] = self.forward
            self.channel[self.forward] = clientsock
        else:
            print("Can't establish connection with remote server.",)
            print("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        print(self.s.getpeername(), "has disconnected")
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):

        # data = self.data
        # here we can parse and/or modify the data before send forward
        # print("[*] on_recv data")
        # print(self.data)
        self.channel[self.s].send(self.data)

    def send_command(self, command, param):

        # print("cmd")
        cmd = struct.pack(">BI", command, param)
        # print(cmd)

        self.forward.send(cmd)



if __name__ == '__main__':
        server = TheServer('127.0.0.1', 1236)
        try:
            server.main_loop()
        except KeyboardInterrupt:
            print("Ctrl C - Stopping server")
            sys.exit(1)