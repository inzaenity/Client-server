from socket import *
from threading import Thread
import sys, select
import pickle
import datetime
import os

# acquire server host and port from command line parameter
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT MAX_ATTEMPTS[1-5]\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
MAX_ATTEMPTS = int(sys.argv[2])
if MAX_ATTEMPTS > 5 or MAX_ATTEMPTS < 1:
    print("\n===== Error usage, MAX_ATTEMPTS[1-5]\n")
    exit(0)
serverAddress = (serverHost, serverPort)
    
# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

#create a dictionary and process information into it
credentials = {}
with open("credentials.txt") as f:
    for line in f:
        username, password = line.split(" ")
        credentials[username.strip()] = [password, 0, 0]
#clear all logs
log = open("edge-device-log.txt", "w")
log.close()
g = open("upload-log.txt", "w")
g.close()
z = open("deletion-log.txt", "w")
z.close()

#Function to add device to log

def AddDeviceLog(message):
    num = len(open("edge-device-log.txt").readlines( )) + 1
    f = open("edge-device-log.txt", "a")
    
    time = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
    device = str(message["username"])
    UDP = str(message["UDP_PORT"])
    f.write(f"{num}; {time}; {device}; {clientAddress[0]}; {UDP}\n")
    f.close()

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
    ~ Written by Tutor
