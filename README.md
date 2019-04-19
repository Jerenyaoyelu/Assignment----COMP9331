#% Assignment Report of COMP9331
#% Written by YAOYE LU
#% Student ID: 5188093
#% Title: Report of implementation of P2P Protocol Circular DHT

1. Steps of implementation

    1.1 Build a peer node class which contains the following properties/functions:
    
        a. A initilization function to nitilize a peer node.
        b. A UDP_Server to permanently listen to the message (ping and file packets) sent over UDP and maintain receiver side logs.
        c. A UDP_Client to send message (ping and file packets) to UDP servers.
        d. A TCP_server to permanently listen to the message (request file, quit and request/response of successor because of a departing/dead peer) sent over TCP.
        e. A ForwardFileRes (TCP client) to sent TCP message (request/response of successor because of a departing/dead peer)
        f. A SAWTransFile to transfer requested file only, simulate the packet dropping, implement stop-and-wait protocol and matintain the sender side logs.
        g. A myHash to calculate the hash value of filename.
        h. A location to figure out where the requested file is stored.
        i. A UsrInput to take standard input from the users to achieve to needs of requesting files or graceful departure.
        j. A main to create threadings for specific process.
    
    1.2 Call the main function

2. Design Choices
    2.1 Ping intervals:

        The interval chosen here is 10 seconds. 

        The reason is that step 3 and step 4 require users to input commands in the terminal, but when they are inputing, the pinging messages are printed out all the time, so if the time interval is too short, the users will not be able to input.

        After several trails, 10 seconds is appropriate to give enough time to type and do not leading evaluator to a long wait. Less than 10 seconds will be very hard to finish the input for some users (myself included), while more than 10 seconds is too long.

    2.2 Number of lost Packets to determine a dead peer:

        The number is decided to be 4.

        The reason is that in the "fast transmission" if the sender received three duplicated acks, then retransfer the packet, and to imitate this mindset 4 is decided.

        Furtherly, considering the unrealiability of UDP transmission, lost a few packets might be normal, but no less than 4 packets continuously lost during the transmission is very unnormal.

    2.3 Formats of message:
    
        The basic idea is to build a dictionary containing a key word "flag" to distinguish the type of messages, and the rest keys in this dictionary depend on specific needs.
        
        Keys specification:
            "flag": type of message
            "seq": sequence number of message
            "Peer"/"SendingPeer"/"RequestingPeer": requesting peer
            "FS": first successor
            "SC": second successor
            "data": file chunks
            "ack": acknowledgement
            "File": filename
            "lacation": record where the file is stored
            "visitedPeer": record peers that have received the file request
            "KilledPeer": the peer killed by user
            "QuitingPeer": gracefully departing peer

        a. Ping Request:
            {"flag":"Ping_request","seq":,"Peer":,"FS":,"SC":}
        b. Ping Response:
            {"flag":"Ping_response","seq":,"Peer":}
        c. Request File:
            {"flag":"Request_File","File":,"RequestingPeer":,"location":,"visitedPeer":[]}
        d. File Found Response:
            {"flag":"FileFound_response","SendingPeer":}
        e. File Transferring:
            {"flag":"File_tansferring","seq": , "ack": , "data":}
        f. Acknowledgement:
            {"flag":"Ack","seq": , "ack":, "data":}
        g. Request Successor:
            {"flag":"Request_successor","Peer":,"KilledPeer":}
        h. Quit:
            {"flag":"Quit","QuitingPeer":, "FS":, "SC":}
        i. Response Successor:
            {"flag":"Response_successor","Peer":,"KilledPeer":,"FS":,"SC":}

3. Version of Python:
    Python3

4. Improvements:
    4.1 Considering file chunks are not transferred in order:
        Infact, I have successfully implemented this in the earlier version, but after being told that there is no need to consider this case in the forum, and to make the code clearer, I just backed up in github and deleted it in the source code.
        Therefore, in future, if there is any real application, this has to be considered and handled.
    
    4.2 Considering the pickled packets got truncated during the transmission when MSS is large enough:
        I have encoutered this problem when I was testing the code. First, I was not able to solve it and then I came to an idea by using flag labeling the type of packets to distinguish if it is a completely original pickled fragment or it is a truncated piece of pickled fragment. And this also inspired the idea of the format of messages.
        BTW, I also have implemented this in earlier version and backed up in github.

5. Important Note:
    5.1 The first letter of the input command has to be UPPER-CASES.
    5.2 Due to the short time inetrval of pinging, it is easy to input the command incorrectly, if that happens, it is NOT that there is bug in the source code, just typos or some unexpected situations, so PLEASE PLEASE just be paient to try again and input carefully, because it happens very often to me as well when testing!!