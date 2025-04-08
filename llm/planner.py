"""
Planning functions for the ReAct application.
"""
import json
import traceback
import streamlit as st
from datetime import datetime
from config import TOOL_DESCRIPTIONS
from utils.status import log_debug

def assess_query_complexity(query: str) -> str:
    """Assess the complexity of a user query based on various factors.

    Returns:
        str: Complexity level - "Low", "Medium", or "High"
    """
    # Simple heuristic-based assessment
    complexity_indicators = [
        "compare", "analyze", "multiple", "several", "complex",
        "relationship", "between", "and then", "afterwards",
        "first", "second", "third", "finally", "if", "else", "otherwise",
        "depending", "based on", "versus", "vs", "different", "similar",
        "pros and cons", "advantages", "disadvantages", "benefits", "drawbacks"
    ]

    # Count sentences
    sentences = [s for s in query.split('.') if s.strip()]

    # Count complexity indicators
    indicator_count = sum(1 for indicator in complexity_indicators if indicator.lower() in query.lower())

    # Count question marks (multiple questions indicate complexity)
    question_count = query.count('?')

    # Assess complexity
    if (len(sentences) > 3 or
        indicator_count > 2 or
        len(query.split()) > 50 or
        question_count > 1):
        return "High"
    elif (len(sentences) > 1 or
          indicator_count > 0 or
          len(query.split()) > 20 or
          question_count > 0):
        return "Medium"
    else:
        return "Low"

def validate_and_assess_plan(plan_list, query_complexity):
    """Validates plan structure and assesses overall complexity.

    Args:
        plan_list (list): The plan steps list to validate
        query_complexity (str): The complexity level of the original query

    Returns:
        list: The validated and potentially enhanced plan
    """
    if not plan_list or len(plan_list) == 0:
        st.error("Empty plan generated. Please try again.")
        return []

    # Check for required keys in each step
    for i, step in enumerate(plan_list):
        if not all(k in step for k in ["step_id", "description", "tool_suggestion", "dependencies", "status", "result"]):
            st.warning(f"Step {i+1} is missing required keys. Fixing...")
            # Add missing keys with default values
            if "step_id" not in step:
                step["step_id"] = i + 1
            if "description" not in step:
                step["description"] = f"Step {i+1}"
            if "tool_suggestion" not in step:
                step["tool_suggestion"] = "None"
            if "dependencies" not in step:
                step["dependencies"] = []
            if "status" not in step:
                step["status"] = "Pending"
            if "result" not in step:
                step["result"] = None

        # Ensure step_ids are sequential
        step["step_id"] = i + 1
        step["status"] = "Pending"
        step["result"] = None

    # Assess plan complexity
    plan_complexity = "Low"
    if len(plan_list) > 7:
        plan_complexity = "Medium"
    if len(plan_list) > 12:
        plan_complexity = "High"

    # Check for non-linear dependencies (increases complexity)
    for step in plan_list:
        if len(step.get("dependencies", [])) > 1:
            # Upgrade complexity level if multiple dependencies exist
            if plan_complexity == "Low":
                plan_complexity = "Medium"
            elif plan_complexity == "Medium":
                plan_complexity = "High"

    # Check for circular dependencies
    dependency_graph = {step["step_id"]: step["dependencies"] for step in plan_list}
    if has_circular_dependencies(dependency_graph):
        st.warning("Plan contains circular dependencies. Fixing...")
        # Fix circular dependencies by removing problematic ones
        for step in plan_list:
            # Simple fix: ensure dependencies only point to earlier steps
            step["dependencies"] = [dep for dep in step["dependencies"] if dep < step["step_id"]]

    # Log plan assessment
    log_debug(f"Plan complexity assessment: {plan_complexity} (Query complexity: {query_complexity})")
    if plan_complexity == "High" and 'status_container' in st.session_state:
        st.session_state.status_container.info(f"🧠 Complex plan with {len(plan_list)} steps. Execution may take longer.")

    return plan_list

def has_circular_dependencies(dependency_graph):
    """Check if the dependency graph has circular dependencies.

    Args:
        dependency_graph (dict): Dictionary mapping step_id to list of dependencies

    Returns:
        bool: True if circular dependencies exist, False otherwise
    """
    visited = set()
    path = set()

    def dfs(node):
        visited.add(node)
        path.add(node)

        for neighbor in dependency_graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in path:
                return True

        path.remove(node)
        return False

    for node in dependency_graph:
        if node not in visited:
            if dfs(node):
                return True

    return False

