# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading
import pickle
MSS = 300

class dhtNode:
    def __init__(self, host, id, fir_successor, sec_successor):
        self.id = id
        self.host = host
        self.fir_successor = fir_successor
        self.sec_successor = sec_successor
        self.fir_predecessor = None
        self.sec_predecessor = None

    def Listening(self):
        LsnPing = ListenToPing(self.host,self.id+50000)
        LsnPing.start()
        LsnRes = ListenToFileReq(self.host,self.id+50000)
        LsnRes.start()
    
    def Pinging(self):
        SndPingToFS = ReqPing(self.host,self.fir_successor+50000)
        SndPingToFS.start()
        SndPingToSC = ReqPing(self.host,self.sec_successor+50000)
        SndPingToSC.start()


class ListenToPing(threading.Thread):
    def __init__(self,host,port):
        super(ListenToPing,self).__init__()
        self.host = host
        self.port = port
    
    #need to distinguish it is a ping request or a file here
    #download file and reassemble it
    def run(self):
        LTPsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        LTPsock.bind((self.host,self.port))
        f_name = None
        next_seq = 0
        Seq = 0
        Ack = 0
        buffer = {}
        isdone =False
        d = b""
        while True:
            data, addr = LTPsock.recvfrom(1024)
            sending_peer = addr[1] - 50000
            if data:
                if "Ping_request" in pickle.loads(data):
                    print(f"A ping request message was received from Peer {sending_peer}")
                    response = pickle.dumps({"Ping_response":time.ctime()})
                    LTPsock.sendto(response,addr)
                # else:#download and reassemble file
            # print("downloading file")
            
            # # while True:
            # if not data: break
            # d += data
                # chunk = pickle.loads(d)
                # print(data)
                # if isdone:
                #     f_name = None
                #     next_seq = 0
                #     Seq = 0
                #     Ack = 0
                #     buffer = {}
                #     isdone =False
                # if not f_name:
                #     f_name = chunk[2].decode()
                #     f = open("received_"+f_name+".pdf",'wb')
                #     next_seq += len(f_name)
                # if chunk[0] == next_seq:
                #     content = chunk[2] + '\r\n'
                #     f.write(content.encode('utf-8'))
                #     Ack = next_seq
                #     next_seq += len(chunk[2])
                #     if buffer:
                #         while min(list(buffer.keys())) == next_seq:
                #             content = buffer[next_seq] + '\r\n'
                #             f.write(content.encode('utf-8'))
                #             del buffer[next_seq]
                #             Ack = next_seq
                #             next_seq += len(chunk[2])
                # else:
                #     if(len(chunk) == 2):
                #         isdone == True
                #     else:
                #         buffer[chunk[0]]=chunk[2]
                # acknowledgement = str(Seq) + " "+str(Ack) + '\r\n'
                # LTPsock.sendto(acknowledgement.encode("utf-8"),addr)
        c = pickle.loads(d)
        print(c)
        LTPsock.close()

class ReqPing(threading.Thread):
    def __init__(self,host,port):
        super(ReqPing,self).__init__()
        self.host = host
        self.port = port
    
    def run(self):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        while True:
            toSendPing = pickle.dumps({"Ping_request": time.ctime()})
            mysock.sendto(toSendPing,(self.host,self.port))
            recvResponse = pickle.loads(mysock.recv(1024))
            if "Ping_response" in recvResponse:
                print(f"A ping response message was received from Peer {self.port - 50000}")
        mysock.close()

class ReqFile(threading.Thread):
    def __init__(self, host, port, request):
        super(ReqFile,self).__init__()
        self.host = host
        self.port = port
        self.request = request

    def run(self):
        # total = len(sys.argv)
        # cmdargs = str(sys.argv)
        serverName = self.host
        serverPort = self.port #change this port number if required
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        clientSocket.send(self.request.encode('utf-8'))
        modifiedSentence = clientSocket.recv(1024)
        print ('From Server:', modifiedSentence)
        clientSocket.close()

class ListenToFileReq(threading.Thread):
    def __init__(self,host,port,request = None):
        super(ListenToFileReq,self).__init__()
        self.host = host
        self.port = port
        self.request = request

    def run(self):
        serverPort = self.port # change this port number if required
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('', serverPort))
        serverSocket.listen(1)
        print ("The server is ready to receive")
        while 1:
            connectionSocket, addr = serverSocket.accept()
            sentence = connectionSocket.recv(1024).split()
            if sentence:
                if len(sentence) == 2:
                    response = f"File request message for {sentence[1]} has been sent to my successor."
                    connectionSocket.send(response.encode('utf-8'))
            connectionSocket.close()

class transferFile(threading.Thread):
    def __init__(self,host,port,file_name):
        super(transferFile,self).__init__()
        self.host = host
        self.port = port
        self.file_name = file_name
    
    def run(self):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # send file
        f = open(self.file_name+".pdf",'rb')
        data = f.read(MSS)
        seq = 0
        Ack = 0
        # send the file name first
        toSendPacket = {}
        toSendPacket["seq"] = seq
        toSendPacket["ack"] = Ack
        toSendPacket["data"] = self.file_name
        #pickle data
        pickle_out = pickle.dumps(toSendPacket)
        mysock.sendto(pickle_out,(self.host,self.port))
        seq += len(self.file_name)
        while data:
            toSendPacket["seq"] = seq
            toSendPacket["ack"] = Ack
            toSendPacket["data"] = data
            pickle_out = pickle.dumps(toSendPacket)
            mysock.sendto(pickle_out,(self.host,self.port))
            seq += len(data)
            data = f.read(MSS)
        # send a data with 0 size to indicate the completion of transfering file
        toSendPacket = {}
        toSendPacket["seq"] = seq
        toSendPacket["ack"] = Ack
        toSendPacket["data"] = data
        pickle_out = pickle.dumps(toSendPacket)
        mysock.sendto(pickle_out,(self.host,self.port))
        self.file_name = None
        mysock.close()

def Myhash(filename):
    return int(filename)%256
def location(hv):
    pass
def main():
    host = 'localhost'
    #step1: initialize and configuration DHT
    peer = dhtNode(host,int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
    #step2: Ping successors
    # listening to ping request
    # # one thread for listen to ping request
    peer.Listening()
    # two threads for sending ping request to two successors
    # send ping request
    peer.Pinging()
    #step3: Requesting a file
    # while True:
    #     command = input("enter a command: ").split()
    #     if len(command) == 2:
    #         t = transferFile(peer.host,peer.fir_successor+50000,"2012")
    #         t.start()
    
    #step4

    #step5
if __name__=='__main__':
    main()