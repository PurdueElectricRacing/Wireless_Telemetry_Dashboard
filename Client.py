import socket
import time
import sys
import can
import cantools

host = '10.192.17.199'#'169.254.48.90'
port = 28700#29536

class CanSocket:

    begin_len = len("< frame 7EE 1619064569.797774 ")

    def __init__(self, dbc_file):
        self.sock = socket.socket()
        self.db = cantools.database.load_file(dbc_file)
        self.connected = False
    
    def start_receiving(self, callback):
        while self.connected:
            data = self.receive_decoded()
            #print(data)
            callback(data)
        print("stopped receiving")

    
    def send_command(self, command):
        self.sock.send(command.encode())
        if ('< ok >' not in self.sock.recv(6).decode('utf-8')):
            print("Invalid command")

    def connect(self, address):
        try:
            self.sock.connect(address)
        except socket.gaierror:
            print("Error connecting")
            self.connected = False
            return False
        print("Connected?")
        self.sock.recv(6)
        self.send_command("< open vcan0 >")
        self.send_command("< rawmode >")
        self.connected = True
        return True
    
    def receive_str(self, n):
        msg = self.sock.recv(n).decode('utf-8')
        if(not msg):
            #raise RuntimeError('Connection Broken!')
            print("Connection broken!")
            self.connected = False
            self.sock.close()
        return msg

    def receive_message(self):
        msg = self.receive_str(self.begin_len)
        while(msg[-1] != '>'):
            # keep receiving until end of frame
            # TODO: seems like a slow method...
            msg += self.receive_str(1)
        # parse msg
        # Example: < frame 7EE 1619064569.797774 DEADBEEF >
        #print(msg)
        start_id = 8
        end_id = msg.find(" ", 8)
        start_time = end_id + 1
        end_time = msg.find(" ", start_time)
        start_data = end_time + 1
        end_data = msg.find(" ", start_data)
        id = int(msg[start_id:end_id], base=16)
        time = float(msg[start_time:end_time])
        data = int(msg[start_data: end_data], base=16).to_bytes(int((end_data-start_data)/2), 'big')
        return can.Message(arbitration_id=id, timestamp=time, data=data)
    
    def receive_decoded(self):
        msg = self.receive_message()
        try:
            return self.db.decode_message(msg.arbitration_id, msg.data)
        except BaseException as e:
            print("Frame not in DBC File: ")
            print(e)
            return ""


if __name__ == '__main__':
    cs = CanSocket('per_2021_dbc.dbc')
    cs.connect((host, port))
    while(True):
        #msg = cs.receive_message()
        #print("Frame id: " + str(msg.arbitration_id) + " Data: "+msg.data.hex())
        print(cs.receive_decoded())

