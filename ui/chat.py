"""
Chat interface components for the ReAct application.
"""
import streamlit as st
import re
import json
import time
from tools.web_tools import extract_urls_from_markdown, detect_url_scrape_request
from utils.conversation import auto_save_conversation
from utils.status import log_debug
from llm.planner import run_planner, assess_query_complexity
from llm.executor import run_executor_step
from llm.summarizer import generate_final_response
from llm.plan_adjuster import adjust_plan
from data_acquisition.news_scraper import WebScraper

def delete_message(idx):
    """Delete a message from the chat history and update memory."""
    if 0 <= idx < len(st.session_state.messages):
        # Remove the message from the messages list
        st.session_state.messages.pop(idx)

        # Remove the message from memory tracking
        if idx in st.session_state.message_memories:
            del st.session_state.message_memories[idx]

        # Update memory keys for messages after the deleted one
        updated_memories = {}
        for memory_idx, memory_data in st.session_state.message_memories.items():
            if memory_idx > idx:
                # Shift indices down by 1 for all messages after the deleted one
                updated_memories[memory_idx - 1] = memory_data
            else:
                # Keep the same index for messages before the deleted one
                updated_memories[memory_idx] = memory_data

        # Update the message_memories dictionary
        st.session_state.message_memories = updated_memories

        # Update the persistent memory
        from tools.memory_tools import update_memory_from_messages
        update_memory_from_messages()

        # Save the updated conversation
        from utils.conversation import auto_save_conversation
        from llm.client import get_openai_client
        client = get_openai_client(st.session_state.api_key, st.session_state.base_url)
        filename, _ = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
        st.session_state.current_conversation_filename = filename

        # Show a success message
        st.toast("Message deleted", icon="✅")

        # Rerun to update the UI
        st.rerun()

def display_messages():
    """Display chat messages with extremely simplified UI to avoid conflicts."""
    for idx, message in enumerate(st.session_state.messages):
        # Use the most basic display method possible
        if message["role"] == "user":
            # For user messages, display content with delete button
            col1, col2 = st.columns([9, 1])
            with col1:
                st.markdown(f"**User:** {message['content']}")
            with col2:
                if st.button("🗑️", key=f"delete_message_{idx}", help="Delete this message"):
                    delete_message(idx)
        else:  # assistant messages
            # For assistant messages, display content with memory toggle and delete button
            st.markdown(f"{message['content']}")

            # Add memory toggle and delete button in columns
            col1, col2 = st.columns([9, 1])

            with col1:
                # Check if this message is already in memory tracking
                is_remembered = True  # Default to True (include in memory)
                if idx in st.session_state.message_memories:
                    is_remembered = st.session_state.message_memories[idx]["remember"]
                else:
                    # Initialize memory for this message
                    from tools.memory_tools import update_message_memory
                    update_message_memory(idx, True)

                # Create a toggle for memory inclusion
                new_state = st.toggle(
                    "🧠",
                    value=is_remembered,
                    key=f"memory_toggle_{idx}",
                    help="Toggle to include/exclude this message from memory"
                )

                # Update memory if toggle state changed
                if new_state != is_remembered:
                    from tools.memory_tools import update_message_memory
                    update_message_memory(idx, new_state)
                    st.rerun()

            with col2:
                # Add delete button
                if st.button("🗑️", key=f"delete_message_{idx}", help="Delete this message"):
                    delete_message(idx)

        # Add a separator between messages
        st.markdown("---")

def display_plan_progress():
    """Display plan progress during execution."""
    # Only display plan and log containers during execution, not in the final output
    if st.session_state.current_step_index >= 0 and st.session_state.current_step_index < len(st.session_state.plan):
        # Show plan overview with progress
        total_steps = len(st.session_state.plan)
        current_step_num = st.session_state.current_step_index + 1
        progress_percentage = current_step_num / total_steps

        # Create a clean progress display with progress bar
        with st.session_state.plan_container.container():
            st.progress(progress_percentage)

            # Determine plan complexity for display
            complexity_level = "Simple"
            complexity_color = "green"
            if total_steps > 7:
                complexity_level = "Moderate"
                complexity_color = "orange"
            if total_steps > 12:
                complexity_level = "Complex"
                complexity_color = "red"

            # Show progress with complexity indicator
            st.caption(f"Processing: {int(progress_percentage * 100)}% complete ({current_step_num}/{total_steps} steps) - :{complexity_color}[{complexity_level} Plan]")

            # Add a detailed plan view in an expander
            with st.expander("View detailed plan", expanded=False):
                for i, step in enumerate(st.session_state.plan):
                    status_icon = "⏳" if i == st.session_state.current_step_index else "✅" if i < st.session_state.current_step_index else "⏸️"
                    deps = ", ".join([str(d) for d in step["dependencies"]]) if step["dependencies"] else "None"
                    st.markdown(f"{status_icon} **Step {step['step_id']}**: {step['description']}\n   Tool: `{step['tool_suggestion']}` | Dependencies: `{deps}`")

        # Only show detailed execution log if debug mode is enabled
        if st.session_state.debug_mode:
            st.session_state.log_container.markdown("\n\n".join(st.session_state.execution_log), unsafe_allow_html=True)

