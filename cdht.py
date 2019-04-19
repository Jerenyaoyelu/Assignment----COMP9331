# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading
import pickle
from random import randint
blocksize, MSS = int(sys.argv[4]),int(sys.argv[4])

class dhtNode:
    def __init__(self,id,fir_successor,sec_successor):
        self.peer = id
        self.port = id + 50000
        self.fir_successor = fir_successor
        self.sec_successor = sec_successor
        self.fir_predecessor = None
        self.sec_predecessor = None
        self.isAlive = True

    def UDP_Server(self,host):
        LTPsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        LTPsock.bind((host,self.port))
        packet = {}
        next_seq,Ack = 0,1
        while self.isAlive:
            data, addr = LTPsock.recvfrom(1024)
            packet = pickle.loads(data)
            if "Ping_request" == packet["flag"]:
                print(f"A ping request message was received from Peer {packet['Peer']}")
                if self.peer == packet["FS"]:
                    self.fir_predecessor = packet["Peer"]
                if self.peer == packet["SC"]:
                    self.sec_predecessor = packet["Peer"]
                response = pickle.dumps({"flag":"Ping_response","seq": packet["seq"],"Peer":self.peer})
                LTPsock.sendto(response,addr)
            if "FileFound_response" == packet["flag"]:
                start = time.time()
                receiver = open("response_log.txt","w+")
                print(f"Received a response message from peer {packet['SendingPeer']}, which has the file .")
                f = open("received_file.pdf",'wb')
                print("We now start receiving the file ………")
            if "File_tansferring" == packet["flag"]:
                log = "rcv"+" "*20 + str(time.time()-start) + " "*20 + str(Ack)+ " "*20 +str(MSS) + " "*20+ str(next_seq) + "\n"
                receiver.write(log)
                Ack += len(packet["data"])
                acknowledgement = pickle.dumps({"flag":"Ack","seq": 0, "ack":Ack, "data":None})
                LTPsock.sendto(acknowledgement,addr)
                log = "snd"+" "*20 + str(time.time()-start) + " "*20 + str(next_seq) + " "*20 +str(MSS)+ " "*20 + str(Ack) + "\n"
                receiver.write(log)
                if packet["data"] == '\0':
                    receiver.close()
                    f.close()
                    print("The file is received.")
                    continue
                f.write(packet["data"])
        LTPsock.close()
    
    def UDP_Client(self,host):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #make sure all the servers are ready
        mysock.settimeout(1)
        seq = 0
        recvd_seq1 = 0
        recvd_seq2 = 0
        isFirAlive = True
        isSecAlive = True
        while self.isAlive:
            try:
                toSendPing = pickle.dumps({"flag":"Ping_request","seq":seq,"Peer":self.peer,"FS":self.fir_successor,"SC":self.sec_successor})
                mysock.sendto(toSendPing,(host,self.fir_successor + 50000))
                # because send ping twice, so I need to receive response twice
                # The reason I didnt get all response before is because of not being aware of this!!
                ready = select.select([mysock], [], [], 1)
                if ready[0]:
                    response = pickle.loads(mysock.recv(1024))
                    print(f"A ping response message was received from Peer {response['Peer']}")
                    if response["Peer"] == self.fir_successor:
                        recvd_seq1 = max(recvd_seq1, response["seq"])
                    if response["Peer"] == self.sec_successor:
                        recvd_seq2 = max(recvd_seq2 ,response["seq"])
                mysock.sendto(toSendPing,(host,self.sec_successor + 50000))
                ready = select.select([mysock], [], [], 1)
                if ready[0]:
                    response = pickle.loads(mysock.recv(1024))
                    print(f"A ping response message was received from Peer {response['Peer']}")
                    if response["Peer"] == self.fir_successor:
                        recvd_seq1 = max(recvd_seq1, response["seq"])
                    if response["Peer"] == self.sec_successor:
                        recvd_seq2 = max(recvd_seq2 ,response["seq"])
                if seq - recvd_seq1 >= 4:
                    # avoid printing duplicately
                    # avoid sending message to a dead peer which leads to an "connection refused" error
                    if isFirAlive:
                        print(f"Peer {self.fir_successor} is no longer alive.")
                        deadPeer = self.fir_successor
                        message = pickle.dumps({"flag":"Request_successor","Peer":self.peer,"KilledPeer":deadPeer})
                        # mysock.sendto(message,(host,self.sec_successor + 50000))
                        self.ForwardFileRes(host,message,self.sec_successor)
                        isFirAlive = False
                if seq - recvd_seq2 >= 4:
                    if isSecAlive:
                        print(f"Peer {self.sec_successor} is no longer alive.")
                        deadPeer = self.sec_successor
                        message = pickle.dumps({"flag":"Request_successor","Peer":self.peer,"KilledPeer":deadPeer})
                        # mysock.sendto(message,(host,self.fir_successor + 50000))
                        self.ForwardFileRes(host,message,self.fir_successor)
                        isSecAlive = False
                seq += 1
                time.sleep(10)
            except TimeoutError:
                continue
        mysock.close()
    def myHash(self,filename):
        return filename % 256

    def location(self,filename):
        hashValue = self.myHash(filename)
        if self.peer < hashValue <= self.fir_successor:
            return self.fir_successor
        if self.fir_successor < self.peer:
            if self.peer < hashValue <= 255 or hashValue <= self.fir_successor:
                return self.fir_successor 
        return -1

    def TCP_server(self,host):
        serverPort = self.port # change this port number if required
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((host, serverPort))
        serverSocket.listen(1)
        while True:
            connectionSocket, addr = serverSocket.accept()
            command = pickle.loads(connectionSocket.recv(1024))
            if command:
                if "Request_File" == command["flag"]:
                    vPeer = command["visitedPeer"]
                    if self.peer not in vPeer and self.peer != command["RequestingPeer"]:
                        vPeer.append(self.peer)
                        filename = command["File"]
                        loca = command["location"]
                        # update location of file in the message
                        if loca == -1 and self.location(filename) > -1:
                            loca = self.location(filename)
                        if loca == self.peer:
                            print(f"File {filename} is here.")
                            self.SAWTransFile(host,self.peer,filename,command["RequestingPeer"])
                        else:
                            print(f"File {filename} is not here.")
                            message = pickle.dumps({"flag":"Request_File","File":filename,"RequestingPeer":command["RequestingPeer"],"location":loca,"visitedPeer":vPeer})
                            self.ForwardFileRes(host,message,self.fir_successor)
                            # self.ForwardFileRes(host,message,self.sec_successor)
                            print(f"File request message for {filename} has been sent to my successor.")
                elif "Quit" == command["flag"]:
                    if self.peer != command['QuitingPeer']:
                        print(f"Peer {command['QuitingPeer']} will depart from the network.")
                        if self.fir_successor == command['QuitingPeer']:
                            self.fir_successor = command['FS']
                            print(f"My first successor is now peer {command['FS']}.")
                            self.sec_successor = command["SC"]
                            print(f"My first successor is now peer {command['SC']}.")
                        if self.sec_successor == command['QuitingPeer']:
                            self.sec_successor = command["FS"]
                            print(f"My first successor is now peer {self.fir_successor}.")
                            print(f"My first successor is now peer {command['FS']}.")
                elif "Request_successor" == command["flag"]:
                    raw_message = {"flag":"Response_successor","Peer":self.peer,"KilledPeer":command["KilledPeer"],"FS":self.fir_successor,"SC":self.sec_successor}
                    message = pickle.dumps(raw_message)
                    self.ForwardFileRes(host,message,command["Peer"])
                else:
                    if self.fir_successor == command['KilledPeer']:
                        self.fir_successor = self.sec_successor
                        print(f"My first successor is now peer {self.fir_successor}.")
                        self.sec_successor = command['FS']
                        print(f"My second successor is now peer {self.sec_successor}.")
                    if self.sec_successor == command['KilledPeer']:
                        print(f"My first successor is now peer {self.fir_successor}.")
                        if command["KilledPeer"] == command["FS"]:
                            self.sec_successor = command["SC"]
                        else:
                            self.sec_successor = command["FS"]
                        print(f"My second successor is now peer {self.sec_successor}.")
            connectionSocket.close()
    #over TCP
    def ForwardFileRes(self,host,message,dest):
        serverName = host
        serverPort = dest + 50000#change this port number if required
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        clientSocket.send(message)
        clientSocket.close()

    #over UDP
    def SAWTransFile(self,host,peer,filename,dest):
        drop_rate = float(sys.argv[5])
        sender = open("requesting_log.txt","w+")
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        f = open(str(filename)+".pdf",'rb')
        data = f.read(MSS)
        seq, Ack = 0,0
        toSendPacket = {"flag":None,"seq": None, "ack":None, "data":None}
        #send a file found response message to the requesting peer
        pickle_out = pickle.dumps({"flag":"FileFound_response","SendingPeer": peer})
        mysock.sendto(pickle_out,(host,dest + 50000))
        seq += 1
        print(f"A response message, destined for peer {dest}, has been sent.")
        print("We now start sending the file ………")
        while data:
            start = time.time()
            toSendPacket["flag"] = "File_tansferring"
            toSendPacket["seq"] = seq
            toSendPacket["ack"] = Ack
            toSendPacket["data"] = data
            pickle_out = pickle.dumps(toSendPacket)
            drop = randint(0,1)
            #simulate packet dropping
            if drop >= drop_rate:
                mysock.sendto(pickle_out,(host,dest + 50000))
                log = "snd"+" "*20 + str(time.time()) + " "*20 + str(seq) + " "*20 +str(MSS)+ " "*20 + str(Ack) + "\n"
                sender.write(log)
            else:
                log = "Drop"+" "*19 + str(time.time()) + " "*20 + str(seq) + " "*20 +str(MSS) + " "*20+ str(Ack)+ "\n"
                sender.write(log)
                time.sleep(1)
                if drop >= drop_rate:
                    mysock.sendto(pickle_out,(host,dest + 50000))
                    log = "RTX"+" "*20 + str(time.time()) + " "*20 + str(seq) + " "*20 +str(MSS) + " "*20+ str(Ack)+ "\n"
                    sender.write(log)
                else:
                    log = "RTX/Drop"+" "*15 + str(time.time()) + " "*20 + str(seq) + " "*20 +str(MSS) + " "*20+ str(Ack)+ "\n"
                    sender.write(log)
                    mysock.sendto(pickle_out,(host,dest + 50000))
            # stop and wait
            while True:
                acknowledge = mysock.recv(1024)
                if acknowledge:
                    log = "rcv"+" "*20 + str(time.time()) + " "*20 + str(Ack) + " "*20 +str(MSS) + " "*20+ str(seq)+ "\n"
                    sender.write(log)
                    break
                else:
                    if time.time()- start > 1:
                        mysock.sendto(pickle_out,(host,dest + 50000))
                        log = "RTX"+" "*20 + str(time.time()) + " "*20 + str(seq) + " "*20 +str(MSS) + " "*20+ str(Ack)+ "\n"
                        sender.write(log)
                        break
            seq += len(data)
            data = f.read(MSS)
        sender.close()
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
            loca = -1
            if len(command) == 2 and command[0] == "Request":
                filename = int(command[1])
                if self.myHash(filename) >255 or self.myHash(filename)<0:
                    print("Requesting file does not exist!")
                if self.peer > self.fir_successor:
                    loca = self.location(filename)
                message = pickle.dumps({"flag":"Request_File","File":filename,"RequestingPeer":self.peer, "location":loca,"visitedPeer":[]})
                self.ForwardFileRes(host,message,self.fir_successor)
                # self.ForwardFileRes(host,message,self.sec_successor)
            elif len(command) == 1 and command[0] == "Quit":
                self.isAlive = False
                message = pickle.dumps({"flag":"Quit","QuitingPeer":self.peer, "FS":self.fir_successor, "SC":self.sec_successor})
                self.ForwardFileRes(host,message,self.fir_predecessor)
                self.ForwardFileRes(host,message,self.sec_predecessor)
            else:
                print("Invalid Input!")

def main():
    host = 'localhost'
    peer = dhtNode(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
    Thred1 = threading.Thread(target=peer.UDP_Server,args=(host,))
    Thred2 = threading.Thread(target=peer.UDP_Client,args=(host,))
    Thred3 = threading.Thread(target=peer.TCP_server, args=(host,))
    Thred4 = threading.Thread(target=peer.UsrInput, args=(host,))
    
    Thred1.start()
    Thred2.start()
    Thred3.start()
    Thred4.start()
if __name__=='__main__':
    main()