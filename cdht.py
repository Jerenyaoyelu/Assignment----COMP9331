# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading
import pickle
blocksize, MSS = 300,300

class UDP_Server(threading.Thread):
    def __init__(self,host,port):
        super(UDP_Server,self).__init__()
        self.host = host
        self.port = port
    
    #need to distinguish it is a ping request or a file here
    #download file and reassemble it
    def run(self):
        LTPsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        LTPsock.bind((self.host,self.port))
        f_name, packet = "", {}
        # chunk = b''
        next_seq,Seq,Ack = 0,0,0
        isdone = False
        while True:
            data, addr = LTPsock.recvfrom(1024)
            packet = pickle.loads(data)
            sending_peer = packet["Peer"]
            if "Ping_request" in packet:
                print(f"A ping request message was received from Peer {sending_peer}")
                response = pickle.dumps({"Ping_response":time.ctime(),"Peer":self.port-50000})
                LTPsock.sendto(response,addr)
            elif "Ping_response" in packet:
                print(f"A ping response message was received from Peer {sending_peer}")
            else:
                # print(packet)
                if isdone:
                    f_name = ""
                    next_seq, Seq, Ack = 0,0,0
                    isdone =False
                if not f_name:
                    f_name = packet["data"]
                    print(f_name)
                    f = open("received_"+f_name+".pdf",'wb')
                    next_seq += len(f_name)
                if packet["seq"] == next_seq:
                    if(packet["data"] == '\0'):
                        isdone == True
                    else:
                        f.write(packet["data"])
                        Ack = next_seq
                        next_seq += len(packet["data"])
                acknowledgement = str(Seq) + " "+str(Ack) + '\r\n'
                LTPsock.sendto(acknowledgement.encode("utf-8"),addr)
        LTPsock.close()

class ReqPing(threading.Thread):
    def __init__(self,host,peer,port):
        super(ReqPing,self).__init__()
        self.host = host
        self.port = port
        self.peer = peer
    
    def run(self):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        while True:
            mysock.settimeout(1)
            try:
                toSendPing = pickle.dumps({"Ping_request": time.ctime(),"Peer":self.peer})
                mysock.sendto(toSendPing,(self.host,self.port))
            except TimeoutError:
                continue
        mysock.close()

class dhtNode:
    def __init__(self,id,fir_successor,sec_successor):
        self.peer = id
        self.port = id + 50000
        self.fir_successor = fir_successor
        self.sec_successor = sec_successor
        self.noreply_1 = 0
        self.noreply_2 = 0
        self.isLeaving = False

    def PingSuccessor(self,host):
        LsnPing = UDP_Server(host,self.peer+50000)
        LsnPing.start()
        SndPingToFS = ReqPing(host,self.peer,self.fir_successor+50000)
        SndPingToFS.start()
        SndPingToSC = ReqPing(host,self.peer,self.sec_successor+50000)
        SndPingToSC.start()
        
    # def Request_TCP(self,message):
    #     serverName = self.host
    #     serverPort = message["RequestingPeer"] + 50000#change this port number if required
    #     clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     clientSocket.connect((serverName, serverPort))
    #     clientSocket.send(self.request.encode('utf-8'))
    #     modifiedSentence = clientSocket.recv(1024)
    #     clientSocket.close()

#     def transferFile(self, filename):
#         LsnRes = ListenToFileReq(self.host,self.id+50000)
#         LsnRes.start()
#         Stdin = threading.Thread(target=self.UsrInput, args=(),daemon=True)
#         if filename not None:
#             file_location = location(filename)
            
            

#     def location(self):
#         hashValue = self.filename % 256
#         if self.id < hashValue <= self.fir_successor:
#             return self.fir_successor
#         if self.fir_successor < self.id:
#             if self.id < hashValue <= 255 or hashValue <= self.fir_successor:
#                 return self.fir_successor 
#         return 0

#     def UsrInput(self):
#         while True:
#             command = input().split()
#             if len(command) == 2 and command[0] == "Request":
#                 filename = command[1]
#                 if filename >255 or filename<0:
#                     print("Requesting file does not exist!")
#                 message = {"File":filename,"RequestingPeer":self.id}
#             elif len(command) == 1 and command[0] == "Quit":
#                 self.isAboutToLeave = True
#             else:
#                 print("Invalid Input!")

# class ReqFile(threading.Thread):
#     def __init__(self, host, port, request):
#         super(ReqFile,self).__init__()
#         self.host = host
#         self.port = port
#         self.request = request

#     def run(self):
#         # total = len(sys.argv)
#         # cmdargs = str(sys.argv)
        

# class ListenToFileReq(threading.Thread):
#     def __init__(self,host,port,request = None):
#         super(ListenToFileReq,self).__init__()
#         self.host = host
#         self.port = port
#         self.request = request

#     def run(self):
#         serverPort = self.port # change this port number if required
#         serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         serverSocket.bind(('', serverPort))
#         serverSocket.listen(1)
#         print ("The server is ready to receive")
#         while 1:
#             connectionSocket, addr = serverSocket.accept()
#             sentence = connectionSocket.recv(1024).split()
#             if sentence:
#                 if len(sentence) == 2:
#                     response = f"File request message for {sentence[1]} has been sent to my successor."
#                     connectionSocket.send(response.encode('utf-8'))
#             connectionSocket.close()

# class transferFile(threading.Thread):
#     def __init__(self,host,port,file_name):
#         super(transferFile,self).__init__()
#         self.host = host
#         self.port = port
#         self.file_name = file_name
    
#     def run(self):
#         mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
#         # send file
#         f = open(self.file_name+".pdf",'rb')
#         data = f.read(MSS)
#         seq = 0
#         Ack = 0
#         # send the file name first
#         toSendPacket = {}
#         toSendPacket["seq"] = seq
#         toSendPacket["ack"] = Ack
#         toSendPacket["data"] = self.file_name
#         #pickle data
#         pickle_out = pickle.dumps(toSendPacket)
#         mysock.sendto(pickle_out,(self.host,self.port))
#         seq += len(self.file_name)
#         while data:
#             toSendPacket["seq"] = seq
#             toSendPacket["ack"] = Ack
#             toSendPacket["data"] = data
#             pickle_out = pickle.dumps(toSendPacket)
#             #slice pickles
#             # sentinel3 = b'\x00\x00START_MESSAGE!\x00\x00'
#             # sentinel4 = b'\x00\x00END_MESSAGE!\x00\x00'
#             # mysock.sendto(sentinel3, (self.host,self.port))
#             mysock.sendto(pickle_out, (self.host,self.port))
#             # for n in range(len(pickle_out) // blocksize + 1):
#             #     mysock.sendto(pickle_out[n * blocksize: (n + 1) * blocksize], (self.host,self.port))
#             # mysock.sendto(sentinel4, (self.host,self.port))
#             seq += len(data)
#             data = f.read(MSS)
#         # send a data with 0 size to indicate the completion of transfering file
#         toSendPacket = {}
#         toSendPacket["seq"] = seq
#         toSendPacket["ack"] = Ack
#         toSendPacket["data"] = '\0'
#         pickle_out = pickle.dumps(toSendPacket)
#         mysock.sendto(pickle_out,(self.host,self.port))
#         self.file_name = None
#         mysock.close()

def main():
    host = 'localhost'
    peer = dhtNode(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
    peer.PingSuccessor(host)
if __name__=='__main__':
    main()