def display_execution_results():
    """Display execution results in collapsible sections."""
    plan_display = []
    if st.session_state.plan is not None and st.session_state.plan:
        for step in st.session_state.plan:
            status_icon = "⚪" # Pending
            if step["status"] == "Completed":
                status_icon = "✅"
            elif step["status"] == "Failed":
                status_icon = "❌"
            elif step["step_id"] == st.session_state.current_step_index + 1: # Next step to run
                 status_icon = "⏳"

            # Hide dependency details from the user interface
            plan_display.append(f"{status_icon} **Step {step['step_id']}:** {step['description']}<br>")
            if step["status"] in ["Completed", "Failed"] and step["result"]:
                 # Show result in collapsed section with the step description as the title
                 with st.expander(f"   {step['description']}", expanded=False):
                      # Get the reasoning and action for this step
                      # Default values in case we can't find the specific reasoning/action
                      reasoning = step.get("reasoning", "No reasoning available")
                      action_str = step.get("action_str", "No action details available")
                      observation = str(step['result'])

                      # Display the reason, act, observe sections
                      st.markdown(f"🧠 **Reason:**")
                      st.markdown(reasoning)

                      st.markdown(f"🎬 **Act:**")
                      st.markdown(action_str)

                      st.markdown(f"👀 **Observe:**")
                      # Process the result to hide raw JSON
                      result_str = observation
                      # If result looks like JSON, try to format it more user-friendly
                      if (result_str.startswith('{') and result_str.endswith('}')) or \
                         (result_str.startswith('[') and result_str.endswith(']')):
                          try:
                              # Try to parse as JSON
                              result_obj = json.loads(result_str)
                              # If it's a simple error message in JSON, just show the message
                              if isinstance(result_obj, dict) and 'error' in result_obj:
                                  st.error(result_obj['error'])
                              else:
                                  # Otherwise show a cleaner version
                                  st.json(result_obj)
                          except json.JSONDecodeError:
                              # If not valid JSON, show as code
                              st.code(result_str, language=None)
                      else:
                          st.code(result_str, language=None)

