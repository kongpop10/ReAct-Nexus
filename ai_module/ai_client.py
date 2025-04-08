"""Handles OpenAI API interactions and AI-related logic."""

import streamlit as st
import json
from datetime import datetime
import traceback

def generate_title(messages, client=None):
    """Generate a title based on the conversation messages using the configured LLM model."""
    try:
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]

        if user_messages and client:
            context = "\n".join(user_messages[-3:])
            try:
                title_model = st.session_state.get('title_model', "google/gemini-2.0-flash-exp:free")

                completion = client.chat.completions.create(
                    model=title_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for conversations. Create a short title (5-7 words max) that captures the essence of the conversation."},
                        {"role": "user", "content": f"Generate a short, descriptive title for this conversation:\n{context}"}
                    ],
                    temperature=0.3,
                    max_tokens=20
                )

                if completion and completion.choices and completion.choices[0].message.content:
                    title = completion.choices[0].message.content.strip()
                    title = title.strip('"\'')
                    return title
            except Exception as e:
                st.write(f"Error using Gemini for title generation: {str(e)}")

        if user_messages:
            latest_user_message = user_messages[-1]
            if len(latest_user_message) > 30:
                title = latest_user_message[:30] + "..."
            else:
                title = latest_user_message
            return title
        else:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            return f"Chat on {timestamp_str}"
    except Exception as e:
        st.write(f"Error generating title: {str(e)}")
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"Chat on {timestamp_str}"

def get_openai_client(api_key, base_url="https://openrouter.ai/api/v1"):
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=base_url)

