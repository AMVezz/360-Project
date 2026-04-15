#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <fcntl.h>

#define PORT 8080
#define BUFFER_SIZE 1024
#define MAX_EVENTS 10
#define MAX_CLIENTS 100



int clients[MAX_CLIENTS];   //numbers representing currently connected clients. set to max (100) 
int client_count = 0;       //tracks how many cleints are in the array 


//set_nonblocking() - makes a socket non-blocking, read/accept return instantly. 
// (fcntl -> linux system call, allows you to get/change properties of a file descriptor)
void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);      //F_GETFL = get flags
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);     //F_SETFL = set flags OR adds 0_NONBLOCK to existing flags 
}



//add client fd to list 
void add_client(int fd) {
    clients[client_count++] = fd;
}



//remove client fd friom list 
void remove_client(int fd) {
    for (int i = 0; i < client_count; i++) {
        if (clients[i] == fd) {
            clients[i] = clients[--client_count];   //replace with last 
            break;
        }
    }
}

//void broadcast() - iterates through clients and sends char *message to everyone but the sender
void broadcast(int sender_fd, char *message, int len) {
    for (int i = 0; i < client_count; i++) {
        if (clients[i] != sender_fd) { 
            write(clients[i], message, len);
        }
    }
}






int main() {
    int server_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    // 1. Create server socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) { perror("socket"); exit(1); }

    // Allow reuse of port immediately after restart
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 2. Bind
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) == -1) {
        perror("bind"); exit(1);
    }

    // 3. Listen
    if (listen(server_fd, 5) == -1) { perror("listen"); exit(1); }

    // 4. Set server socket to non-blocking
    set_nonblocking(server_fd);

    // 5. Create epoll instance
    int epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) { perror("epoll_create1"); exit(1); }

    // 6. Add server socket to epoll watch list
    struct epoll_event event;
    event.events = EPOLLIN;  // watch for incoming data
    event.data.fd = server_fd;
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &event);

    printf("Server listening on port %d\n", PORT);

    // 7. Event loop
    struct epoll_event events[MAX_EVENTS];
    while (1) {
        // Wait for something to happen on any watched fd
        int n = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);

        for (int i = 0; i < n; i++) {
            int fd = events[i].data.fd;

            if (fd == server_fd) {
                // New client connecting
                int client_fd = accept(server_fd, (struct sockaddr*)&address, (socklen_t*)&addrlen);
                if (client_fd == -1) { perror("accept"); continue; }

                set_nonblocking(client_fd);

                // Add new client to epoll
                event.events = EPOLLIN;
                event.data.fd = client_fd;
                epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &event);

                add_client(client_fd);
                printf("Client connected: fd=%d\n", client_fd);

            } else {
                // Existing client sent a message
                char buffer[BUFFER_SIZE];
                int bytes_read = read(fd, buffer, BUFFER_SIZE);

                if (bytes_read <= 0) {
                    // Client disconnected
                    printf("Client disconnected: fd=%d\n", fd);
                    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL);
                    remove_client(fd);
                    close(fd);
                } else {
                    buffer[bytes_read] = '\0';
                    printf("Message from fd=%d: %s", fd, buffer);
                    broadcast(fd, buffer, bytes_read);
                }
            }
        }
    }

    close(server_fd);
    return 0;
}