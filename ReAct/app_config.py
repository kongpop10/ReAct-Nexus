"""
Application configuration and shared instances for the ReAct application.
This module helps avoid circular imports between main.py and UI components.
"""
import os
from scf.manager_instance import scf_manager

# Export the SCF manager instance
__all__ = ['scf_manager']
