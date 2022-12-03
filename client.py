"""
    Python 3
    Usage: python3 client.py IP TCPPORT UDPPORT
    coding: utf-8
    
    Author: Daniel Zhang z5310780
"""
from socket import *
import sys
import pickle
import time
import random
from threading import Thread
import os.path

#Server would be running on the same host as Client
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT UDP_PORT\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
UDP_PORT = int(sys.argv[3])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)
# build connection with the server and send message to it
clientSocket.connect(serverAddress)
#create a UDP listening only socket for the client side
udpListen = socket(AF_INET, SOCK_DGRAM)
udpListen.bind((serverHost, UDP_PORT))
addr = (serverHost, UDP_PORT)


# While loop to ask for Password until it is correct or reach max attempts
access = False
username = input("Username:")
while(access == False):
    password = input("Password:")
    # send over username,password and UDP port to check if user exists and password is correct
    # Sent using pickle, to encode a dictionary
    message = pickle.dumps({"Command": "Authenticate", "username": username, "password": password, "UDP_PORT": UDP_PORT})
    clientSocket.sendall(message)

    # receive response from the server and print messages accordingly
    data = clientSocket.recv(1024)
    receivedMessage = pickle.loads(data)
    if receivedMessage["Command"] == "Allowed":
        print("Access granted")
        access = True
    elif receivedMessage["Command"] == "Denied":
        print("Access denied")
    elif receivedMessage["Command"] == "Locked":
        print("Invalid Password. Your account has been blocked. Please try again later")
        sys.exit(0)

# function to listen on UDP socket
def UVFRECV():
    # First packet contains the filename
    data,addr = udpListen.recvfrom(4096)
    print("\nReceived File:",data.strip())
    filename = data.strip()
    f = open(data.strip(),'wb')
    # Subsequence packets contain actual file data
    data,addr = udpListen.recvfrom(4096)
    # Create file
    try:
        while(data):
            f.write(data)
            udpListen.settimeout(2)
            data,addr = udpListen.recvfrom(4096)
    except timeout:
        f.close()
        udpListen.close()
        print(filename, "downloaded")
    print("Enter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):", end = '', flush = True)

# Function to send Files using UDP
def UVFSEND(command):
    command = command.strip()
    UVF = command.split()

    if len(UVF) < 3:
        print("UVF command requires deviceName and fileName")
        return
    device = str(UVF[1])
    fileName = str(UVF[2])
    # check if file exists
    try :
        open(fileName, "r")
    except FileNotFoundError:
        print(f"\n{fileName} doesn't exist\nEnter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):", end = '', flush = True)
        return

    message = pickle.dumps({"Command": "AED", "username": username})
    clientSocket.sendall(message)
    data = clientSocket.recv(4096)
    receivedMessage = pickle.loads(data)
    ActiveDevices = []
    # break up data from the AED command into an array 
    for i in range(len(receivedMessage["ActiveDevice"])):
        string1 = str(receivedMessage["ActiveDevice"][i])
        string1 = string1.split()
        ActiveDevices.append([string1[0],string1[1],string1[2]])

    address = ""
    # find the address of the device
    for i in range(len(ActiveDevices)):
        if device in ActiveDevices[i][0]:
            address = (ActiveDevices[i][1],int(ActiveDevices[i][2].strip(',')))         
    if address == "":
        print(f"{device} is offline\nEnter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):", end = '', flush = True)
        return
    # create UDP socket for sending bytes
    SocketSend = socket(AF_INET, SOCK_DGRAM)
    SocketSend.sendto(fileName.encode(),address)
    
    with open(fileName, "rb") as f:
        data = f.read(4096)
        while (data):
            if(SocketSend.sendto(data,address)):
                # Prevent sender from overwhelming receiver
                time.sleep(0.1)
                data = f.read(4096)
    
    SocketSend.close()
    f.close()
    print(f"\n{fileName} send complete\nEnter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):", end = '', flush = True)
    return

UVFThread = Thread(target=UVFRECV)
# this makes it so that the thread dies when the main process dies
UVFThread.daemon = True
UVFThread.start()

