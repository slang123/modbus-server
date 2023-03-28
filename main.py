import socket
import binascii
import array
import sys
import os
from _thread import *


registers_input = [[0], [0], [0], [0], [0], [2301, 22, 16, 101, 102, 0, 0x5555, 0x6666, 4812], [2301, 22, 16, 101, 102, 0, 0x5555, 0x6666, 4812]]
registers_holding = [[0], [1], [5600, 6000, 1], [6500], [6501], [2301, 101, 102, 4500, 4500, 560, 112], [2301, 101, 102, 4500, 4500, 560, 112]]

ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 502
ThreadCount = 0
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(5)

def modbus_crc16(data):
    crc = 0xFFFF
    for cur_byte in data:
        crc = crc ^ cur_byte
        for _ in range(8):
            a = crc
            carry_flag = a & 0x0001
            crc = crc >> 1
            if carry_flag == 1:
                crc = crc ^ 0xA001
    return bytes([crc % 256,crc >> 8 % 256])

def multi_threaded_client(connection):
    #connection.send(str.encode('Server is working:'))
    while True:
        data = connection.recv(256)
        if not data:
            break
        id = data[0]
        cmd = data[1]
        offs = (data[2] << 8) | data[3]
        nreg = (data[4] << 8) | data[5]

        if cmd == 4:    # Read input registers
            txbytes = bytes([id, cmd, nreg*2])
            # add the data to the package
            n=0
            while n < nreg:
                bytes_val = registers_input[id][n+offs].to_bytes(2, 'big')
                txbytes = txbytes + bytes_val[0].to_bytes(1,'big') + bytes_val[1].to_bytes(1,'big')
                n=n+1
            # Add crc to bytes
            crc = modbus_crc16(txbytes)
            txbytes = txbytes + crc[0].to_bytes(1,'big')+crc[1].to_bytes(1,'big')
            print(txbytes)
            connection.send(txbytes)
        if cmd == 3:  # Read holding registers
            txbytes = bytes([id, cmd, nreg * 2])
            # add the data to the package
            n = 0
            while n < nreg:
                bytes_val = registers_holding[id][n+offs].to_bytes(2, 'big')
                txbytes = txbytes + bytes_val[0].to_bytes(1, 'big') + bytes_val[1].to_bytes(1, 'big')
                n = n + 1
            # Add crc to bytes
            crc = modbus_crc16(txbytes)
            txbytes = txbytes + crc[0].to_bytes(1, 'big') + crc[1].to_bytes(1, 'big')
            print(txbytes)
            connection.send(txbytes)
        if cmd == 6:  # Preset single register
            val = (data[4] << 8) | data[5]
            registers_holding[id][offs] = val
            print(data)
            connection.send(data)
        if cmd == 10:  # Preset multiple registers
            n = 0
            while (n < nreg):
                val = (data[7+(n*2)] << 8) | data[8+(n*2)]
                registers_holding[id][offs+n] = val
                n = n + 1
            txbytes = bytes([id, cmd, data[2], data[3], data[4], data[5]])
            crc = modbus_crc16(txbytes)
            txbytes = txbytes + crc[0].to_bytes(1, 'big') + crc[1].to_bytes(1, 'big')
            print(data)
            connection.send(data)

    print("Closing client")
    connection.close()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("Starting modbusRTU TCP server")
    while True:
        Client, address = ServerSideSocket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(multi_threaded_client, (Client,))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))
    print("Closing socket server")
    ServerSideSocket.close()