def run_planner(client, user_query: str, planner_model: str, custom_system_prompt=None, allowed_tools=None) -> list:
    """Generates the initial plan using the Planner LLM. Always returns a list."""
    if not client:
        st.error("API key not configured. Cannot run Planner.")
        return []

    # Assess query complexity
    complexity = assess_query_complexity(user_query)
    log_debug(f"Query complexity assessment: {complexity}")

    # Adjust temperature based on complexity
    temperature = 0.2  # Default
    if complexity == "High":
        temperature = 0.1  # Lower temperature for more deterministic output on complex queries
        if 'status_container' in st.session_state:
            st.session_state.status_container.info("🧠 Complex query detected. Using enhanced planning...")

    # Get the current memory state to include in the prompt
    memory_info = ""
    if st.session_state.persistent_memory:
        # Separate message memories from other memories for better organization
        message_keys = [k for k in st.session_state.persistent_memory.keys() if k.startswith('message_')]
        other_keys = [k for k in st.session_state.persistent_memory.keys() if not k.startswith('message_')]

        memory_sections = []

        # Add message memories if available
        if message_keys:
            message_section = "\n\nYou have access to the following information from previous messages:\n"
            for key in message_keys:
                # Extract the message index from the key
                idx = key.split('_')[1]
                message_section += f"- Previous response {idx}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(message_section)

        # Add other memories if available
        if other_keys:
            other_section = "\n\nYou have access to the following memory items from previous interactions:\n"
            for key in other_keys:
                other_section += f"- {key}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(other_section)

        # Combine all memory sections
        if memory_sections:
            memory_info = ''.join(memory_sections)

    # Filter tool descriptions if allowed_tools is specified
    tool_descriptions = TOOL_DESCRIPTIONS
    if allowed_tools is not None:
        # Filter the tool descriptions to only include allowed tools
        tool_descriptions = "\n".join([line for line in TOOL_DESCRIPTIONS.split('\n')
                                if any(tool in line for tool in allowed_tools) or not line.strip().startswith('-')])

    # Use custom system prompt if provided, otherwise use the default
    if custom_system_prompt:
        base_prompt = custom_system_prompt
    else:
        base_prompt = "You are a meticulous planning agent. Your task is to break down the user's query into a sequence of actionable steps."

    system_prompt = f"""{base_prompt}
Today's Date: {datetime.now().strftime('%Y-%m-%d')}
You have access to the following tools:
{tool_descriptions}

**IMPORTANT FOR FILE OPERATIONS:**
- When the user wants to ADD, APPEND, or UPDATE content in an existing file, plan to use `write_file` with `append=true`
- When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, plan to use `write_file` with `append=false` (default)
- When the user wants to DELETE or REMOVE a file, plan to use `delete_file` with the filename
- Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
- After performing a web search, URLs are extracted and stored in memory under the key "search_result_urls". Use `memory_get("search_result_urls")` to retrieve the list of URLs for scraping or further processing.

- Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

**IMPORTANT FOR WEB SCRAPING AND KNOWLEDGE:**
- When the user wants to scrape a URL and use it as knowledge, plan to use `web_scrape` to get the content and then `memory_set` to store it
- After scraping a URL, store the content in memory with a descriptive key like "scraped_[domain]" for future reference
- When answering questions about previously scraped content, plan to use `memory_get` to retrieve the stored content

**IMPORTANT FOR KNOWLEDGE BASE OPERATIONS:**
- When the user wants to add a web page to the knowledge base, plan to use `kb_add_web` with the URL
- When the user wants to add a local markdown file to the knowledge base, plan to use `kb_add_file` with the filename
- When the user wants to list all knowledge base entries, plan to use `kb_list`
- When the user wants to retrieve content from the knowledge base, plan to use `kb_get` with the entry_id or memory_key
- When the user wants to delete a knowledge base entry, plan to use `kb_delete` with the entry_id
- When the user wants to search the knowledge base, plan to use `kb_search` with the query
- Knowledge base entries are automatically added to memory and can be accessed in future conversations

**IMPORTANT FOR MEMORY OPERATIONS:**
- Use memory_get, memory_set, and memory_list tools to maintain information across multiple queries
- When the user refers to information from previous interactions, plan to use memory_get to retrieve it
- When you discover information that might be useful in future queries, plan to use memory_set to store it{memory_info}

**GUIDELINES FOR COMPLEX QUERIES:**
- For multi-part queries, break down each part into separate steps with clear dependencies
- For data-intensive tasks, include steps for data validation and error handling
- For tasks requiring multiple sources, plan to gather all information before synthesis
- For tasks with potential failure points, include fallback steps or verification steps
- For tasks requiring comparisons or analysis, break down into data gathering, analysis, and synthesis steps
- For tasks involving multiple tools in sequence, ensure proper data flow between steps
- For tasks with conditional logic, create separate steps for each condition and use dependencies appropriately
- For tasks requiring iterative processing, create steps that can handle batches or chunks of data
- For tasks with ambiguity, include steps to clarify requirements or validate assumptions

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
            temperature=temperature,  # Use complexity-based temperature
            response_format={"type": "json_object"} # Request JSON output if model supports it
        )
        response_content = completion.choices[0].message.content
        # Sometimes the response might be wrapped in ```json ... ```, try to extract
        if response_content.strip().startswith("```json"):
             response_content = response_content.strip()[7:-3].strip()
        # The model might return a dict with a key like "plan"
        parsed_json = json.loads(response_content)
        if isinstance(parsed_json, dict) and len(parsed_json) == 1:
             plan_list = list(parsed_json.values())[0] # Get the list if it's nested
        elif isinstance(parsed_json, list):
             plan_list = parsed_json
        else:
             raise ValueError("Planner did not return a JSON list.")

        # Validate and assess plan structure
        plan_list = validate_and_assess_plan(plan_list, complexity)
        return plan_list
    except json.JSONDecodeError as e:
        st.error(f"Planner Error: Failed to decode JSON response: {e}\nResponse received:\n{response_content}")
        return []
    except Exception as e:
        st.error(f"Planner Error: An unexpected error occurred: {e}\n{traceback.format_exc()}")
        return []