def handle_url_scrape_request(prompt, client):
    """Handle direct URL scraping requests."""
    is_scrape_request, url, memory_key, add_to_kb = detect_url_scrape_request(prompt)

    if is_scrape_request and url:
        # This is a direct URL scraping request, handle it without planning
        with st.spinner("🌐 Scraping website content..."):
            with st.chat_message("assistant"):
                # Clear any previous status
                if 'status_container' in st.session_state:
                    st.session_state.status_container.empty()
                    # Show scraping status
                    st.session_state.status_container.info(f"🌐 Scraping content from {url}...")

                try:
                    scraper = WebScraper()
                    content = scraper.scrape_content(url)

                    # Determine if we should add to knowledge base
                    kb_entry = None
                    if add_to_kb:
                        # Extract a title from the URL
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        title = f"Web content from {domain}"

                        # Add to knowledge base
                        from tools.knowledge_tools import knowledge_manager
                        kb_entry = knowledge_manager.add_web_source(url, content, title)
                        if "error" in kb_entry:
                            st.warning(f"Failed to add to knowledge base: {kb_entry['error']}")
                            kb_entry = None

                    # Store the scraped content in memory
                    if kb_entry and "memory_key" in kb_entry:
                        # Use the knowledge base memory key
                        memory_key = kb_entry["memory_key"]

                    st.session_state.context[memory_key] = content
                    st.session_state.persistent_memory[memory_key] = content

                    # Create a response message
                    if kb_entry:
                        response = f"I've scraped the content from {url} and added it to the knowledge base. This information will be available across all conversations.\n\nKnowledge Base Entry ID: {kb_entry['id']}\nMemory Key: {memory_key}\n\nThe content includes information about: {content[:200]}...\n\nReference: {url}"
                    else:
                        response = f"I've scraped the content from {url} and stored it in memory. I'll use this information to answer your future questions in this conversation.\n\nThe content includes information about: {content[:200]}...\n\nReference: {url}"

                    # Add to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    new_message_idx = len(st.session_state.messages) - 1

                    # Display message content using basic components
                    st.markdown(f"{response}")

                    # Add memory toggle and delete button in columns
                    col1, col2 = st.columns([9, 1])

                    with col1:
                        # Add memory toggle
                        is_remembered = True  # Default to True (include in memory)
                        new_state = st.toggle(
                            "🧠",
                            value=is_remembered,
                            key=f"memory_toggle_{new_message_idx}",
                            help="Toggle to include/exclude this message from memory"
                        )

                        # Update memory if toggle state changed
                        if not new_state:
                            # Update to exclude from memory
                            from tools.memory_tools import update_message_memory
                            update_message_memory(new_message_idx, False)

                    with col2:
                        # Add delete button
                        if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
                            delete_message(new_message_idx)

                    # Add a separator
                    st.markdown("---")

                    # Update message memory
                    from tools.memory_tools import update_message_memory
                    update_message_memory(new_message_idx, True)

                    # Update status
                    if kb_entry:
                        st.session_state.status_container.success(f"✅ Successfully added {url} to knowledge base")
                    else:
                        st.session_state.status_container.success(f"✅ Successfully scraped content from {url}")

                    # Automatically save the conversation
                    filename, _ = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
                    st.session_state.current_conversation_filename = filename
                except Exception as e:
                    error_msg = f"I encountered an error while trying to scrape {url}: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    new_message_idx = len(st.session_state.messages) - 1

                    # Display error message using basic components
                    st.error(f"{error_msg}")

                    # Add memory toggle and delete button in columns
                    col1, col2 = st.columns([9, 1])

                    with col1:
                        # Add memory toggle
                        is_remembered = True  # Default to True (include in memory)
                        new_state = st.toggle(
                            "🧠",
                            value=is_remembered,
                            key=f"memory_toggle_{new_message_idx}",
                            help="Toggle to include/exclude this message from memory"
                        )

                        # Update memory if toggle state changed
                        if not new_state:
                            # Update to exclude from memory
                            from tools.memory_tools import update_message_memory
                            update_message_memory(new_message_idx, False)

                    with col2:
                        # Add delete button
                        if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
                            delete_message(new_message_idx)

                    # Add a separator
                    st.markdown("---")

                    # Update message memory
                    from tools.memory_tools import update_message_memory
                    update_message_memory(new_message_idx, True)
        return True
    return False

def handle_regular_query(prompt, client):
    """Handle regular queries with planning and execution."""
    with st.spinner("🤖 Planning..."):
        with st.chat_message("assistant"):
            # Clear any previous status and show planning status
            if 'status_container' in st.session_state:
                st.session_state.status_container.empty()
                st.session_state.status_container.info("🧠 Creating execution plan...")
            # Assess query complexity first
            query_complexity = assess_query_complexity(prompt)
            if query_complexity == "High" and 'status_container' in st.session_state:
                st.session_state.status_container.info("🧠 Complex query detected. Creating detailed plan...")

            # Check if SCF is available and should be used
            use_scf = False
            try:
                from scf.manager_instance import scf_manager
                if scf_manager and query_complexity in ["Medium", "High"]:
                    use_scf = True
                    # Route the query to the appropriate component
                    component_name = scf_manager.route_query(prompt)
                    if 'status_container' in st.session_state:
                        st.session_state.status_container.info(f"🧠 Using {component_name} component for this query")
                    # Get component-specific system prompt and capabilities
                    system_prompt = scf_manager.get_component_prompt(component_name)
                    capabilities = scf_manager.get_component_capabilities(component_name)
                    # Generate plan with component-specific context
                    st.session_state.plan = run_planner(client, prompt, st.session_state.planner_model,
                                                       system_prompt, capabilities) or []
                    # Store component info in context for use during execution
                    st.session_state.context['current_component'] = component_name
                    st.session_state.context['component_capabilities'] = capabilities
            except (ImportError, AttributeError):
                use_scf = False

            # If SCF is not available or not used, fall back to standard planning
            if not use_scf:
                st.session_state.plan = run_planner(client, prompt, st.session_state.planner_model) or []

            if st.session_state.plan:
                # Update status with plan information and complexity
                steps_count = len(st.session_state.plan)
                complexity_emoji = "🟢" if steps_count < 8 else "🟡" if steps_count < 13 else "🔴"
                if 'status_container' in st.session_state:
                    st.session_state.status_container.success(f"✅ Plan created with {steps_count} steps {complexity_emoji}")
                # Start execution
                st.session_state.current_step_index = 0
                st.rerun() # Trigger the execution loop
            else:
                st.error("Failed to generate a plan. Please check the console for errors.")
                st.session_state.messages.append({"role": "assistant", "content": "Apologies, I encountered an issue while creating the execution plan. Please try again or check your API keys."})

