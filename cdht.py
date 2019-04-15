# Written by YAOYE LU (5188093) in Python 3
import sys
import time
import socket
import select
import threading

class dhtNode:
    def __init__(self, id, fir_successor, sec_successor):
        self.id = id
        self.fir_successor = fir_successor
        self.sec_successor = sec_successor
        self.fir_predecessor = None
        self.sec_predecessor = None

    # def _handle_ping_message(self, message, addr):

    def Ping_listen_udp(self, host, port):
        serversock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        serversock.bind((host,port))
        serversock.listen(5) #listen for connection

        #Start the while loop.
        while True:
            print("jj")
            clientsock,addr = serversock.accept()
            message = clientsock.recv(1024)
            sending_peer = addr[1] - 50000
            if message:
                print(f"A ping request message was received from Peer {sending_peer}")
                response = "Ping_response"
                clientsock.sendto(response,addr)
        clientsock.close()

    def Ping_request_udp(self, host, port):
        mysock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        mysock.connect((host,port))
        ping_frequency = 0
        while True:
            print("kk")
            if ping_frequency % 3 == 0:
                request = "ping_request"+" "+ "\r\n"
                mysock.sendto(request.encode("utf-8"),(host,port))
                data=mysock.recv(1024)
            if data:
                print(f"A ping response message was received from Peer {port-50000}")
            ping_frequency += 1
        mysock.close()


#     def File_listen_tcp(self):
#         pass
    
#     def File_request_tcp(self):
#         pass

#     def depart_peer(self):
#         pass

#     def kill_peer(self):
#         pass

# def Myhash(filename):
#     return int(filename)%256
# def location(hv):
#     pass
def main():
    host = 'localhost'
    #step1: initialize and configuration DHT
    peer = dhtNode(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
    

    #step2: Ping successors
    #2.1 a peer whose identity is i will listen to the UDP port 50000 + i for ping messages.
    #2.2 output a line to the terminal when a ping request message is received from any of its two predecessors:
        #2.2.1 "A ping request message was received from Peer 5."
    #2.3 When a peer receives a ping request message, it should send a ping response message to the sending peer so that the sending peer knows that the receiving peer is alive.
    #2.4 When a peer receives a ping response from another peer, it should display on the terminal:
        #2.3.1 "A ping response message was received from Peer 10."
    #2.5 You will need to decide on how often you send the ping messages.
    # listening to ping request
    port = peer.id + 50000
    # one thread for listen to ping request
    Listening_ping = threading.Thread(target = peer.Ping_listen_udp, args= (host,port),daemon=True)
    Listening_ping.start()
    # two threads for sending ping request to two successors
    fr_port = peer.fir_successor + 50000
    sc_port = peer.sec_successor + 50000
    Sending_ping_to_FirSccesr = threading.Thread(target = peer.Ping_request_udp,args=(host,fr_port), daemon=True)
    Sending_ping_to_FirSccesr.start()
    Sending_ping_to_SecSccesr = threading.Thread(target = peer.Ping_request_udp,args=(host,sc_port), daemon=True)
    Sending_ping_to_SecSccesr.start()
    # send ping request
    
        # command = input("enter a command: ")


    #step3: Requesting a file
    #3.1 To request a file with filename X from peer Y, the requester will type “request X” to the xterm of peer Y.
        #3.1.1 your program must be able to receive string inputs.
        #3.1.2 all the filenames in this P2P system are four digit numbers.
        #3.1.3 To compute the hash of a file, you must compute the remainder of the filename integer when it is divided by 256
        #3.1.4 the file will be stored in the peer that is the closest successor of n.
    #3.2 If a peer wants to request for a file, the peer will send a file request message to its successor. 
        # 3.2.1 The file request message will be passed round the P2P network until it reaches the peer that has the file. 
        # 3.2.3 The responding peer will send a response message directly to the requesting peer.
    #3.3 The responding peer has to transfer a file to the requesting peer over UDP connection.
        # 3.3.1 implementing a simple protocol with stop-and-wait behaviour. 
            # stop-and-wait: start a timer
            # the sender sends a data packet to the receiver, and waits until it receives an acknowledgement, or a timeout happens. 
            # In case an ACK is received, the sender sends the next part of data, and if a timeout occurs, the sender re-transmits the data.
        #3.3.2 only deals with packet lost.
    #3.4 The responding peer forms packet with MSS bytes of data. 
        #3.4.1 add the sequence number, acknowledge number, and MSS, and encapsulate all as a packet
    #3.5 Once the requesting peer received the data packet, it will generate a corresponding acknowledgement and send back to the responding peer.
    #3.6 On receipt of the acknowledgement packet, the responding peer will transfer the next MSS bytes of data.
        #3.6.1 If the data packet gets lost, the requesting peer will not transfer the acknowledgement and thus the timeout will happen in the responding peer.
    #3.7 the responding peer maintains a timer for each data packet it sends. 
        #3.7.1 The timeout-interval is set to 1 seconds in this assignment.
        #3.7.2 If the responding peer does not receive an ack within timeout-interval, it considers the packet to be lost, and re-transmit the packet.
    #3.8 The responding and requesting peers must maintain a log file named responding_log.txt and requesting_log.txt recording the information about each segment they send and receive.
    #3.9 the peers shall accept a drop_rate value as input which is the probability in which packets are dropped.

    #step4

    #step5
if __name__=='__main__':
    main()