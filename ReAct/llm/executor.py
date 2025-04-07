"""
Execution functions for the ReAct application.
"""
import json
import traceback
import streamlit as st
from tools import TOOLS
from utils.status import log_debug

def run_executor_step(client, step: dict, context: dict, executor_model: str) -> tuple[str, str, str]:
    """Executes a single step using the Executor LLM and tools (simulates ReAct)."""
    if not client:
        return "Error: API Client not initialized.", "Error", "Cannot run Executor (API key missing?)."

    step_desc = step['description']
    tool_suggestion = step['tool_suggestion']

    # Check if we're using a specific component from MCP
    current_component = context.get('current_component', None)
    component_capabilities = context.get('component_capabilities', None)

    # Filter available tools if component has restricted capabilities
    available_tools = list(TOOLS.keys())
    if component_capabilities is not None:
        available_tools = component_capabilities

    # Customize prompt based on component
    if current_component:
        agent_description = f"You are a specialized {current_component} agent. Your goal is to perform the action described in the current step."
    else:
        agent_description = "You are an execution agent. Your goal is to perform the action described in the current step."

    # --- Reason Phase ---
    reasoning_prompt = f"""{agent_description}
Current Step: "{step_desc}"
Suggested Tool: {tool_suggestion}
Available Tools: {available_tools}
Context from previous steps: {json.dumps(context, indent=2)}

1.  **Reason:** Analyze the step description and context. Decide which tool is *best* suited to accomplish this step. If a tool is needed, determine the *exact* arguments required, drawing information from the context if necessary. Pay close attention to the parameter names expected by each tool.

   **REQUIRED PARAMETERS FOR TOOLS:**
   - `web_search` requires a `query` parameter (string)
   - `web_scrape` requires a `url` parameter (string)
   - `get_stock_data` requires a `symbol` parameter (string)
   - `read_file` requires a `filename` parameter (string)
   - `write_file` requires `filename` (string) and `content` (string) parameters, with optional `append` (boolean)
   - `list_files` has an optional `directory` parameter (string)
   - `delete_file` requires a `filename` parameter (string)
   - `execute_python` requires a `code` parameter (string)
   - `memory_get` requires a `key` parameter (string) - NOT `memory_key`
   - `memory_set` requires `key` (string) and `value` (string) parameters
   - `memory_list` takes no parameters

   **IMPORTANT FOR FILE OPERATIONS:**
   - When the user wants to ADD, APPEND, or UPDATE content in an existing file, use `write_file` with `append=true`
   - When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, use `write_file` with `append=false` (default)
   - When the user wants to DELETE or REMOVE a file, use `delete_file` with the filename
   - Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
   - Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

   **IMPORTANT FOR WEB SCRAPING AND KNOWLEDGE:**
   - When scraping a URL for knowledge, use `web_scrape` to get the content and then `memory_set` to store it
   - After scraping a URL, store the content in memory with a descriptive key like "scraped_[domain]" for future reference
   - When answering questions about previously scraped content, use `memory_get` to retrieve the stored content

   If no tool is needed (e.g., summarizing context), decide on the action.
2.  **Action Format:** Respond with a JSON object containing the chosen tool and its arguments. The format *must* be:
    `{{"tool": "tool_name", "args": {{"arg_name1": "value1", "arg_name2": "value2", "reasoning": "Your detailed reasoning here"}}}}`

    Always include a "reasoning" field in the args object that explains your thought process.

    If no tool is needed for this step (e.g., the step is just about reasoning or formatting based on context), use:
    `{{"tool": "None", "args": {{"comment": "Reasoning or action description", "reasoning": "Your detailed reasoning here"}}}}`

Provide *only* the JSON object as your response.
"""
    reasoning = "Reasoning not initiated."
    action_json_str = ""
    action_str = "Error" # Default action string
    observation = "Execution did not proceed." # Default observation

    # We'll extract the reasoning from the LLM response later

    try:
        log_debug(f"Attempting LLM call for step: {step_desc}") # Debug output
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": reasoning_prompt},
                {"role": "user", "content": f"Execute step: {step_desc}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        log_debug(f"LLM call completed. Completion object: {completion}") # Debug output

        # --- ROBUSTNESS CHECKS ---
        if not completion:
            reasoning = "Executor Error: LLM API call returned None object."
            st.error(reasoning)
            return reasoning, action_str, "LLM API response invalid (None completion)."

        if not completion.choices:
            reasoning = "Executor Error: LLM API call returned no 'choices'."
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            return reasoning, action_str, "LLM API response invalid (no choices)."

        if len(completion.choices) == 0:
            reasoning = "Executor Error: LLM API call returned empty 'choices' list."
            finish_reason = completion.usage if hasattr(completion, 'usage') else 'N/A' # Check if usage info exists, maybe finish reason is there?
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            st.warning(f"Potentially check finish reason if available: {finish_reason}")
            return reasoning, action_str, "LLM API response invalid (empty choices)."

        choice = completion.choices[0]
        if choice.message is None or choice.message.content is None:
            finish_reason = choice.finish_reason if hasattr(choice, 'finish_reason') else 'N/A'
            reasoning = f"Executor Error: LLM API response missing 'message' or 'content'. Finish Reason: {finish_reason}"
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            if finish_reason == 'content_filter':
                 st.warning("Content filter likely triggered.")
                 observation = f"LLM refused to respond due to content filter (Finish Reason: {finish_reason})."
            else:
                 observation = f"LLM API response invalid (missing content). Finish Reason: {finish_reason}"
            return reasoning, action_str, observation

        action_json_str = choice.message.content
        log_debug(f"Raw action JSON: {action_json_str}") # Debug output

        # Extract reasoning from the LLM response
        # The LLM should be thinking about the reasoning in its internal process
        # before generating the action JSON, so we'll consider the content as containing
        # the reasoning implicitly

        # Parse action JSON
        try:
            action = json.loads(action_json_str)

            # Validate the action JSON structure
            if not isinstance(action, dict):
                reasoning = "Executor Error: Action must be a JSON object/dictionary"
                st.error(reasoning)
                return reasoning, "Error", "Invalid action format: not a JSON object"

            # Check for required fields
            if 'tool' not in action:
                reasoning = "Executor Error: Missing 'tool' field in action JSON"
                st.error(reasoning)
                return reasoning, "Error", "Missing 'tool' field in action"

            if 'args' not in action or not isinstance(action['args'], dict):
                reasoning = "Executor Error: Missing or invalid 'args' field in action JSON"
                st.error(reasoning)
                return reasoning, "Error", "Missing or invalid 'args' field in action"

            # Update reasoning with the actual reasoning from the LLM
            # Extract reasoning from the 'reasoning' field in args if available
            if action['tool'] == 'None':
                action_str = action['args'].get('comment', 'No action required')
                reasoning = action['args'].get('reasoning', action['args'].get('comment', 'No explicit reasoning provided'))
            else:
                # Remove reasoning from the displayed action string to avoid duplication
                action_args = action['args'].copy()
                extracted_reasoning = action_args.pop('reasoning', None)
                action_str = f"{action['tool']}({json.dumps(action_args)})"

                # Use the extracted reasoning if available, otherwise construct a default one
                if extracted_reasoning:
                    reasoning = extracted_reasoning
                else:
                    reasoning = f"Based on the step description, I need to use the {action['tool']} tool with the following parameters: {json.dumps(action_args, indent=2)}"
        except json.JSONDecodeError as e:
            reasoning = f"Executor Error: Invalid JSON response from LLM: {e}"
            st.error(reasoning)
            st.error(f"Invalid JSON content: {action_json_str}")
            return reasoning, "Error", "Invalid action JSON format"
        except KeyError as e:
            reasoning = f"Executor Error: Missing required key in action JSON: {e}"
            st.error(reasoning)
            st.error(f"Malformed action JSON: {action_json_str}")
            return reasoning, "Error", "Malformed action JSON structure"

        # --- Execute Tool ---
        try:
            if action['tool'] != "None":
                # Remove the reasoning field from args before passing to the tool function
                tool_args = action['args'].copy()
                if 'reasoning' in tool_args:
                    tool_args.pop('reasoning')
                # Compatibility fix: remap 'memory_key' to 'key' if present for memory_get
                if action['tool'] == "memory_get":
                    if 'memory_key' in tool_args:
                        tool_args['key'] = tool_args.pop('memory_key')
                    # Ensure key parameter exists for memory_get
                    if 'key' not in tool_args or not tool_args['key']:
                        raise ValueError("memory_get requires a 'key' parameter")

                log_debug(f"\n\nAttempting to execute: {action['tool']} with args {tool_args}")

                # Check if the tool is allowed for the current component
                component_capabilities = context.get('component_capabilities', None)
                # If component_capabilities is None, all tools are allowed
                # If component_capabilities contains 'all', all tools are allowed
                # Otherwise, check if the specific tool is in the capabilities list
                if (component_capabilities is not None and
                    'all' not in component_capabilities and
                    action['tool'] not in component_capabilities):
                    # Log the error for debugging
                    log_debug(f"Tool '{action['tool']}' is not allowed for the current component. Allowed tools: {component_capabilities}")
                    # Use a more user-friendly error message
                    raise ValueError(f"Tool '{action['tool']}' is not allowed for the current component")

                if action['tool'] not in TOOLS:
                    raise ValueError(f"Tool '{action['tool']}' not registered in TOOLS dictionary")

                tool_func = TOOLS[action['tool']]

                # Validate arguments are in keyword form
                if not isinstance(tool_args, dict):
                    raise TypeError(f"Tool arguments must be dictionary, got {type(tool_args).__name__}")

                # Check for required arguments based on tool type
                if action['tool'] == "memory_get" and ('key' not in tool_args or not tool_args['key']):
                    raise ValueError("memory_get requires a 'key' parameter")
                elif action['tool'] == "memory_set" and ('key' not in tool_args or 'value' not in tool_args):
                    raise ValueError("memory_set requires both 'key' and 'value' parameters")
                elif action['tool'] == "web_search" and ('query' not in tool_args or not tool_args['query']):
                    raise ValueError("web_search requires a 'query' parameter")

                observation = tool_func(**tool_args)
                st.success(f"Tool execution completed: {action['tool']}")
            else:
                # For 'None' tool, we just need the comment as observation
                # Make sure we don't include the reasoning field in the observation
                observation = action['args'].get('comment', 'No action required')
        except Exception as e:
            reasoning = f"Tool execution error: {str(e)}"
            st.error(reasoning)
            st.error(traceback.format_exc())
            return reasoning, action_str, f"Tool execution failed: {str(e)}"

        return reasoning, action_str, observation

    except Exception as e:
        reasoning = f"Executor Error: Unexpected error during execution - {str(e)}"
        st.error(reasoning)
        st.error(traceback.format_exc())
        return reasoning, "Error", f"Unexpected error: {str(e)}"