def handle_execution_step(client):
    """Handle execution of a single step in the plan."""
    current_step = st.session_state.plan[st.session_state.current_step_index]

    # Add a button to skip the current step if needed
    _, col2 = st.columns([5, 1])
    with col2:
        if st.button("Skip this step", key=f"skip_step_{current_step['step_id']}"):
            # Mark the current step as skipped
            current_step["status"] = "Skipped"
            current_step["result"] = "Manually skipped by user"
            st.success(f"Step {current_step['step_id']} marked as skipped. Moving to next step...")
            # Move to the next step
            st.session_state.current_step_index += 1
            st.rerun()

    if current_step["status"] == "Pending":
        # Check dependencies (simple check: previous step must be completed)
        dependencies_met = True
        if current_step["dependencies"]:
            for dep_id in current_step["dependencies"]:
                # Find the dependent step
                dep_step = next((s for s in st.session_state.plan if s["step_id"] == dep_id), None)
                # Consider both Completed and Skipped steps as valid dependencies
                if not dep_step or (dep_step["status"] != "Completed" and dep_step["status"] != "Skipped"):
                    dependencies_met = False
                    # This state shouldn't normally be reached with sequential execution,
                    # but good for robustness if dependencies were complex.
                    status_msg = f"Step {current_step['step_id']} waiting for dependency {dep_id} which is {dep_step['status'] if dep_step else 'Not Found'}"
                    st.warning(status_msg)

                    # Check if we need to offer a way to skip this dependency
                    if dep_step and dep_step["status"] not in ["Completed", "Skipped", "Pending"]:
                        # Dependency is in a problematic state (e.g., Failed)
                        if st.button(f"Skip dependency {dep_id} and continue", key=f"skip_dep_{dep_id}_{current_step['step_id']}"):
                            # Mark the dependency as skipped
                            dep_step["status"] = "Skipped"
                            dep_step["result"] = "Manually skipped to unblock dependent steps"
                            st.success(f"Dependency {dep_id} marked as skipped. Continuing execution...")
                            st.rerun()
                    elif dep_step and dep_step["status"] == "Pending":
                        # Dependency is still pending, check if it's been waiting too long
                        # Track when we started waiting for this dependency
                        wait_key = f"waiting_since_{current_step['step_id']}_{dep_id}"
                        if wait_key not in st.session_state:
                            import time
                            st.session_state[wait_key] = time.time()

                        # Check if we've been waiting too long (30 seconds)
                        import time
                        waiting_time = time.time() - st.session_state[wait_key]
                        if waiting_time > 30:  # 30 seconds threshold
                            st.error(f"Dependency {dep_id} has been pending for {int(waiting_time)} seconds")
                            if st.button(f"Skip stuck dependency {dep_id}", key=f"skip_stuck_dep_{dep_id}_{current_step['step_id']}"):
                                # Mark the dependency as skipped
                                dep_step["status"] = "Skipped"
                                dep_step["result"] = "Automatically skipped after waiting too long"
                                st.success(f"Dependency {dep_id} marked as skipped. Continuing execution...")
                                # Clear the waiting timestamp
                                if wait_key in st.session_state:
                                    del st.session_state[wait_key]
                                st.rerun()
                    break # Stop execution for this cycle

        if dependencies_met:
            # Update the status container with the current step information
            if 'status_container' in st.session_state:
                st.session_state.status_container.info(f"⏳ Step {current_step['step_id']}/{len(st.session_state.plan)}: {current_step['description']}")
            with st.spinner(f"Running Step {current_step['step_id']}/{len(st.session_state.plan)}..."):
                reasoning, action_str, observation = run_executor_step(
                    client, current_step, st.session_state.context, st.session_state.executor_model
                )

                # Update Execution Log display and store for the current step
                step_log = [
                    f"**Step {current_step['step_id']}**: {current_step['description']}",
                    f"🧠 **Reason:** {reasoning}",
                    f"🎬 **Act:** {action_str}",
                    f"👀 **Observe:**\n```\n{observation}\n```"
                ]
                st.session_state.execution_log = step_log

                # Store the reasoning and action in the step for later display
                current_step["reasoning"] = reasoning
                current_step["action_str"] = action_str

                # Debug output to verify reasoning is being updated
                log_debug(f"Reasoning for step {current_step['step_id']}: {reasoning}")

                # Update Plan State
                current_step["result"] = observation

                # Check for errors in the observation or reasoning
                has_error = "Error" in observation[:20] or "Error" in reasoning[:20] or "failed" in observation.lower()

                if has_error:
                    # Mark the step as failed initially
                    current_step["status"] = "Failed"

                    # Special handling: if this step was web_search, extract URLs from markdown result
                    if current_step.get("tool_suggestion") == "web_search" and isinstance(observation, str):
                        urls = extract_urls_from_markdown(observation)
                        st.session_state.context["search_result_urls"] = urls

                    # Try to adjust the plan to recover from the failure
                    try:
                        adjusted_plan, should_continue, next_step_index, status_message = adjust_plan(
                            client, st.session_state.plan, st.session_state.current_step_index,
                            st.session_state.context, observation, st.session_state.executor_model
                        )

                        # Update the plan with the adjusted version
                        st.session_state.plan = adjusted_plan

                        if status_message:
                            if 'status_container' in st.session_state:
                                st.session_state.status_container.warning(status_message)

                        if should_continue:
                            # Continue execution with the adjusted plan
                            st.session_state.current_step_index = next_step_index
                        else:
                            # Cannot recover, halt execution
                            st.session_state.messages.append({"role": "assistant", "content": f"Step {current_step['step_id']} failed and could not be recovered. Stopping execution."})
                            st.session_state.current_step_index = -2  # Indicate failure halt
                    except Exception as e:
                        # If plan adjustment fails, fall back to the original behavior
                        st.error(f"Plan adjustment failed: {str(e)}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Step {current_step['step_id']} failed. Stopping execution."})
                        st.session_state.current_step_index = -2  # Indicate failure halt
                else:
                    # Step completed successfully
                    current_step["status"] = "Completed"
                    # Update context (simple way: store result by step_id)
                    st.session_state.context[f"step_{current_step['step_id']}_result"] = observation

                    # Check if we need to adjust the plan based on the observation
                    try:
                        adjusted_plan, should_continue, next_step_index, status_message = adjust_plan(
                            client, st.session_state.plan, st.session_state.current_step_index,
                            st.session_state.context, observation, st.session_state.executor_model
                        )

                        # Update the plan with the adjusted version
                        st.session_state.plan = adjusted_plan

                        if status_message:
                            if 'status_container' in st.session_state:
                                st.session_state.status_container.info(status_message)

                        # Move to the next step
                        st.session_state.current_step_index = next_step_index
                    except Exception as e:
                        # If plan adjustment fails, fall back to the original behavior
                        log_debug(f"Plan adjustment failed: {str(e)}")
                        st.session_state.current_step_index += 1

                st.rerun() # Rerun to process next step or completion

