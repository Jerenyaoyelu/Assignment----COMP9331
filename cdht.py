# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading
import pickle
blocksize, MSS = 300,300

class dhtNode:
    def __init__(self,id,fir_successor,sec_successor):
        self.peer = id
        self.port = id + 50000
        self.fir_successor = fir_successor
        self.sec_successor = sec_successor
        self.fir_predecessor = None
        self.sec_predecessor = None
        self.noreply_1 = 0
        self.noreply_2 = 0
        self.isAlive = True

    def UDP_Server(self,host):
        LTPsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        LTPsock.bind((host,self.port))
        packet = {}
        next_seq,Seq,Ack = 0,0,0
        while True:
            data, addr = LTPsock.recvfrom(1024)
            packet = pickle.loads(data)
            sending_peer = packet["Peer"]
            if "Ping_request" == packet["flag"]:
                print(f"A ping request message was received from Peer {sending_peer}")
                if self.fir_predecessor is None:
                    self.fir_predecessor = packet["FS"]
                if self.sec_predecessor is None:
                    self.sec_predecessor = packet["SC"]
                response = pickle.dumps({"flag":"Ping_response","Peer":self.peer})
                LTPsock.sendto(response,addr)
            if "Ping_response" == packet["flag"]:
                print(f"A ping response message was received from Peer {sending_peer}")
                if sending_peer == self.fir_successor:
                    self.noreply_1 -= 1
                if sending_peer == self.sec_successor:
                    self.noreply_2 -= 1
            if "FileFound_response" == packet["flag"]:
                print(f"Received a response message from peer {packet['SendingPeer']}, which has the file .")
                f = open("received_file.pdf",'wb')
                print("We now start receiving the file ………")
            if "File_tansferring" == packet["flag"]:
                if packet["data"] == '\0':
                    next_seq, Seq, Ack = 0,0,0
                else:
                    f.write(packet["data"])
                Ack = next_seq
                next_seq += len(packet["data"])
                acknowledgement = pickle.dumps({"flag":"Ack","seq": 0, "ack":Ack, "data":None})
                LTPsock.sendto(acknowledgement,addr)
        LTPsock.close()
    
    def UDP_Client(self,host):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        while True:
            mysock.settimeout(1)
            try:
                toSendPing = pickle.dumps({"flag":"Ping_request","Peer":self.peer,"FS":self.fir_successor,"SC":self.sec_successor})
                mysock.sendto(toSendPing,(host,self.fir_successor + 50000))
                mysock.sendto(toSendPing,(host,self.sec_successor + 50000))
                self.noreply_1 += 1
                self.noreply_2 += 1
            except TimeoutError:
                continue
        mysock.close()
    
    def location(self,filename):
        hashValue = filename % 256
        if self.peer < hashValue <= self.fir_successor:
            return self.fir_successor
        if self.fir_successor < self.peer:
            if self.peer < hashValue <= 255 or hashValue <= self.fir_successor:
                return self.fir_successor 
        return 0

    def TCP_server(self,host):
        serverPort = self.port # change this port number if required
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((host, serverPort))
        serverSocket.listen(1)
        while True:
            connectionSocket, addr = serverSocket.accept()
            command = pickle.loads(connectionSocket.recv(1024))
            if command and "Request_File" == command["flag"]:
                filename = command["File"]
                if self.location(filename) == self.peer:
                    print(f"File {filename} is here.")
                    self.SAWTransFile(host,self.peer,filename,command["RequestingPeer"])
                else:
                    print(f"File {filename} is not here.")
                    message = pickle.dumps({"flag":"Request_File","File":filename,"RequestingPeer":command["RequestingPeer"]})
                    self.ForwardFileRes(host,message)
                    print(f"File request message for {filename} has been sent to my successor.")
            connectionSocket.close()
    #over TCP
    def ForwardFileRes(self,host,message):
        serverName = host
        serverPort = message["RequestingPeer"] + 50000#change this port number if required
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        clientSocket.send(message)
        clientSocket.close()
    #over UDP
    def SAWTransFile(self,host,peer,filename,dest):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        f = open(filename+".pdf",'rb')
        data = f.read(MSS)
        seq, Ack = 0,0
        toSendPacket = {"flag":None,"seq": None, "ack":None, "data":None}
        #send a file found response message to the requesting peer
        pickle_out = pickle.dumps({"flag":"FileFound_response","SendingPeer": peer})
        mysock.sendto(pickle_out,(host,dest + 50000))
        print(f"A response message, destined for peer {dest}, has been sent.")
        print("We now start sending the file ………")
        while data:
            toSendPacket["flag"] = "File_tansferring"
            toSendPacket["seq"] = seq
            toSendPacket["ack"] = Ack
            toSendPacket["data"] = data
            pickle_out = pickle.dumps(toSendPacket)
            mysock.sendto(pickle_out,(host,dest + 50000))
            start = time.time()
            # stop and wait
            while True:
                acknowledge = mysock.recv(1024)
                if acknowledge:
                    break
                else:
                    # timer
                    if time.time()- start > 1:
                        mysock.sendto(pickle_out,(host,dest + 50000))
            seq += len(data)
            data = f.read(MSS)
        # send a data with 0 size to indicate the completion of transfering file
        toSendPacket["flag"] = "File_tansferring"
        toSendPacket["seq"] = seq
        toSendPacket["ack"] = Ack
        toSendPacket["data"] = '\0'
        pickle_out = pickle.dumps(toSendPacket)
        mysock.sendto(pickle_out,(host,dest + 50000))
        print("The file is sent.")
        mysock.close()

    def UsrInput(self,host):
        while True:
            command = input().split()
            if len(command) == 2 and command[0] == "Request":
                filename = command[1]
                if filename >255 or filename<0:
                    print("Requesting file does not exist!")
                message = pickle.dumps({"flag":"Request_File","File":filename,"RequestingPeer":self.id})
                self.ForwardFileRes(host,message)
            elif len(command) == 1 and command[0] == "Quit":
                self.isAlive = False
            else:
                print("Invalid Input!")   

def main():
    host = 'localhost'
    peer = dhtNode(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
    Thred1 = threading.Thread(target=peer.UDP_Server,args=(host,))
    Thred1.start()
    Thred2 = threading.Thread(target=peer.UDP_Client,args=(host,))
    time.sleep(0.5)
    Thred2.start()
if __name__=='__main__':
    main()