"""
Specialized Component Framework (SCF) Manager for the ReAct application.
Handles component routing, coordination, and execution.
"""
import os
import json
import re
import streamlit as st
from config import WORKSPACE_DIR

class SCFManager:
    """Manages Specialized Component Framework for complex queries."""

    def __init__(self, config_path=None):
        """Initialize the SCF Manager with a configuration file."""
        self.config_path = config_path or os.path.join(WORKSPACE_DIR, "scf_config.json")
        self.components = {}
        self.routing_rules = []
        self.default_component = None
        self.load_config()

    def load_config(self):
        """Load the SCF configuration from a JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.components = {comp['name']: comp for comp in config.get('components', [])}
                    self.routing_rules = config.get('routing_rules', [])
                    self.default_component = config.get('default_component', 'planner')
                return True
            else:
                st.warning(f"SCF configuration file not found at {self.config_path}")
                return False
        except Exception as e:
            st.error(f"Error loading SCF configuration: {str(e)}")
            return False

    def route_query(self, query):
        """Route a query to the appropriate component based on routing rules."""
        # Check each routing rule for a match
        for rule in self.routing_rules:
            pattern = rule.get('pattern', '')
            if re.search(pattern, query, re.IGNORECASE):
                component_name = rule.get('component')
                if component_name in self.components:
                    return component_name

        # If no match found, use the default component
        return self.default_component

    def get_component_prompt(self, component_name):
        """Get the system prompt for a specific component."""
        component = self.components.get(component_name)
        if component:
            return component.get('system_prompt', '')
        return None

    def get_component_capabilities(self, component_name):
        """Get the capabilities (allowed tools) for a specific component."""
        component = self.components.get(component_name)
        if component:
            capabilities = component.get('capabilities', [])
            # If 'all' is in capabilities, return all tools
            if 'all' in capabilities:
                return None  # None means all tools are allowed
            return capabilities
        return []

    def execute_with_component(self, client, query, component_name, model):
        """Execute a query using a specific component."""
        from llm.planner import run_planner
        from llm.executor import run_executor_step

        # Get component-specific system prompt
        system_prompt = self.get_component_prompt(component_name)
        capabilities = self.get_component_capabilities(component_name)

        # Store component info in context for use during execution
        st.session_state.context['current_component'] = component_name
        st.session_state.context['component_capabilities'] = capabilities

        # Log the component being used
        if 'status_container' in st.session_state:
            st.session_state.status_container.info(f"🧠 Using {component_name} component for this query")

        # Generate plan with component-specific context
        plan = run_planner(client, query, model, system_prompt, capabilities)

        return plan

    def coordinate_components(self, client, query):
        """Coordinate multiple components for a complex query."""
        # This is a placeholder for more sophisticated coordination logic
        # For now, we'll just route to a single component
        component_name = self.route_query(query)
        return self.execute_with_component(client, query, component_name, st.session_state.planner_model)