def handle_plan_completion(client):
    """Handle completion of the plan and generate final response."""
    # Update status to show completion
    if 'status_container' in st.session_state:
        st.session_state.status_container.success("✅ Plan Execution Completed!")

    # Generate final response to the user
    with st.spinner("Generating final response..."):
        # Find the last user message to use as the query
        user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
        if user_messages:
            user_query = user_messages[-1]["content"]
        else:
            user_query = "Unknown query"
        final_response = generate_final_response(client, user_query, st.session_state.plan)

        # Clear the status container after generating the response
        if 'status_container' in st.session_state:
            st.session_state.status_container.empty()

    # Process the final response to handle LaTeX and dollar amounts
    try:
        from processing.format_results import process_final_output
        processed_response = process_final_output(final_response)
    except ImportError:
        # If the module is not available, use the original response
        processed_response = final_response
        st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

    # Add the processed response to the chat
    st.session_state.messages.append({"role": "assistant", "content": processed_response})

    # Add this new message to memory (automatically remembered by default)
    new_message_idx = len(st.session_state.messages) - 1
    from tools.memory_tools import update_message_memory
    update_message_memory(new_message_idx, True)

    # Display the processed response immediately using basic components
    st.markdown(f"{processed_response}")

    # Add memory toggle and delete button in columns
    col1, col2 = st.columns([9, 1])

    with col1:
        # Add memory toggle
        is_remembered = True  # Default to True (include in memory)
        new_state = st.toggle(
            "🧠",
            value=is_remembered,
            key=f"memory_toggle_{new_message_idx}",
            help="Toggle to include/exclude this message from memory"
        )

        # Update memory if toggle state changed
        if not new_state:
            # Update to exclude from memory
            from tools.memory_tools import update_message_memory
            update_message_memory(new_message_idx, False)

    with col2:
        # Add delete button
        if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
            delete_message(new_message_idx)

    # Add a separator
    st.markdown("---")

    # Automatically save the conversation
    filename, _ = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
    st.session_state.current_conversation_filename = filename

    # Reset for next query
    st.session_state.current_step_index = -1
    # Keep plan visible, but could clear: st.session_state.plan = None

    # Transfer important information from context to persistent memory
    if st.session_state.context:
        # Copy any important results to persistent memory
        for key, value in st.session_state.context.items():
            if not key.startswith('step_'):
                # Only preserve named memory items, not step results
                st.session_state.persistent_memory[key] = value

    # Force a rerun to ensure the UI is updated
    st.rerun()

