"""
Plan adjustment functions for the ReAct application.
Allows for dynamic modification of plans during execution.
"""
import json
import streamlit as st
from datetime import datetime
from config import TOOL_DESCRIPTIONS
from utils.status import log_debug

def adjust_plan(client, plan, current_step_index, context, observation, executor_model):
    """
    Dynamically adjusts the plan based on execution results.
    
    Args:
        client: The LLM client
        plan: The current plan
        current_step_index: The index of the current step
        context: The execution context
        observation: The observation from the current step
        executor_model: The model to use for plan adjustment
    
    Returns:
        tuple: (adjusted_plan, should_continue, next_step_index, status_message)
    """
    # If we're at the last step, no need to adjust
    if current_step_index >= len(plan) - 1:
        return plan, True, current_step_index + 1, None
    
    # Check if the current step failed
    current_step = plan[current_step_index]
    if "error" in observation.lower() or "failed" in observation.lower():
        # The step failed, we need to adjust the plan
        return handle_step_failure(client, plan, current_step_index, context, observation, executor_model)
    
    # Check if we need to add additional steps based on the observation
    if needs_additional_steps(observation):
        return add_additional_steps(client, plan, current_step_index, context, observation, executor_model)
    
    # Default: continue with the original plan
    return plan, True, current_step_index + 1, None

def handle_step_failure(client, plan, current_step_index, context, observation, executor_model):
    """Handle a failed step by creating a recovery plan."""
    current_step = plan[current_step_index]
    
    # Create a prompt for the LLM to generate a recovery plan
    system_prompt = f"""You are a plan adjustment specialist. The current execution step has failed.
Your task is to analyze the failure and suggest how to modify the plan to recover.

Current Plan:
{json.dumps(plan, indent=2)}

Failed Step (index {current_step_index}):
{json.dumps(current_step, indent=2)}

Error Observation:
{observation}

Context:
{json.dumps(context, indent=2)}

You have these options:
1. RETRY: Suggest retrying the same step with modified parameters
2. REPLACE: Replace the failed step with one or more alternative steps
3. SKIP: Skip the failed step and continue with the next step
4. ABORT: Abort the plan execution if recovery is not possible

Respond with a JSON object with the following structure:
{{
  "action": "RETRY|REPLACE|SKIP|ABORT",
  "reason": "Detailed explanation of your decision",
  "new_steps": [] // Only for REPLACE action, array of new step objects
}}

For REPLACE action, each new step should have the same structure as existing steps:
{{
  "step_id": integer,
  "description": "Step description",
  "tool_suggestion": "tool_name",
  "dependencies": [list of step_ids],
  "status": "Pending",
  "result": null
}}
"""
    
    try:
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze the failed step and suggest a recovery plan."}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        adjustment = json.loads(response_content)
        
        action = adjustment.get("action", "ABORT")
        reason = adjustment.get("reason", "No reason provided")
        
        if action == "RETRY":
            # Modify the current step based on the failure
            plan[current_step_index]["status"] = "Pending"  # Reset status
            plan[current_step_index]["result"] = None  # Clear result
            # Add a note about the retry
            plan[current_step_index]["description"] += f" (Retry after failure: {reason})"
            return plan, True, current_step_index, f"🔄 Retrying step {current_step_index + 1}: {reason}"
            
        elif action == "REPLACE":
            # Replace the failed step with new steps
            new_steps = adjustment.get("new_steps", [])
            if not new_steps:
                return plan, False, -2, f"❌ Plan adjustment failed: Replacement steps not provided"
            
            # Remove the failed step
            failed_step = plan.pop(current_step_index)
            
            # Insert new steps at the current position
            for i, new_step in enumerate(new_steps):
                # Ensure step_id is sequential
                new_step["step_id"] = current_step_index + i + 1
                plan.insert(current_step_index + i, new_step)
            
            # Adjust step_ids for all subsequent steps
            for i in range(current_step_index + len(new_steps), len(plan)):
                plan[i]["step_id"] = i + 1
            
            # Adjust dependencies for all steps
            for step in plan:
                # Update dependencies that pointed to steps after the failed step
                step["dependencies"] = [dep if dep <= failed_step["step_id"] else dep + len(new_steps) - 1 
                                       for dep in step["dependencies"]]
            
            return plan, True, current_step_index, f"🔄 Replaced failed step with {len(new_steps)} new steps: {reason}"
            
        elif action == "SKIP":
            # Mark the current step as skipped and move to the next
            plan[current_step_index]["status"] = "Skipped"
            plan[current_step_index]["result"] = f"Skipped: {reason}"
            return plan, True, current_step_index + 1, f"⏭️ Skipping failed step: {reason}"
            
        else:  # ABORT or unknown action
            return plan, False, -2, f"❌ Plan execution aborted: {reason}"
            
    except Exception as e:
        st.error(f"Error during plan adjustment: {str(e)}")
        return plan, False, -2, f"❌ Plan adjustment failed: {str(e)}"

