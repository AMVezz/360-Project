# Cpt_S 360 Group Project: QuickChat

## Project Overview and Goals

QuickChat is a real-time chat application that allows multiple people to connect to a central server and exchange messages instantly. The system is designed to demonstrate core networking and systems concepts by implementing a complete client-server architecture from scratch.

The server runs on an AWS cloud server, allowing remote clients to connect over the internet instead of only using localhost.

The goals of this project were:

* Build a multi-user chat system using networking
* Understand how concurrent connections are handled on the server
* Apply system-level I/O techniques for efficient communication
* Design a simple and intuitive user interaction model

---

## Running the Server

### Build:

`make`

### Run:

`./server`

The CLI should display:
`Server listening on port 8080`

---

## Testing the Chat

* Open a new terminal and connect using:
  `nc localhost 8080`
* Open multiple terminals to simulate multiple users

---

## Themes Used

### 1. Event-Based Concurrency

The server uses an event-driven model to handle multiple clients. Instead of creating a new thread for each user, it monitors multiple connections and responds when activity occurs. This improves efficiency and reduces overhead.

### 2. Network Programming

The project uses POSIX sockets to establish communication between clients and the server. Core functions such as `socket()`, `bind()`, `listen()`, `accept()`, and `recv()/send()` were used to implement the networking layer.

### 3. System-Level I/O

Low-level I/O operations were used to read and write data between clients and the server. This required careful handling of buffers, partial reads/writes, and ensuring reliable message transmission.

### 4. Application-Layer Protocol Design

A simple custom protocol was designed for message exchange. Messages are sent as plain text, and the server broadcasts incoming messages to all connected clients. This demonstrates how higher-level communication rules are built on top of raw sockets.

---

## Design Decisions and Trade-Offs

* **Plain Text Protocol**

  * Used simple text messages for easier implementation
  * Trade-off: lacks structure and extensibility compared to formats like JSON

* **No Authentication**

  * Simplified user handling by not requiring login
  * Trade-off: no user identity or security

---

## Challenges Encountered

* Handling multiple client connections without crashing the server
* Managing partial reads and ensuring full messages are received
* Debugging socket errors and connections droping
* Synchronizing messages to all clients

---

## Lessons Learned

* Got some experience with socket programming and networking
* Learned how to manage multiple users

---

## Example Usage

Start server:

```
./server
```

Connect while logged in to server:

```
nc localhost 8080
```

Connect

```
nc (server IP) 8080
```

Then you can type messages in any client terminal to broadcast to others.