def run_planner(client, user_query: str, planner_model: str) -> list:
    """Generates the initial plan using the Planner LLM. Always returns a list."""
    if not client:
        st.error("API key not configured. Cannot run Planner.")
        return []

    memory_info = ""
    if st.session_state.persistent_memory:
        message_keys = [k for k in st.session_state.persistent_memory.keys() if k.startswith('message_')]
        other_keys = [k for k in st.session_state.persistent_memory.keys() if not k.startswith('message_')]

        memory_sections = []

        if message_keys:
            message_section = "\n\nYou have access to the following information from previous messages:\n"
            for key in message_keys:
                idx = key.split('_')[1]
                message_section += f"- Previous response {idx}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(message_section)

        if other_keys:
            other_section = "\n\nYou have access to the following memory items from previous interactions:\n"
            for key in other_keys:
                other_section += f"- {key}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(other_section)

        if memory_sections:
            memory_info = ''.join(memory_sections)

    system_prompt = f"""You are a meticulous planning agent. Your task is to break down the user's query into a sequence of actionable steps.
Today's Date: {datetime.now().strftime('%Y-%m-%d')}
You have access to the following tools:
{TOOL_DESCRIPTIONS}

**IMPORTANT FOR FILE OPERATIONS:**
- When the user wants to ADD, APPEND, or UPDATE content in an existing file, plan to use `write_file` with `append=true`
- When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, plan to use `write_file` with `append=false` (default)
- When the user wants to DELETE or REMOVE a file, plan to use `delete_file` with the filename
- Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
- Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

**IMPORTANT FOR MEMORY OPERATIONS:**
- Use memory_get, memory_set, and memory_list tools to maintain information across multiple queries
- When the user refers to information from previous interactions, plan to use memory_get to retrieve it
- When you discover information that might be useful in future queries, plan to use memory_set to store it{memory_info}

Based on the user query: "{user_query}"

Generate a structured plan as a JSON list of objects. Each object represents a step and must have the following keys:
- "step_id": A unique integer identifier for the step (starting from 1).
- "description": A clear, concise instruction for what needs to be done in this step.
- "tool_suggestion": The name of the *most likely* tool to be used for this step (must be one of the available tools). If no specific tool is needed (e.g., final reasoning/compilation), suggest "None".
- "dependencies": A list of `step_id`s that must be completed *before* this step can start. Empty list `[]` if no dependencies.
- "status": Initialize this to "Pending".
- "result": Initialize this to `null`.

Ensure the plan is logical, sequential, and covers all aspects of the user query. The final step should typically involve compiling or presenting the result.
Output *only* the JSON list, nothing else before or after.
"""
    try:
        completion = client.chat.completions.create(
            model=planner_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        response_content = completion.choices[0].message.content
        if response_content.strip().startswith("```json"):
            response_content = response_content.strip()[7:-3].strip()
        parsed_json = json.loads(response_content)
        if isinstance(parsed_json, dict) and len(parsed_json) == 1:
            plan_list = list(parsed_json.values())[0]
        elif isinstance(parsed_json, list):
            plan_list = parsed_json
        else:
            raise ValueError("Planner did not return a JSON list.")

        for i, step in enumerate(plan_list):
            if not all(k in step for k in ["step_id", "description", "tool_suggestion", "dependencies", "status", "result"]):
                raise ValueError(f"Step {i+1} is missing required keys.")
            step["step_id"] = i + 1
            step["status"] = "Pending"
            step["result"] = None
        return plan_list
    except json.JSONDecodeError as e:
        st.error(f"Planner Error: Failed to decode JSON response: {e}\nResponse received:\n{response_content}")
        return []
    except Exception as e:
        st.error(f"Planner Error: An unexpected error occurred: {e}\n{traceback.format_exc()}")
        return []

def run_executor_step(client, step: dict, context: dict, executor_model: str) -> tuple:
    """Executes a single step using the Executor LLM and tools (simulates ReAct)."""
    if not client:
        return "Error: API Client not initialized.", "Error", "Cannot run Executor (API key missing?)."

    step_desc = step['description']
    tool_suggestion = step['tool_suggestion']

    reasoning_prompt = f"""You are an execution agent. Your goal is to perform the action described in the current step.
Current Step: "{step_desc}"
Suggested Tool: {tool_suggestion}
Available Tools: {list(TOOLS.keys())}
Context from previous steps: {json.dumps(context, indent=2)}

IMPORTANT:

- When embedding any markdown content, LaTeX, or other text inside JSON string values, you MUST escape all backslashes as double backslashes (`\\\\`).
- Also ensure any special characters like quotes are properly escaped for JSON.
- Failure to do so will produce invalid JSON, which will cause an error.

1.  **Reason:** Analyze the step description and context. Decide which tool is *best* suited to accomplish this step. If a tool is needed, determine the *exact* arguments required, drawing information from the context if necessary. Pay close attention to the parameter names expected by each tool.

   **IMPORTANT FOR FILE OPERATIONS:**
   - When the user wants to ADD, APPEND, or UPDATE content in an existing file, use `write_file` with `append=true`
   - When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, use `write_file` with `append=false` (default)
   - When the user wants to DELETE or REMOVE a file, use `delete_file` with the filename
   - Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
   - Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

   If no tool is needed (e.g., summarizing context), decide on the action.
2.  **Action Format:** Respond with a JSON object containing the chosen tool and its arguments. The format *must* be:
    `{{"tool": "tool_name", "args": {{"arg_name1": "value1", "arg_name2": "value2", "reasoning": "Your detailed reasoning here"}}}}`

    Always include a "reasoning" field in the args object that explains your thought process.

    If no tool is needed for this step (e.g., the step is just about reasoning or formatting based on context), use:
    `{{"tool": "None", "args": {{"comment": "Reasoning or action description", "reasoning": "Your detailed reasoning here"}}}}`

Provide *only* the JSON object as your response.
"""
    try:
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": reasoning_prompt},
                {"role": "user", "content": f"Execute step: {step_desc}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        if not completion or not completion.choices or len(completion.choices) == 0:
            return "Executor Error: LLM API call returned no valid choices.", "Error", "Invalid LLM response."

        choice = completion.choices[0]
        if choice.message is None or choice.message.content is None:
            return "Executor Error: Missing content in LLM response.", "Error", "Invalid LLM response content."

        action_json_str = choice.message.content
        try:
            action = json.loads(action_json_str)
            if action['tool'] == 'None':
                action_str = action['args'].get('comment', 'No action required')
                reasoning = action['args'].get('reasoning', action['args'].get('comment', 'No explicit reasoning provided'))
            else:
                action_args = action['args'].copy()
                extracted_reasoning = action_args.pop('reasoning', None)
                action_str = f"{action['tool']}({json.dumps(action_args)})"
                reasoning = extracted_reasoning or f"Using {action['tool']} with parameters: {json.dumps(action_args)}"
        except Exception as e:
            return f"Executor Error: Failed to parse action JSON: {e}", "Error", "Invalid action JSON."

        try:
            if action['tool'] != "None":
                tool_args = action['args'].copy()
                tool_args.pop('reasoning', None)
                if action['tool'] not in TOOLS:
                    raise ValueError(f"Tool '{action['tool']}' not registered.")
                tool_func = TOOLS[action['tool']]
                if not isinstance(tool_args, dict):
                    raise TypeError("Tool arguments must be a dict.")
                observation = tool_func(**tool_args)
            else:
                observation = action['args'].get('comment', 'No action required')
        except Exception as e:
            reasoning = f"Tool execution error: {str(e)}"
            return reasoning, action_str, f"Tool execution failed: {str(e)}"

        return reasoning, action_str, observation
    except Exception as e:
        reasoning = f"Executor Error: Unexpected error: {str(e)}"
        return reasoning, "Error", f"Unexpected error: {str(e)}"