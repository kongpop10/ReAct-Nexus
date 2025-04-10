"""
Knowledge Base sidebar component for the ReAct application.
Displays and manages knowledge sources in the knowledge base.
"""
import streamlit as st
from storage.knowledge_manager import KnowledgeManager

def render_knowledge_base_sidebar(knowledge_manager: KnowledgeManager):
    """Render the knowledge base sidebar with management functionality."""
    st.sidebar.subheader("📖 Knowledge Base")

    # Display current knowledge base entries
    entries = knowledge_manager.get_all_entries()

    if not entries:
        st.sidebar.info("No knowledge sources available yet.")
    else:
        # Group entries by type
        web_entries = [e for e in entries if e["type"] == "web"]
        local_entries = [e for e in entries if e["type"] == "local"]

        # Display web sources
        if web_entries:
            st.sidebar.markdown("### 🌐 Web Sources")
            for entry in web_entries:
                status_icon = "🟢" if entry["status"] == "active" else "⚪"
                with st.sidebar.container():
                    cols = st.sidebar.columns([4, 1])
                    cols[0].markdown(f"{status_icon} **{entry['title']}**")
                    if cols[1].button("🚫", key=f"delete_kb_{entry['id']}", help="Delete this knowledge source"):
                        knowledge_manager.delete_entry(entry["id"])
                        # Remove from memory if present
                        if entry["memory_key"] in st.session_state.context:
                            del st.session_state.context[entry["memory_key"]]
                        if entry["memory_key"] in st.session_state.persistent_memory:
                            del st.session_state.persistent_memory[entry["memory_key"]]
                        st.sidebar.success(f"Deleted knowledge source: {entry['title']}")
                        st.rerun()
                    st.sidebar.caption(f"Source: {entry['source']}")
                    st.sidebar.caption(f"Memory Key: {entry['memory_key']}")

        # Display local sources
        if local_entries:
            st.sidebar.markdown("### 📄 Local Files")
            for entry in local_entries:
                status_icon = "🟢" if entry["status"] == "active" else "⚪"
                with st.sidebar.container():
                    cols = st.sidebar.columns([4, 1])
                    cols[0].markdown(f"{status_icon} **{entry['title']}**")
                    if cols[1].button("🚫", key=f"delete_kb_{entry['id']}", help="Delete this knowledge source"):
                        knowledge_manager.delete_entry(entry["id"])
                        # Remove from memory if present
                        if entry["memory_key"] in st.session_state.context:
                            del st.session_state.context[entry["memory_key"]]
                        if entry["memory_key"] in st.session_state.persistent_memory:
                            del st.session_state.persistent_memory[entry["memory_key"]]
                        st.sidebar.success(f"Deleted knowledge source: {entry['title']}")
                        st.rerun()
                    st.sidebar.caption(f"Source: {entry['source']}")
                    st.sidebar.caption(f"Memory Key: {entry['memory_key']}")

    # Add new knowledge source section
    with st.sidebar.expander("➕ Add Knowledge Source", expanded=False):
        # Add web source
        with st.form(key="add_web_source_form"):
            st.subheader("Add Web Source")
            web_url = st.text_input("URL", key="kb_web_url")
            web_title = st.text_input("Title (optional)", key="kb_web_title")
            web_submit = st.form_submit_button("Add Web Source")

        if web_submit and web_url:
            with st.spinner("Scraping and adding to knowledge base..."):
                try:
                    # Scrape the content
                    from data_acquisition.news_scraper import WebScraper
                    scraper = WebScraper()
                    content = scraper.scrape_content(web_url)

                    # Add to knowledge base
                    entry = knowledge_manager.add_web_source(web_url, content, web_title if web_title else None)

                    if "error" in entry:
                        st.error(f"Failed to add to knowledge base: {entry['error']}")
                    else:
                        # Add to session memory
                        st.session_state.context[entry["memory_key"]] = content
                        st.session_state.persistent_memory[entry["memory_key"]] = content
                        st.success(f"Added web source to knowledge base: {entry['title']}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error adding web source: {str(e)}")

        # Add local file
        with st.form(key="add_local_file_form"):
            st.subheader("Add Local File")
            uploaded_file = st.file_uploader("Upload Markdown File (.md)", type=["md"], key="kb_file_upload")
            file_title = st.text_input("Title (optional)", key="kb_file_title")
            file_submit = st.form_submit_button("Add File")

        if file_submit and uploaded_file:
            with st.spinner("Adding file to knowledge base..."):
                try:
                    # Add to knowledge base using the uploaded file
                    entry = knowledge_manager.add_uploaded_file(uploaded_file, file_title if file_title else None)

                    if "error" in entry:
                        st.error(f"Failed to add to knowledge base: {entry['error']}")
                    else:
                        # Get content and add to session memory
                        content = knowledge_manager.get_entry_content(entry["id"])
                        st.session_state.context[entry["memory_key"]] = content
                        st.session_state.persistent_memory[entry["memory_key"]] = content
                        st.success(f"Added local file to knowledge base: {entry['title']}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error adding local file: {str(e)}")
