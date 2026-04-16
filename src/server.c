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

//USERNAME struct 
typedef struct {
    int fd;
    char username[64];
    int has_username;       //0 =waiting for username / 1 =go to chat 
} Client;

Client clients[MAX_CLIENTS];
int client_count = 0;

void set_nonblocking(int fd);
void remove_client(int fd);
void broadcast(int sender_fd, char *message, int len);

//add client fd to list 
void add_client(int fd) {
    clients[client_count].fd = fd;
    clients[client_count].has_username = 0;
    memset(clients[client_count].username, 0, 64);
    client_count++;
}

//remove client fd from list 
void remove_client(int fd) {
    for (int i = 0; i < client_count; i++) {
        if (clients[i].fd == fd) {
            clients[i] = clients[--client_count];
            break;
        }
    }
}

//void broadcast() - iterates through clients and sends char *message to everyone but the sender
void broadcast(int sender_fd, char *message, int len) {
    for (int i = 0; i < client_count; i++) {
        if (clients[i].fd != sender_fd) {
            write(clients[i].fd, message, len);
        }
    }
}

int main() {
    int server_fd;    //file descriptor for server socket 
    struct sockaddr_in address;   //holds ip address/port #
    int addrlen = sizeof(address); 

    //socket() - creates server socket/returns file descriptor 
    server_fd = socket(AF_INET, SOCK_STREAM, 0); //AF_INET: use IPv4 | SOCK_STREAM: use TCP | 0: lets OS pick protocol 
    if (server_fd == -1) { perror("socket"); exit(1); }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));     //setsockopt() - allows port reuse after server restart 

    //bind()-
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;   //INADOR_ANY: listen everywhere available, not just a specific IP 
    address.sin_port = htons(PORT);     //setting port to 8080/converts port # to network byte order (htons)
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
    event.events = EPOLLIN;
    event.data.fd = server_fd;
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &event);

    printf("Server listening on port %d\n", PORT);

    // 7. Event loop
    struct epoll_event events[MAX_EVENTS];
    while (1) {
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
                    buffer[strcspn(buffer, "\r\n")] = '\0'; // strip newline

                    for (int j = 0; j < client_count; j++) {
                        if (clients[j].fd == fd) {
                            if (!clients[j].has_username) {
                                // expecting LOGIN username password
                                if (strncmp(buffer, "LOGIN ", 6) == 0) {
                                    char *rest = buffer + 6;        // skip "LOGIN "
                                    char *space = strchr(rest, ' ');
                                    if (space) *space = '\0';       // null terminate at space, ignore password
                                    strncpy(clients[j].username, rest, 63);
                                    clients[j].has_username = 1;
                                    printf("fd=%d logged in as: %s\n", fd, clients[j].username);
                                    write(fd, "OK\n", 3);

                                    char welcome[128];
                                    snprintf(welcome, sizeof(welcome), "%s joined the chat\n", clients[j].username);
                                    broadcast(fd, welcome, strlen(welcome));
                                } else {
                                    write(fd, "ERROR\n", 6);
                                }
                            } else {
                                // expecting MSG text
                                if (strncmp(buffer, "MSG ", 4) == 0) {
                                    char *msg = buffer + 4;         // skip "MSG "
                                    char formatted[BUFFER_SIZE + 70];
                                    snprintf(formatted, sizeof(formatted), "%s: %s\n", clients[j].username, msg);
                                    printf("%s", formatted);
                                    broadcast(fd, formatted, strlen(formatted));
                                }
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

    close(server_fd);
    return 0;
}

//set_nonblocking() - makes a socket non-blocking, read/accept return instantly. 
// (fcntl -> linux system call, allows you to get/change properties of a file descriptor)
void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);      //F_GETFL = get flags
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);     //F_SETFL = set flags OR adds 0_NONBLOCK to existing flags 
}