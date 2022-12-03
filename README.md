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

## reflections
### possible future improvements
1) make UDP reliability guarantee using acks and a stop and wait protocol
2) maybe make more efficent using JSON instead of Pickle
### program errors
1) If a client exits using keyboard interrupt, the server won’t update the log files accordingly as that function is exclusively tied with the out command. This creates errors for AED as it will show the user to still be active.
2 ) Currently if two of the same users log in with different UDP port numbers but the same username, AED will show two of the same users active. Furthermore, sending over a file using UVF will send it to the user who logged in first as he would be placed higher on the log list.
3 ) If A user logs in with a username which doesn’t exist in the database, he would be stuck on the login forever until he uses keyboard interrupt. This is because the timeout function for authentication works by comparing the last attempted login of a user in the database not the IP address of the client.