def needs_additional_steps(observation):
    """Determine if additional steps are needed based on the observation."""
    # This is a simple heuristic - in a real system, you'd want more sophisticated detection
    indicators = [
        "additional steps needed",
        "need more information",
        "requires further processing",
        "incomplete result",
        "partial information",
        "need to iterate",
        "more steps required"
    ]
    
    return any(indicator.lower() in observation.lower() for indicator in indicators)

def add_additional_steps(client, plan, current_step_index, context, observation, executor_model):
    """Add additional steps to the plan based on the observation."""
    current_step = plan[current_step_index]
    
    # Create a prompt for the LLM to generate additional steps
    system_prompt = f"""You are a plan enhancement specialist. The current execution step has completed,
but the observation indicates that additional steps are needed.

Current Plan:
{json.dumps(plan, indent=2)}

Current Step (index {current_step_index}):
{json.dumps(current_step, indent=2)}

Observation:
{observation}

Context:
{json.dumps(context, indent=2)}

Your task is to suggest additional steps to insert after the current step.

Respond with a JSON object with the following structure:
{{
  "reason": "Detailed explanation of why additional steps are needed",
  "new_steps": [] // Array of new step objects to insert
}}

Each new step should have the same structure as existing steps:
{{
  "step_id": integer,
  "description": "Step description",
  "tool_suggestion": "tool_name",
  "dependencies": [list of step_ids],
  "status": "Pending",
  "result": null
}}
"""
    
    try:
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze the observation and suggest additional steps."}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        adjustment = json.loads(response_content)
        
        reason = adjustment.get("reason", "No reason provided")
        new_steps = adjustment.get("new_steps", [])
        
        if not new_steps:
            # No additional steps needed, continue with the original plan
            return plan, True, current_step_index + 1, None
        
        # Insert new steps after the current step
        for i, new_step in enumerate(new_steps):
            # Ensure step_id is sequential
            new_step["step_id"] = current_step_index + i + 2  # +2 because we're inserting after the current step
            plan.insert(current_step_index + i + 1, new_step)
        
        # Adjust step_ids for all subsequent steps
        for i in range(current_step_index + len(new_steps) + 1, len(plan)):
            plan[i]["step_id"] = i + 1
        
        # Adjust dependencies for all steps
        for step in plan:
            # Update dependencies that pointed to steps after the current step
            if step["step_id"] > current_step_index + len(new_steps) + 1:
                step["dependencies"] = [dep if dep <= current_step_index + 1 else dep + len(new_steps) 
                                      for dep in step["dependencies"]]
        
        return plan, True, current_step_index + 1, f"➕ Added {len(new_steps)} new steps: {reason}"
        
    except Exception as e:
        st.error(f"Error adding additional steps: {str(e)}")
        # Continue with the original plan despite the error
        return plan, True, current_step_index + 1, f"⚠️ Failed to add additional steps: {str(e)}"
