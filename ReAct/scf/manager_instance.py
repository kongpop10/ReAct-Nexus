"""
Module to initialize and provide access to the SCF Manager instance.
This avoids circular imports between main.py and ui/chat.py.
"""
import os
from scf import SCFManager

# Initialize SCF Manager
# Use the consolidated configuration file
scf_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scf_config.json")
scf_manager = SCFManager(scf_config_path)