"""

class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        
        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True

    def run(self):
        message = ''
        
        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            
            try:
                message = pickle.loads(data)
            except EOFError:
                print("===== the user disconnected - ", clientAddress)
                break
            
            #parse the message received from client and take corresponding actions
            
            if message["Command"] == "Authenticate":
                
                # series of if statements to determine whether the user is allowed in and send response back to client
                if message["username"] in credentials:
                    if credentials[message["username"]][2] != 0:
                        # if lock time hasn't expired yet
                        if (datetime.datetime.now() - credentials[message["username"]][2]).seconds < 10:
                            reply = pickle.dumps({"Command": "locked"})
                            self.clientSocket.send(reply)
                        else:
                            credentials[message["username"]][2] == 0
                            if message["password"].strip() == credentials[message["username"]][0].strip():
                                reply = pickle.dumps({"Command": "Allowed"})
                                self.clientSocket.send(reply)
                                AddDeviceLog(message)
                        
                            else:
                                #save number of attempts and when
                                credentials[message["username"]][1] += 1
                                if credentials[message["username"]][1] >= MAX_ATTEMPTS:
                                    credentials[message["username"]][1] = 0
                                    credentials[message["username"]][2] = datetime.datetime.now()
                                    reply = pickle.dumps({"Command": "Locked"})
                                    self.clientSocket.send(reply)
                                else:
                                    reply = pickle.dumps({"Command": "Denied"})
                                    self.clientSocket.send(reply)
                    elif message["password"].strip() == credentials[message["username"]][0].strip():
                        reply = pickle.dumps({"Command": "Allowed"})
                        self.clientSocket.send(reply)
                        AddDeviceLog(message)
                        
                    else:
                        credentials[message["username"]][1] += 1
                        if credentials[message["username"]][1] >= MAX_ATTEMPTS:
                            credentials[message["username"]][1] = 0
                            credentials[message["username"]][2] = datetime.datetime.now()
                            reply = pickle.dumps({"Command": "Locked"})
                            self.clientSocket.send(reply)
                        else:
                            reply = pickle.dumps({"Command": "Denied"})
                            self.clientSocket.send(reply)
                else:
                    reply = pickle.dumps({"Command": "Denied"})
                    self.clientSocket.send(reply)

            # OUT command
            # Update logs accordingly and send confimation message back to client
            # Note logs won't be accurate if two people log in using same user
            elif message["Command"] == "OUT":
                with open("edge-device-log.txt", "r") as f:
                    lines = f.readlines()
                f.close()
                linenum = 0
                for i in range(len(lines)):
                    if message["username"] in lines[i]:
                        linenum = i 
                        break
                with open("edge-device-log.txt", "w") as f:
                    for i in range(linenum):
                        f.write(lines[i])
                    after = linenum + 1
                    while after < len(lines):
                        DeviceNum = int(lines[after][0])
                        list1 = list(lines[after])
                        list1[0] = DeviceNum - 1
                        mystring = ""
                        for i in list1:
                            mystring += str(i)
                        f.write(mystring)
                        after += 1
                f.close()
                print(message["username"], "exited the edge netword")
                reply = pickle.dumps({"Command": "EXITSUCCESS"})
                self.clientSocket.send(reply)

            # AED command
            # reads the logs and sends back required information
            elif message["Command"] == "AED":
                print("Edge device", message["username"], "issued AED command")
                print("Return other active edge device list:")
                with open("edge-device-log.txt", "r") as f:
                    lines = f.readlines()
                ActiveDevice = []
                for i in range(len(lines)):
                    if message["username"] in lines[i]:
                        continue
                    else:
                        log = lines[i].strip().split("; ")
                        string1 = str(log[2]) + " " + str(log[3]) + " " + str(log[4]) + ", active since " + str(log[1])
                        print(string1)
                        ActiveDevice.append(string1)
                reply = pickle.dumps({"ActiveDevice": ActiveDevice})
                self.clientSocket.send(reply)
                f.close()

            # UED command
            # Creates of file using data sent over tcp
            elif message["Command"] == "UED":
                
                data = message["FileData"]
                time = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
                dataAmount = len(message["FileData"])
                username = message["username"]
                fileID = message["FileID"]
                fileName = message["FileName"]
                with open("upload-log.txt","a") as f:
                    f.write(f"{username}; {time}; {fileID}; {dataAmount}\n")
                f.close()
                with open(fileName, "w") as g:
                    FileData = message["FileData"]
                    for i in range(len(FileData)):
                        g.write(FileData[i])
                g.close()
                print(f"Edge device {username} issued UED command")
                print(f"A data file is received from edge device {username}")
                print(f"The file with ID of {fileName} has been received, upload-log.txt file has been updated")
                reply = pickle.dumps({"Command":"UPLOADSUCCESS"})
                self.clientSocket.send(reply)

            # SCS command
            # Does the mathematical operations required on requested file and sends back result
            elif message["Command"] == "SCS":
                FileID = str(message["username"]) + "-" + str(message["FileID"]) + ".txt"

                print(f"Edge device",message["username"], "requested a computation operation on the file wth ID of", message["FileID"])
                try:
                    f = open(FileID, "r")
                    lines = f.readlines()
                    if message["Operation"] == "SUM":
                        SUM = 0
                        for i in range(len(lines)):
                            temp = int(lines[i].strip())
                            SUM = SUM + temp
                        reply = pickle.dumps({"Result": SUM})
                        self.clientSocket.send(reply)
                        print(message["Operation"], "computation has been made on edge device", message["username"], "the result is ", SUM )
                    elif message["Operation"] == "AVERAGE":
                        SUM = 0
                        for i in range(len(lines)):
                            temp = int(lines[i].strip())
                            SUM = SUM + temp
                        AVERAGE = SUM/len(lines)
                        reply = pickle.dumps({"Result": AVERAGE})
                        self.clientSocket.send(reply)
                        print(message["Operation"], "computation has been made on edge device", message["username"], "the result is", AVERAGE)
                    elif message["Operation"] == "MAX":
                        MAX = 0
                        for i in range(len(lines)):
                            temp = int(lines[i].strip())
                            if temp > MAX:
                                MAX = temp
                        reply = pickle.dumps({"Result": MAX})
                        self.clientSocket.send(reply)
                        print(message["Operation"], "computation has been made on edge device", message["username"], "the result is", MAX)
                    elif message["Operation"] == "MIN":
                        MIN = 100
                        for i in range(len(lines)):
                            temp = int(lines[i].strip())
                            if temp < MIN:
                                MIN = temp
                        reply = pickle.dumps({"Result": MIN})
                        self.clientSocket.send(reply)
                        print(message["Operation"], "computation has been made on edge device", message["username"], "the result is", MIN)
                   
                except:
                    print("File doesn't exist")
                    reply = pickle.dumps({"Result":"FileNotExist"})
                    self.clientSocket.send(reply)

            # DTE command
            # deletes requied file and updates log accordingly
            elif message["Command"] == "DTE":
                FileID = str(message["username"]) + "-" + str(message["FileID"]) + ".txt"
                print(f"Edge device",message["username"], "issued DTE command, the file ID is", message["FileID"])
                username = message["username"]
                fileID = message["FileID"]
                time = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
                try:
                    f = open(FileID, "r")
                    lines = f.readlines()
                    dataAmount = len(lines)
                    f.close()
                    g = open("deletion-log.txt","a")
                    g.write(f"{username}; {time}; {fileID}; {dataAmount}\n")
                    g.close()
                    os.remove(FileID)
                    print(f"The file with ID of {fileID} from edge device {username} has been deleted, deletion log file has been updated")
                    reply = pickle.dumps({"Result": "DELETESUCCESS"})
                    self.clientSocket.send(reply)

                except:
                    print("File doesn't exist")
                    reply = pickle.dumps({"Result":"FileNotExist"})
                    self.clientSocket.send(reply)
                






print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")

while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()


# Downsides
# if we shut the server down and then restart it, previous files on the server will still exist
# If we don't log out using the OUT command, the edge-device-log.txt doesn't update properly
# If two people log in using the same username, the program will have errors in the logs