# While loop asking for commands
while True:
    command = input("Enter one of the following commands (EDG, UED, SCS, DTE, AED, OUT, UVF):")

    

    # parse the message received from user and take corresponding actions using if statements

    if command[0:3] == "EDG":
        # process arguments and error checking
        command = command.strip()
        EDG = command.split()
        if len(EDG) < 3:
            print("EDG command required fileID and dataAmount as arguments")
            continue
        try:
            fileID = int(EDG[1])
            dataAmount = int(EDG[2])
        except:
            print("EDG error usage, EDG [int] [int]")
            continue
        filename = str(username) + "-" + str(EDG[1]) + ".txt"
        with open(filename, "w") as f:
            for i in range(dataAmount):
                f.write(str(random.randint(0,10)) + "\n")
        print("Data generation done, ",dataAmount,"data samples have been generated and stored in the file ",filename)

    elif command[0:3] == "UED":
        command = command.strip()
        UED = command.split()
        if len(UED) < 2:
            print("FileID is needed to upload the data")
            continue
        fileID = str(username) + "-" + str(UED[1]) + ".txt"

        try:
            f = open(fileID, "r")
        except:
            print("file doesn't exist")
            continue
        lines = f.readlines()
        # send over the file
        message = pickle.dumps({"Command": "UED", "username": username, "FileName":fileID, "FileID": UED[1], "FileData": lines})
        clientSocket.sendall(message) 
        data = clientSocket.recv(1024)
        receivedMessage = pickle.loads(data)
        # check if file was recieved succesfully by looking at reply from server
        if receivedMessage["Command"] == "UPLOADSUCCESS":
            print(f"{fileID} uploaded successfully")
            continue

    elif command[0:3] == "SCS":
        command = command.strip()
        SCS = command.split()
        operations = ["SUM","AVERAGE","MAX","MIN"]
        if len(SCS) < 3:
            print("SCS command requires fileID and computationOperation as arguments")
            continue
        try:
            ID = int(SCS[1])
            operation = str(SCS[2])
        except:
            print("fileID should be an integer")
            continue
        if operation not in operations:
            print(operation," operation doesn't exist. Operations available: SUM, AVERAGE, MAX, MIN")
            continue

        # sends command over to server and prints result
        message = pickle.dumps({"Command": "SCS", "username": username, "FileID": ID, "Operation": operation})
        clientSocket.sendall(message)
        data = clientSocket.recv(1024)
        receivedMessage = pickle.loads(data)
        if receivedMessage["Result"] != "FileNotExist":
            result = receivedMessage["Result"]
            print(f"Computation {operation} result on the file {username}-{ID}.txt is {result}")
        else:
            print(f"{username}-{ID}.txt doesn't exist")

    #Send DTE request to server and print reply
    elif command[0:3] == "DTE":
        command = command.strip()
        DTE = command.split()
        if len(DTE) < 2:
            print("DTE command requires FileID")
            continue
        try:
            ID = int(DTE[1])
        except:
            print("FileId should be an integer")
            continue
        message = pickle.dumps({"Command": "DTE", "username": username, "FileID": ID})
        clientSocket.sendall(message)
        data = clientSocket.recv(1024)
        receivedMessage = pickle.loads(data)
        if receivedMessage["Result"] != "FileNotExist":
            print("File has been deleted")
        else:
            print(f"{username}-{ID}.txt doesn't exist")

    # send AED request to server and print reply
    elif command == "AED":
        message = pickle.dumps({"Command": "AED", "username": username})
        clientSocket.sendall(message)
        data = clientSocket.recv(4096)
        receivedMessage = pickle.loads(data)
        if not receivedMessage["ActiveDevice"]:
            print("No other active edge devices")
        for i in range(len(receivedMessage["ActiveDevice"])):
            print(receivedMessage["ActiveDevice"][i])

    #Exits the program but lets server know first
    elif command == "OUT":
        message = pickle.dumps({"Command": "OUT", "username": username})
        clientSocket.sendall(message)
        data = clientSocket.recv(1024)
        receivedMessage = pickle.loads(data)
        if receivedMessage["Command"] == "EXITSUCCESS":
            print("Bye", username)
            break

    elif command[0:3] == "UVF":
        # Start a new thread for the UVF command so that we can still use client during the file transfer
        t1 = Thread(target = UVFSEND, args =(command,))
        t1.daemon = True
        t1.start()

    # incase the command is unrecognised
    else:
        print("Command not recognised")
        
        



# close the socket
clientSocket.close()