def handle_plan_failure():
    """Handle failure of the plan and generate failure response."""
    # Update status to show failure
    if 'status_container' in st.session_state:
        st.session_state.status_container.error("❌ Plan Execution Halted due to step failure.")

    # Generate a failure response
    failed_step = next((step for step in st.session_state.plan if step["status"] == "Failed"), None)

    # Clear the status container after a short delay
    time.sleep(2)  # Keep the error message visible for 2 seconds
    if 'status_container' in st.session_state:
        st.session_state.status_container.empty()

    if failed_step:
        failure_message = f"I encountered an issue while trying to answer your query. The step '{failed_step['description']}' failed with the following error: {failed_step['result']}"

        # Add any successful steps' results
        successful_steps = [step for step in st.session_state.plan if step["status"] == "Completed"]

        # Extract references from successful steps
        references = []

        if successful_steps:
            failure_message += "\n\nHowever, I was able to complete the following steps:\n"

            for step in successful_steps:
                failure_message += f"\n- {step['description']}: {step['result']}"

                # Check if this step involves web scraping
                if step["tool_suggestion"] == "web_scrape" and "url" in step["description"].lower():
                    # Try to extract URL from the step description or result
                    url_match = re.search(r'https?://[^\s"\')]+', step["description"] + " " + str(step["result"]))
                    if url_match:
                        references.append(f"Web source: {url_match.group(0)}")

                # Check if this step involves web search
                elif step["tool_suggestion"] == "web_search":
                    # Web search results often contain URLs in the result
                    urls = re.findall(r'https?://[^\s"\')]+', str(step["result"]))
                    for url in urls:
                        references.append(f"Search result: {url}")

                # Check if this step involves reading files
                elif step["tool_suggestion"] == "read_file" and "filename" in str(step["description"]).lower():
                    # Try to extract filename from the step description or result
                    file_match = re.search(r'[\w\.-]+\.(txt|csv|json|md|py|html|xml|pdf)', step["description"] + " " + str(step["result"]))
                    if file_match:
                        references.append(f"File source: {file_match.group(0)}")

        # Remove duplicate references
        references = list(set(references))

        # Add references to the failure message if any were found
        if references:
            failure_message += "\n\nSources used:\n"
            for ref in references:
                failure_message += f"\n- {ref}"

        # Process the failure message to handle LaTeX and dollar amounts
        try:
            from processing.format_results import process_final_output
            processed_failure = process_final_output(failure_message)
        except ImportError:
            # If the module is not available, use the original message
            processed_failure = failure_message
            st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

        st.session_state.messages.append({"role": "assistant", "content": processed_failure})

        # Add this new message to memory (automatically remembered by default)
        new_message_idx = len(st.session_state.messages) - 1
        from tools.memory_tools import update_message_memory
        update_message_memory(new_message_idx, True)

        # Display the processed failure message immediately
        with st.chat_message("assistant"):
            # Display message content
            st.markdown(processed_failure)

            # Simplified controls to avoid potential UI conflicts
            col1, col2 = st.columns([9, 1])

            with col1:
                # Add memory toggle
                st.toggle(
                    "🧠",
                    value=True,
                    key=f"memory_toggle_{new_message_idx}",
                    help="Toggle to include/exclude this message from memory"
                )

            with col2:
                # Add delete button
                if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
                    delete_message(new_message_idx)

        # Automatically save the conversation
        from llm.client import get_openai_client
        client = get_openai_client(st.session_state.api_key, st.session_state.base_url)
        filename, _ = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
        st.session_state.current_conversation_filename = filename
    else:
        failure_message = "I encountered an issue while trying to answer your query. The execution plan failed, but I couldn't identify which specific step caused the problem."

        # Process the failure message to handle LaTeX and dollar amounts
        try:
            from processing.format_results import process_final_output
            processed_failure = process_final_output(failure_message)
        except ImportError:
            # If the module is not available, use the original message
            processed_failure = failure_message
            st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

        st.session_state.messages.append({"role": "assistant", "content": processed_failure})

        # Add this new message to memory (automatically remembered by default)
        new_message_idx = len(st.session_state.messages) - 1
        from tools.memory_tools import update_message_memory
        update_message_memory(new_message_idx, True)

        # Display the processed failure message immediately using basic components
        st.markdown(f"{processed_failure}")

        # Add memory toggle and delete button in columns
        col1, col2 = st.columns([9, 1])

        with col1:
            # Add memory toggle
            is_remembered = True  # Default to True (include in memory)
            new_state = st.toggle(
                "🧠",
                value=is_remembered,
                key=f"memory_toggle_{new_message_idx}",
                help="Toggle to include/exclude this message from memory"
            )

            # Update memory if toggle state changed
            if not new_state:
                # Update to exclude from memory
                from tools.memory_tools import update_message_memory
                update_message_memory(new_message_idx, False)

        with col2:
            # Add delete button
            if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
                delete_message(new_message_idx)

        # Add a separator
        st.markdown("---")

        # Automatically save the conversation
        from llm.client import get_openai_client
        client = get_openai_client(st.session_state.api_key, st.session_state.base_url)
        filename, _ = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
        st.session_state.current_conversation_filename = filename

    # Keep state as is for debugging, reset index to prevent re-execution attempt
    st.session_state.current_step_index = -1

    # Force a rerun to ensure the UI is updated
    st.rerun()

