# Client - Server 

## Abstract
An application based on client-server architecture consisting of one server and multiple clients communicating concurrently as well as peer to peer networks. Supports a range of functions including Authentication, data generation, data sharing between edge device and server, and between two edge devices.

Goal of project is to:
1. Design and implement a communication protocol
2. Familiarise with socket programming

## Usage
```
python3 TCPServer3.py SERVER_PORT MAX_ATTEMPTS[1-5]
```
In separate terminal
```
python3 client.py IP TCPPORT UDPPORT
```
Currently program only supports local host as the server port.

**Files Walkthrough**
|File/Folder         | Purpose                                                                                                                                        |
|--------------------|:----------------------------------------------------------------------------------------------------------------------------------------------:|
|server.py      | code to run the serever
|client.py         | code to run the client
|credentials.txt      | list of users and passwords
