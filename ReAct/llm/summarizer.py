"""
Response generation functions for the ReAct application.
"""
import re
import streamlit as st

def generate_final_response(client, user_query, plan):
    """Generates a final response to the user's query based on execution results."""
    if not client:
        return "I couldn't generate a proper response due to API configuration issues."

    # Prepare context for the final response
    results_summary = []

    # Extract references from web scraping and file reading steps
    references = []

    for step in plan:
        if step["result"] and step["status"] == "Completed":
            results_summary.append(f"Step {step['step_id']} ({step['description']}): {step['result']}")

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

    results_text = "\n\n".join(results_summary)
    references_text = "\n".join(references) if references else "No external sources were used."

    system_prompt = f"""You are a helpful assistant tasked with providing a thorough and insightful final response to the user's query.
The user asked: "{user_query}"

A plan was executed with the following results:
{results_text}

The following sources were used to gather information:
{references_text}

Based on these execution results, provide a comprehensive, thorough, and insightful response that directly answers the user's original query.
Focus on synthesizing the information, providing deep analysis, and presenting it in a user-friendly way.
If the execution results don't fully answer the query, acknowledge this and provide the best response possible with the available information.

Your summary should be detailed and demonstrate critical thinking about the information gathered.
Make connections between different pieces of information and highlight important insights.

IMPORTANT: If any web pages or files were used as sources, you MUST include references to these sources in your response.
Format the references section at the end of your response like this:

Sources:
- [Source description or title] (URL or filename)
"""

    try:
        completion = client.chat.completions.create(
            model=st.session_state.summarizer_model,  # Using the summarizer model for the final response
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please provide a final response to my query: {user_query}"}
            ],
            temperature=0.3
        )

        final_response = completion.choices[0].message.content
        return final_response
    except Exception as e:
        st.error(f"Error generating final response: {e}")
        return f"I've completed the steps to answer your query, but encountered an error when generating the final response. Here's a summary of what I found:\n\n{results_text}"
