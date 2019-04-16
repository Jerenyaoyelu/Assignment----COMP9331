# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading
import pickle
blocksize, MSS = 300

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
        f_name, chunk = None, None
        next_seq,Seq,Ack = 0,0,0
        isdone, isPing,isSlice = False, False
        sentinel1 = b'\x00\x00PING_REQUEST!\x00\x00'
        sentinel2 = b'\x00\x00PING_END!\x00\x00'
        sentinel3 = b'\x00\x00START_MESSAGE!\x00\x00'
        sentinel4 = b'\x00\x00END_MESSAGE!\x00\x00'
        Fblocks = []
        while True:
            data, addr = LTPsock.recvfrom(1024)
            sending_peer = addr[1] - 50000
            blocks.append(data)
            # beginning of a ping request
            if data == sentinel1:
                isPing = True
            # beginning of a sliced pickled fragments
            elif data == sentinel3:
                isSlice = True
            # a completely original pickled fragment or some part of sliced pickled fragment or a ping message
            elif data != sentinel2 and data != sentinel4:
                # is a ping message
                if isPing:
                    # because we dont have to consider packet sent out of order
                    # otherwise we have to store in a list first rather than send response immediately
                    print(f"A ping request message was received from Peer {sending_peer}")
                    response = pickle.dumps({"Ping_response":time.ctime()})
                    LTPsock.sendto(response,addr)
                # is some part of sliced pickled fragment
                elif isSlice:
                    Fblocks.append(data)
                else:  # is a completely original pickled fragment 
                    chunk = pickle.loads(data)
            # end of a ping request
            elif data == sentinel2:
                isPing = False
            else:# end of a sliced pickled fragment
                isSlice = False
                chunk = b''.join(Fblocks)
                Fblocks = []
            # a complete pickled fragment
            if chunk:
                if isdone:
                    f_name = None
                    next_seq, Seq, Ack = 0,0,0
                    isdone =False
                if not f_name:
                    f_name = chunk["data"]
                    f = open("received_"+f_name+".pdf",'wb')
                    next_seq += len(f_name)
                if chunk["seq"] == next_seq:
                    if(len(chunk) == 2):
                        isdone == True
                    else:
                        f.write(chunk["data"])
                        Ack = next_seq
                        next_seq += len(chunk["data"])
                acknowledgement = str(Seq) + " "+str(Ack) + '\r\n'
                LTPsock.sendto(acknowledgement.encode("utf-8"),addr)
                chunk = None
        LTPsock.close()

class ReqPing(threading.Thread):
    def __init__(self,host,port):
        super(ReqPing,self).__init__()
        self.host = host
        self.port = port
    
    def run(self):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # while True:
        toSendPing = pickle.dumps({"Ping_request": time.ctime()})
        sentinel1 = b'\x00\x00PING_REQUEST!\x00\x00'
        sentinel2 = b'\x00\x00PING_END!\x00\x00'
        mysock.sendto(sentinel1,(self.host,self.port))
        mysock.sendto(toSendPing,(self.host,self.port))
        mysock.sendto(sentinel2,(self.host,self.port))
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
            #slice pickles
            sentinel3 = b'\x00\x00START_MESSAGE!\x00\x00'
            sentinel4 = b'\x00\x00END_MESSAGE!\x00\x00'
            mysock.sendto(sentinel3, (self.host,self.port))
            for n in range(len(pickle_out) // blocksize + 1):
                mysock.sendto(pickle_out[n * blocksize: (n + 1) * blocksize], (self.host,self.port))
            mysock.sendto(sentinel4, (self.host,self.port))

            seq += len(data)
            data = f.read(MSS)
        # send a data with 0 size to indicate the completion of transfering file
        toSendPacket = {}
        toSendPacket["seq"] = seq
        toSendPacket["ack"] = Ack
        toSendPacket["data"] = ""
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
    while True:
        command = input("enter a command: ").split()
        if command:
            if len(command) == 2:
                while 1:
                     if Myhash(command[1])
            t = transferFile(peer.host,peer.fir_successor+50000,"2012")
            t.start()
    
    #step4

    #step5
if __name__=='__main__':
    main()