def process_user_input(prompt, client):
    """Process user input and handle different types of requests."""
    if not client:
        st.error("Please configure the OpenRouter API Key in the sidebar.")
        return

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message using basic components
    new_message_idx = len(st.session_state.messages) - 1
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"**User:** {prompt}")
    with col2:
        if st.button("🗑️", key=f"delete_message_{new_message_idx}", help="Delete this message"):
            delete_message(new_message_idx)

    # Add a separator
    st.markdown("---")

    # Create status container right below user message
    # Initialize status_container if it doesn't exist yet
    if 'status_container' not in st.session_state:
        st.session_state.status_container = st.empty()
    else:
        st.session_state.status_container.empty()
        # Recreate the container to ensure it's positioned below the current user message
        st.session_state.status_container = st.empty()

    # Deep research mode toggle is now displayed in the main UI, so we don't need to show status here

    # Clear previous execution state
    st.session_state.plan = None
    st.session_state.current_step_index = -1

    # Transfer important information from context to persistent memory before clearing
    if st.session_state.context:
        # Copy any important results to persistent memory
        for key, value in st.session_state.context.items():
            if not key.startswith('step_'):
                # Only preserve named memory items, not step results
                st.session_state.persistent_memory[key] = value

    # Initialize context with persistent memory
    st.session_state.context = st.session_state.persistent_memory.copy()

    st.session_state.execution_log = []

    # Make sure the containers are initialized and cleared
    if 'plan_container' in st.session_state:
        st.session_state.plan_container.empty() # Clear display immediately
    if 'log_container' in st.session_state:
        st.session_state.log_container.empty()
    if 'status_container' in st.session_state:
        st.session_state.status_container.empty()

    # Check if this is a URL scraping request
    if not handle_url_scrape_request(prompt, client):
        # Regular query - generate plan and execute
        handle_regular_query(prompt, client)
