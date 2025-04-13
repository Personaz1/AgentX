#!/usr/bin/env python3
import socket
import ssl
import json
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, Tuple
import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from agent_protocol.shared.protocol import Command, Response, create_status_command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_communication')

# Secure communication class that handles encryption/decryption
class SecureChannel:
    def __init__(self, key: Optional[str] = None):
        # Generate or use provided encryption key
        if key:
            # Use provided key
            self.key = hashlib.sha256(key.encode()).digest()
        else:
            # Generate a random key
            self.key = os.urandom(32)
            
    def encrypt(self, data: str) -> bytes:
        """Encrypt data with AES."""
        padder = padding.PKCS7(128).padder()
        iv = os.urandom(16)
        padded_data = padder.update(data.encode()) + padder.finalize()
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data
        return base64.b64encode(iv + encrypted_data)
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data with AES."""
        raw_data = base64.b64decode(encrypted_data)
        iv = raw_data[:16]
        ciphertext = raw_data[16:]
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode()
    
    def get_key_base64(self) -> str:
        """Get the base64 encoded encryption key."""
        return base64.b64encode(self.key).decode()
    
    @classmethod
    def from_base64_key(cls, base64_key: str) -> 'SecureChannel':
        """Create a SecureChannel from a base64 encoded key."""
        key = base64.b64decode(base64_key)
        instance = cls()
        instance.key = key
        return instance

# Base Communication Server and Client
class CommunicationServer:
    def __init__(
        self, 
        host: str = '0.0.0.0', 
        port: int = 8765, 
        secure_channel: Optional[SecureChannel] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.secure_channel = secure_channel or SecureChannel()
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.running = False
        self.server_socket = None
        self.clients = []
        self.command_handlers = {}
        
    def start(self):
        """Start the communication server."""
        if self.running:
            logger.warning("Server is already running")
            return
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow port reuse
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        if self.use_ssl and self.cert_file and self.key_file:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            self.server_socket = context.wrap_socket(self.server_socket, server_side=True)
        
        self.running = True
        logger.info(f"Server started on {self.host}:{self.port}")
        
        # Start accepting connections in a separate thread
        threading.Thread(target=self._accept_connections, daemon=True).start()
    
    def stop(self):
        """Stop the communication server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        self.clients = []
        logger.info("Server stopped")
    
    def _accept_connections(self):
        """Accept client connections."""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)
                logger.info(f"Client connected: {addr}")
                
                # Handle client communication in a separate thread
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                    time.sleep(0.1)
    
    def _handle_client(self, client_socket, addr):
        """Handle communication with a client."""
        try:
            while self.running:
                # Receive message size (4 bytes header for message length)
                header = client_socket.recv(4)
                if not header:
                    break
                
                message_size = int.from_bytes(header, byteorder='big')
                encrypted_data = b''
                
                # Receive the full message
                remaining = message_size
                while remaining > 0:
                    chunk = client_socket.recv(min(remaining, 4096))
                    if not chunk:
                        break
                    encrypted_data += chunk
                    remaining -= len(chunk)
                
                if not encrypted_data:
                    break
                
                # Decrypt the message
                json_data = self.secure_channel.decrypt(encrypted_data)
                command = Command.from_json(json_data)
                
                # Process the command
                response = self._process_command(command)
                
                # Send the response
                self._send_response(client_socket, response)
                
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            # Clean up
            try:
                client_socket.close()
                self.clients.remove(client_socket)
                logger.info(f"Client disconnected: {addr}")
            except:
                pass
    
    def _process_command(self, command: Command) -> Response:
        """Process a received command."""
        handler = self.command_handlers.get(command.command_type.value)
        if handler:
            try:
                return handler(command)
            except Exception as e:
                logger.error(f"Error processing command {command.command_id}: {e}")
                return Response(
                    command_id=command.command_id,
                    status="error",
                    data={},
                    error_message=str(e)
                )
        else:
            return Response(
                command_id=command.command_id,
                status="error",
                data={},
                error_message=f"No handler for command type: {command.command_type.value}"
            )
    
    def _send_response(self, client_socket, response: Response):
        """Send a response to a client."""
        json_data = response.to_json()
        encrypted_data = self.secure_channel.encrypt(json_data)
        
        # Send message size header followed by the encrypted data
        message_size = len(encrypted_data)
        client_socket.send(message_size.to_bytes(4, byteorder='big'))
        client_socket.send(encrypted_data)
    
    def register_command_handler(self, command_type: str, handler: Callable[[Command], Response]):
        """Register a handler for a specific command type."""
        self.command_handlers[command_type] = handler

class CommunicationClient:
    def __init__(
        self, 
        host: str, 
        port: int, 
        secure_channel: Optional[SecureChannel] = None,
        use_ssl: bool = False,
        cert_file: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.secure_channel = secure_channel or SecureChannel()
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                if self.cert_file:
                    context.load_verify_locations(cafile=self.cert_file)
                self.socket = context.wrap_socket(
                    self.socket, 
                    server_hostname=self.host
                )
            
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to server {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.connected = False
                logger.info("Disconnected from server")
    
    def send_command(self, command: Command) -> Optional[Response]:
        """Send a command to the server and get the response."""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Encrypt and send the command
            json_data = command.to_json()
            encrypted_data = self.secure_channel.encrypt(json_data)
            
            # Send message size header followed by the encrypted data
            message_size = len(encrypted_data)
            self.socket.send(message_size.to_bytes(4, byteorder='big'))
            self.socket.send(encrypted_data)
            
            # Receive the response
            header = self.socket.recv(4)
            if not header:
                logger.error("Connection closed by server")
                self.disconnect()
                return None
            
            message_size = int.from_bytes(header, byteorder='big')
            encrypted_data = b''
            
            # Receive the full response
            remaining = message_size
            while remaining > 0:
                chunk = self.socket.recv(min(remaining, 4096))
                if not chunk:
                    break
                encrypted_data += chunk
                remaining -= len(chunk)
            
            if not encrypted_data:
                logger.error("Empty response from server")
                return None
            
            # Decrypt the response
            json_data = self.secure_channel.decrypt(encrypted_data)
            return Response.from_json(json_data)
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.disconnect()
            return None
    
    def ping(self) -> bool:
        """Ping the server to check connectivity."""
        response = self.send_command(create_status_command())
        return response is not None and response.status.value == "success" 