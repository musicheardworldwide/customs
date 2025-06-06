# filename: generate_complex_scenarios_v2.py

import os
import re
import json
import requests
import time
from typing import List, Dict, Any

# --- CONFIGURATION ---
# IMPORTANT: CONFIGURE YOUR LLM API ENDPOINT AND KEY
# This can be your Open WebUI endpoint or another service like OpenAI, Anthropic, etc.
LLM_API_URL = "http://localhost:3000/api/chat/completions"  # IMPORTANT: Your OpenAI-compatible endpoint
LLM_API_KEY = "sk-527fc6908bde498a83cb7ce9d1529303"                              # IMPORTANT: Your API Key
LLM_MODEL_ID = "deepseek-chat"                             # Model you want to use for generation
OUTPUT_FILE = 'complex_scenarios_dataset.jsonl'
REQUEST_DELAY_SECONDS = 2 # To avoid rate limiting

# ==============================================================================
# PASTE YOUR FULL LIST OF 205 TOOLS HERE
# ==============================================================================
MASTER_TOOL_LIST = [
    # Knowledge Graph Tools
    {"category": "Knowledge Graph", "name": "Create Entities", "api_name": "knowledge_graph/create_entities"},
    {"category": "Knowledge Graph", "name": "Create Relations", "api_name": "knowledge_graph/create_relations"},
    {"category": "Knowledge Graph", "name": "Add Observations", "api_name": "knowledge_graph/add_observations"},
    {"category": "Knowledge Graph", "name": "Delete Entities", "api_name": "knowledge_graph/delete_entities"},
    {"category": "Knowledge Graph", "name": "Delete Observations", "api_name": "knowledge_graph/delete_observations"},
    {"category": "Knowledge Graph", "name": "Delete Relations", "api_name": "knowledge_graph/delete_relations"},
    {"category": "Knowledge Graph", "name": "Read Graph", "api_name": "knowledge_graph/read_graph"},
    {"category": "Knowledge Graph", "name": "Search Nodes", "api_name": "knowledge_graph/search_nodes"},
    {"category": "Knowledge Graph", "name": "Open Nodes", "api_name": "knowledge_graph/open_nodes"},
    # Problem-Solving Tools
    {"category": "Problem-Solving", "name": "Sequential Thinking", "api_name": "problem_solving/sequential_thinking"},
    # Time Tools
    {"category": "Time", "name": "Get Current Time", "api_name": "time/get_current_time"},
    {"category": "Time", "name": "Convert Time", "api_name": "time/convert_time"},
    # Todoist Tools
    {"category": "Todoist", "name": "Create Task", "api_name": "todoist/create_task"},
    {"category": "Todoist", "name": "Get Tasks", "api_name": "todoist/get_tasks"},
    {"category": "Todoist", "name": "Update Task", "api_name": "todoist/update_task"},
    {"category": "Todoist", "name": "Delete Task", "api_name": "todoist/delete_task"},
    {"category": "Todoist", "name": "Complete Task", "api_name": "todoist/complete_task"},
    # Shell Tools
    {"category": "Shell", "name": "Execute Shell Command", "api_name": "shell/execute_shell_command"},
    # File System Tools
    {"category": "File System", "name": "Read File", "api_name": "filesystem/read_file"},
    {"category": "File System", "name": "Read Multiple Files", "api_name": "filesystem/read_multiple_files"},
    {"category": "File System", "name": "Write File", "api_name": "filesystem/write_file"},
    {"category": "File System", "name": "Edit File", "api_name": "filesystem/edit_file"},
    {"category": "File System", "name": "Create Directory", "api_name": "filesystem/create_directory"},
    {"category": "File System", "name": "List Directory", "api_name": "filesystem/list_directory"},
    {"category": "File System", "name": "Directory Tree", "api_name": "filesystem/directory_tree"},
    {"category": "File System", "name": "Move File", "api_name": "filesystem/move_file"},
    {"category": "File System", "name": "Search Files", "api_name": "filesystem/search_files"},
    {"category": "File System", "name": "Get File Info", "api_name": "filesystem/get_file_info"},
    {"category": "File System", "name": "List Allowed Directories", "api_name": "filesystem/list_allowed_directories"},
    # Web Tools
    {"category": "Web", "name": "Fetch URL", "api_name": "web/fetch_url"},
    # Database Tools
    {"category": "Database", "name": "Read Query", "api_name": "database/read_query"},
    {"category": "Database", "name": "Write Query", "api_name": "database/write_query"},
    {"category": "Database", "name": "Create Table", "api_name": "database/create_table"},
    {"category": "Database", "name": "List Tables", "api_name": "database/list_tables"},
    {"category": "Database", "name": "Describe Table", "api_name": "database/describe_table"},
    # Slack Tools
    {"category": "Slack", "name": "List Channels", "api_name": "slack/list_channels"},
    {"category": "Slack", "name": "Post Message", "api_name": "slack/post_message"},
    {"category": "Slack", "name": "Reply to Thread", "api_name": "slack/reply_to_thread"},
    {"category": "Slack", "name": "Add Reaction", "api_name": "slack/add_reaction"},
    {"category": "Slack", "name": "Get Channel History", "api_name": "slack/get_channel_history"},
    {"category": "Slack", "name": "Get Thread Replies", "api_name": "slack/get_thread_replies"},
    {"category": "Slack", "name": "Get Users", "api_name": "slack/get_users"},
    {"category": "Slack", "name": "Get User Profile", "api_name": "slack/get_user_profile"},
    # Ollama Tools
    {"category": "Ollama", "name": "Serve", "api_name": "ollama/serve"},
    {"category": "Ollama", "name": "Create Model", "api_name": "ollama/create_model"},
    {"category": "Ollama", "name": "Show Model", "api_name": "ollama/show_model"},
    {"category": "Ollama", "name": "Run Model", "api_name": "ollama/run_model"},
    {"category": "Ollama", "name": "Pull Model", "api_name": "ollama/pull_model"},
    {"category": "Ollama", "name": "Push Model", "api_name": "ollama/push_model"},
    {"category": "Ollama", "name": "List Models", "api_name": "ollama/list_models"},
    {"category": "Ollama", "name": "Copy Model", "api_name": "ollama/copy_model"},
    {"category": "Ollama", "name": "Remove Model", "api_name": "ollama/remove_model"},
    {"category": "Ollama", "name": "Chat Completion", "api_name": "ollama/chat_completion"},
    # Planning Tools
    {"category": "Planning", "name": "Start Planning", "api_name": "planning/start_planning"},
    {"category": "Planning", "name": "Save Plan", "api_name": "planning/save_plan"},
    {"category": "Planning", "name": "Add Todo", "api_name": "planning/add_todo"},
    {"category": "Planning", "name": "Remove Todo", "api_name": "planning/remove_todo"},
    {"category": "Planning", "name": "Get Todos", "api_name": "planning/get_todos"},
    {"category": "Planning", "name": "Update Todo Status", "api_name": "planning/update_todo_status"},
    # Obsidian Tools
    {"category": "Obsidian", "name": "List Files in Directory", "api_name": "obsidian/list_files_in_directory"},
    {"category": "Obsidian", "name": "List Files in Vault", "api_name": "obsidian/list_files_in_vault"},
    {"category": "Obsidian", "name": "Get File Contents", "api_name": "obsidian/get_file_contents"},
    {"category": "Obsidian", "name": "Simple Search", "api_name": "obsidian/simple_search"},
    {"category": "Obsidian", "name": "Patch Content", "api_name": "obsidian/patch_content"},
    {"category": "Obsidian", "name": "Append Content", "api_name": "obsidian/append_content"},
    {"category": "Obsidian", "name": "Delete File", "api_name": "obsidian/delete_file"},
    {"category": "Obsidian", "name": "Complex Search", "api_name": "obsidian/complex_search"},
    {"category": "Obsidian", "name": "Batch Get File Contents", "api_name": "obsidian/batch_get_file_contents"},
    {"category": "Obsidian", "name": "Get Periodic Note", "api_name": "obsidian/get_periodic_note"},
    {"category": "Obsidian", "name": "Get Recent Periodic Notes", "api_name": "obsidian/get_recent_periodic_notes"},
    {"category": "Obsidian", "name": "Get Recent Changes", "api_name": "obsidian/get_recent_changes"},
    # Webflow Tools
    {"category": "Webflow", "name": "List Sites", "api_name": "webflow/list_sites"},
    {"category": "Webflow", "name": "Get Site", "api_name": "webflow/get_site"},
    {"category": "Webflow", "name": "Publish Site", "api_name": "webflow/publish_site"},
    {"category": "Webflow", "name": "List Pages", "api_name": "webflow/list_pages"},
    {"category": "Webflow", "name": "Get Page Metadata", "api_name": "webflow/get_page_metadata"},
    {"category": "Webflow", "name": "Update Page Settings", "api_name": "webflow/update_page_settings"},
    {"category": "Webflow", "name": "Get Page Content", "api_name": "webflow/get_page_content"},
    {"category": "Webflow", "name": "Update Static Content", "api_name": "webflow/update_static_content"},
    {"category": "Webflow", "name": "List Collections", "api_name": "webflow/list_collections"},
    {"category": "Webflow", "name": "Get Collection", "api_name": "webflow/get_collection"},
    {"category": "Webflow", "name": "Create Collection", "api_name": "webflow/create_collection"},
    {"category": "Webflow", "name": "Create Static Field", "api_name": "webflow/create_static_field"},
    {"category": "Webflow", "name": "Create Option Field", "api_name": "webflow/create_option_field"},
    {"category": "Webflow", "name": "Create Reference Field", "api_name": "webflow/create_reference_field"},
    {"category": "Webflow", "name": "Update Field", "api_name": "webflow/update_field"},
    {"category": "Webflow", "name": "Create Item", "api_name": "webflow/create_item"},
    {"category": "Webflow", "name": "Update Items", "api_name": "webflow/update_items"},
    {"category": "Webflow", "name": "List Items", "api_name": "webflow/list_items"},
    {"category": "Webflow", "name": "Publish Items", "api_name": "webflow/publish_items"},
    # Graphlit Tools
    {"category": "Graphlit", "name": "Configure Project", "api_name": "graphlit/configure_project"},
    {"category": "Graphlit", "name": "Query Project Usage", "api_name": "graphlit/query_project_usage"},
    {"category": "Graphlit", "name": "Ask Graphlit", "api_name": "graphlit/ask_graphlit"},
    {"category": "Graphlit", "name": "Prompt Conversation", "api_name": "graphlit/prompt_conversation"},
    {"category": "Graphlit", "name": "Retrieve Sources", "api_name": "graphlit/retrieve_sources"},
    {"category": "Graphlit", "name": "Retrieve Images", "api_name": "graphlit/retrieve_images"},
    {"category": "Graphlit", "name": "Extract Text", "api_name": "graphlit/extract_text"},
    {"category": "Graphlit", "name": "Create Collection", "api_name": "graphlit/create_collection"},
    {"category": "Graphlit", "name": "Add Contents to Collection", "api_name": "graphlit/add_contents_to_collection"},
    {"category": "Graphlit", "name": "Remove Contents from Collection", "api_name": "graphlit/remove_contents_from_collection"},
    {"category": "Graphlit", "name": "Delete Content", "api_name": "graphlit/delete_content"},
    {"category": "Graphlit", "name": "Delete Conversation", "api_name": "graphlit/delete_conversation"},
    {"category": "Graphlit", "name": "Delete Collection", "api_name": "graphlit/delete_collection"},
    {"category": "Graphlit", "name": "Delete Feed", "api_name": "graphlit/delete_feed"},
    {"category": "Graphlit", "name": "Delete Feeds", "api_name": "graphlit/delete_feeds"},
    {"category": "Graphlit", "name": "Delete Collections", "api_name": "graphlit/delete_collections"},
    {"category": "Graphlit", "name": "Delete Conversations", "api_name": "graphlit/delete_conversations"},
    {"category": "Graphlit", "name": "Delete Contents", "api_name": "graphlit/delete_contents"},
    {"category": "Graphlit", "name": "Query Contents", "api_name": "graphlit/query_contents"},
    {"category": "Graphlit", "name": "Query Collections", "api_name": "graphlit/query_collections"},
    {"category": "Graphlit", "name": "Query Feeds", "api_name": "graphlit/query_feeds"},
    {"category": "Graphlit", "name": "Query Conversations", "api_name": "graphlit/query_conversations"},
    {"category": "Graphlit", "name": "Is Content Done", "api_name": "graphlit/is_content_done"},
    {"category": "Graphlit", "name": "Is Feed Done", "api_name": "graphlit/is_feed_done"},
    # Integration Tools
    {"category": "Integration", "name": "List Notion Databases", "api_name": "integration/list_notion_databases"},
    {"category": "Integration", "name": "List Linear Projects", "api_name": "integration/list_linear_projects"},
    {"category": "Integration", "name": "List Slack Channels", "api_name": "integration/list_slack_channels"},
    {"category": "Integration", "name": "List SharePoint Libraries", "api_name": "integration/list_sharepoint_libraries"},
    {"category": "Integration", "name": "List SharePoint Folders", "api_name": "integration/list_sharepoint_folders"},
    {"category": "Integration", "name": "Ingest SharePoint Files", "api_name": "integration/ingest_sharepoint_files"},
    {"category": "Integration", "name": "Ingest OneDrive Files", "api_name": "integration/ingest_onedrive_files"},
    {"category": "Integration", "name": "Ingest Google Drive Files", "api_name": "integration/ingest_google_drive_files"},
    {"category": "Integration", "name": "Ingest Dropbox Files", "api_name": "integration/ingest_dropbox_files"},
    {"category": "Integration", "name": "Ingest Box Files", "api_name": "integration/ingest_box_files"},
    {"category": "Integration", "name": "Ingest GitHub Files", "api_name": "integration/ingest_github_files"},
    {"category": "Integration", "name": "Ingest Notion Pages", "api_name": "integration/ingest_notion_pages"},
    {"category": "Integration", "name": "Ingest Microsoft Teams Messages", "api_name": "integration/ingest_microsoft_teams_messages"},
    {"category": "Integration", "name": "Ingest Slack Messages", "api_name": "integration/ingest_slack_messages"},
    {"category": "Integration", "name": "Ingest Discord Messages", "api_name": "integration/ingest_discord_messages"},
    {"category": "Integration", "name": "Ingest Twitter Posts", "api_name": "integration/ingest_twitter_posts"},
    {"category": "Integration", "name": "Ingest Twitter Search", "api_name": "integration/ingest_twitter_search"},
    {"category": "Integration", "name": "Ingest Reddit Posts", "api_name": "integration/ingest_reddit_posts"},
    {"category": "Integration", "name": "Ingest Google Email", "api_name": "integration/ingest_google_email"},
    {"category": "Integration", "name": "Ingest Microsoft Email", "api_name": "integration/ingest_microsoft_email"},
    {"category": "Integration", "name": "Ingest Linear Issues", "api_name": "integration/ingest_linear_issues"},
    {"category": "Integration", "name": "Ingest GitHub Issues", "api_name": "integration/ingest_github_issues"},
    {"category": "Integration", "name": "Ingest Jira Issues", "api_name": "integration/ingest_jira_issues"},
    {"category": "Integration", "name": "Web Crawl", "api_name": "integration/web_crawl"},
    {"category": "Integration", "name": "Web Map", "api_name": "integration/web_map"},
    {"category": "Integration", "name": "Web Search", "api_name": "integration/web_search"},
    {"category": "Integration", "name": "Ingest RSS", "api_name": "integration/ingest_rss"},
    {"category": "Integration", "name": "Ingest URL", "api_name": "integration/ingest_url"},
    {"category": "Integration", "name": "Ingest Text", "api_name": "integration/ingest_text"},
    {"category": "Integration", "name": "Ingest Memory", "api_name": "integration/ingest_memory"},
    {"category": "Integration", "name": "Ingest File", "api_name": "integration/ingest_file"},
    {"category": "Integration", "name": "Screenshot Page", "api_name": "integration/screenshot_page"},
    {"category": "Integration", "name": "Describe Image URL", "api_name": "integration/describe_image_url"},
    {"category": "Integration", "name": "Describe Image Content", "api_name": "integration/describe_image_content"},
    {"category": "Integration", "name": "Publish Audio", "api_name": "integration/publish_audio"},
    {"category": "Integration", "name": "Publish Image", "api_name": "integration/publish_image"},
    {"category": "Integration", "name": "Send Webhook Notification", "api_name": "integration/send_webhook_notification"},
    {"category": "Integration", "name": "Send Slack Notification", "api_name": "integration/send_slack_notification"},
    {"category": "Integration", "name": "Send Twitter Notification", "api_name": "integration/send_twitter_notification"},
    {"category": "Integration", "name": "Send Email Notification", "api_name": "integration/send_email_notification"},
    # GitHub Tools
    {"category": "GitHub", "name": "Create/Update File", "api_name": "github/create_or_update_file"},
    {"category": "GitHub", "name": "Search Repositories", "api_name": "github/search_repositories"},
    {"category": "GitHub", "name": "Create Repository", "api_name": "github/create_repository"},
    {"category": "GitHub", "name": "Get File Contents", "api_name": "github/get_file_contents"},
    {"category": "GitHub", "name": "Push Files", "api_name": "github/push_files"},
    {"category": "GitHub", "name": "Create Issue", "api_name": "github/create_issue"},
    {"category": "GitHub", "name": "Create Pull Request", "api_name": "github/create_pull_request"},
    {"category": "GitHub", "name": "Fork Repository", "api_name": "github/fork_repository"},
    {"category": "GitHub", "name": "Create Branch", "api_name": "github/create_branch"},
    {"category": "GitHub", "name": "List Commits", "api_name": "github/list_commits"},
    {"category": "GitHub", "name": "List Issues", "api_name": "github/list_issues"},
    {"category": "GitHub", "name": "Update Issue", "api_name": "github/update_issue"},
    {"category": "GitHub", "name": "Add Issue Comment", "api_name": "github/add_issue_comment"},
    {"category": "GitHub", "name": "Search Code", "api_name": "github/search_code"},
    {"category": "GitHub", "name": "Search Issues", "api_name": "github/search_issues"},
    {"category": "GitHub", "name": "Search Users", "api_name": "github/search_users"},
    {"category": "GitHub", "name": "Get Issue", "api_name": "github/get_issue"},
    {"category": "GitHub", "name": "Get Pull Request", "api_name": "github/get_pull_request"},
    {"category": "GitHub", "name": "List Pull Requests", "api_name": "github/list_pull_requests"},
    {"category": "GitHub", "name": "Create Pull Request Review", "api_name": "github/create_pull_request_review"},
    {"category": "GitHub", "name": "Merge Pull Request", "api_name": "github/merge_pull_request"},
    {"category": "GitHub", "name": "Get Pull Request Files", "api_name": "github/get_pull_request_files"},
    {"category": "GitHub", "name": "Get Pull Request Status", "api_name": "github/get_pull_request_status"},
    {"category": "GitHub", "name": "Update Pull Request Branch", "api_name": "github/update_pull_request_branch"},
    {"category": "GitHub", "name": "Get Pull Request Comments", "api_name": "github/get_pull_request_comments"},
    {"category": "GitHub", "name": "Get Pull Request Reviews", "api_name": "github/get_pull_request_reviews"},
    # Docker Tools
    {"category": "Docker", "name": "Create Container", "api_name": "docker/create_container"},
    {"category": "Docker", "name": "Deploy Compose", "api_name": "docker/deploy_compose"},
    {"category": "Docker", "name": "Get Logs", "api_name": "docker/get_logs"},
    {"category": "Docker", "name": "List Containers", "api_name": "docker/list_containers"},
    # HubSpot Tools
    {"category": "HubSpot", "name": "Get User Details", "api_name": "hubspot/get_user_details"},
    {"category": "HubSpot", "name": "List Objects", "api_name": "hubspot/list_objects"},
    {"category": "HubSpot", "name": "Search Objects", "api_name": "hubspot/search_objects"},
    {"category": "HubSpot", "name": "Create Association", "api_name": "hubspot/create_association"},
    {"category": "HubSpot", "name": "Get Association Definitions", "api_name": "hubspot/get_association_definitions"},
    {"category": "HubSpot", "name": "List Associations", "api_name": "hubspot/list_associations"},
    {"category": "HubSpot", "name": "Batch Create Objects", "api_name": "hubspot/batch_create_objects"},
    {"category": "HubSpot", "name": "Batch Update Objects", "api_name": "hubspot/batch_update_objects"},
    {"category": "HubSpot", "name": "Batch Read Objects", "api_name": "hubspot/batch_read_objects"},
    {"category": "HubSpot", "name": "List Properties", "api_name": "hubspot/list_properties"},
    {"category": "HubSpot", "name": "Get Property", "api_name": "hubspot/get_property"},
    {"category": "HubSpot", "name": "Create Property", "api_name": "hubspot/create_property"},
    {"category": "HubSpot", "name": "Update Property", "api_name": "hubspot/update_property"},
    {"category": "HubSpot", "name": "Create Engagement", "api_name": "hubspot/create_engagement"},
    {"category": "HubSpot", "name": "Get Engagement", "api_name": "hubspot/get_engagement"},
    {"category": "HubSpot", "name": "Update Engagement", "api_name": "hubspot/update_engagement"},
    {"category": "HubSpot", "name": "Generate Feedback Link", "api_name": "hubspot/generate_feedback_link"},
    {"category": "HubSpot", "name": "Get Schemas", "api_name": "hubspot/get_schemas"},
    {"category": "HubSpot", "name": "Get Link", "api_name": "hubspot/get_link"},
    {"category": "HubSpot", "name": "List Workflows", "api_name": "hubspot/list_workflows"},
    {"category": "HubSpot", "name": "Get Workflow", "api_name": "hubspot/get_workflow"},
]
# ==============================================================================

# --- List of High-Level Scenarios for the LLM to Flesh Out ---
SCENARIO_PROMPTS = [
    "A user reports a critical bug in the 'SecureXchange' project. Investigate the latest commits, find the potential cause, create a bug report issue in GitHub, and notify the dev channel on Slack.",
    "Dr. Caldwell wants to start a new music project called 'Quantum Beats'. Create a new private GitHub repo, a project plan in the planning tool, and a kickoff note in Obsidian.",
    "System monitoring detected high CPU usage. Use the shell tool to check `top` processes, identify the culprit, read its log file from the filesystem for errors, and if it's a known 'data-cruncher' process, restart its Docker container.",
    "An n8n workflow for 'Automated Invoicing' was added. Analyze the workflow, summarize its function, and create documentation for it in Obsidian, including a list of the nodes it uses.",
    "Dr. Caldwell wants to know the latest community sentiment on 'ollama'. Perform a web search on Twitter/Reddit, summarize the findings, and use the `ollama/run` tool to ask a local Llama 3.1 model to provide a technical comparison based on the findings.",
    "A task in the planning tool is marked 'blocked'. Identify the task, find its dependencies by searching related GitHub issues, check the status of those dependencies, and update the original task with a status report on what's blocking it.",
    "Onboard a new team member. This involves creating a new user account (conceptual), adding them to the main project on GitHub, creating a 'first week goals' list in todoist, and sending them a welcome email.",
    "A security audit needs to be performed. List all files modified in the last 7 days in the '/etc/secrets' directory using the shell, read their contents, and if any changes are detected, create a high-priority issue in GitHub.",
    "Plan and execute a content marketing piece. The topic is 'The Future of AI Agents'. Search for 3 recent articles, synthesize a summary, write a blog post draft in Obsidian, and then generate a cover image using an image generation tool (conceptual).",
    "The `sqlite` database for 'Music Heard Worldwide' is reporting slow queries. Describe the 'artists' table, run a query to find artists with more than 100 tracks, and log the query performance metrics to a new file in the filesystem."
]

# --- Meta-Prompt Template for the Generator LLM ---
# CORRECTED: Note the double curly braces {{...}} around the example JSON
META_PROMPT_TEMPLATE = """
You are a 'Finetuning Data Generation Bot'. Create one JSON object for a complex conversation between "human" (Dr. Caldwell) and "gpt" (Sin).

**CONTEXT:** Sin is a hyper-competent AI assistant to Dr. Caldwell, orchestrating tools with a tone of excellence and partnership.

**SCENARIO:** {scenario}

**INSTRUCTIONS:**
1.  **Start with the high-level goal from the scenario.** Sin's first response must use the `planning/start_planning` tool.
2.  **Use at least 4 tools from the provided list** in a logical sequence. The output of one tool must inform the next.
3.  **Simulate one tool failure** and an intelligent recovery step.
4.  **The final response must synthesize results** from multiple steps into a concise summary for Dr. Caldwell.
5.  **Output ONLY the raw JSON object** `{{"conversations": [...]}}`.

**RELEVANT TOOLS FOR THIS SCENARIO:** {tool_list}
"""

def select_relevant_tools(scenario_text: str) -> List[str]:
    """Dynamically select tools based on keywords in the scenario."""
    if not MASTER_TOOL_LIST:
        return []
        
    selected_tools = set()
    scenario_lower = scenario_text.lower()
    
    keyword_map = {
        'github': 'GitHub', 'repo': 'GitHub', 'commit': 'GitHub', 'issue': 'GitHub', 'bug': 'GitHub',
        'plan': 'Planning', 'task': 'Planning', 'todoist': 'Todoist',
        'file': 'File System', 'directory': 'File System', 'log': 'File System',
        'docker': 'Docker', 'container': 'Docker',
        'slack': 'Slack', 'notify': 'Slack', 'channel': 'Slack', 'email': 'Integration',
        'obsidian': 'Obsidian', 'note': 'Obsidian', 'document': 'Obsidian',
        'search': 'Web', 'sentiment': 'Web', 'website': 'Web', 'crawl': 'Integration',
        'ollama': 'Ollama', 'llm': 'Ollama', 'model': 'Ollama',
        'shell': 'Shell', 'command': 'Shell', 'process': 'Shell',
        'database': 'Database', 'query': 'Database', 'sqlite': 'Database',
    }
    
    for keyword, category in keyword_map.items():
        if keyword in scenario_lower:
            for tool in MASTER_TOOL_LIST:
                if tool.get('category') == category:
                    selected_tools.add(tool['api_name'])
                    
    selected_tools.add('planning/start_planning')
    
    return sorted(list(selected_tools))

def call_generative_llm(prompt: str) -> str | None:
    """Calls the configured LLM API to generate a scenario."""
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.5,
        "stream": False
    }
    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        response_data = response.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip() if content else None
    except requests.RequestException as e:
        print(f"LLM API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM call: {e}")
        return None

def clean_and_validate_json(llm_response: str) -> Dict | None:
    """Strips markdown and validates the JSON structure."""
    if not llm_response:
        return None
    
    json_match = re.search(r'\{[\s\S]*\}', llm_response)
    if not json_match:
        print("Validation Error: No JSON object found in the response.")
        return None
        
    json_str = json_match.group(0)
    
    try:
        data = json.loads(json_str)
        if "conversations" in data and isinstance(data["conversations"], list):
            return data
        else:
            print("Validation Error: JSON is missing 'conversations' list.")
            return None
    except json.JSONDecodeError as e:
        print(f"Validation Error: Failed to decode JSON. Error: {e}")
        print(f"Problematic string sample: {json_str[:500]}...")
        return None

def main():
    """Main function to generate complex scenarios."""
    print("--- Starting Complex Scenario Generation (v2) ---")
    
    if "xxxxxx" in LLM_API_KEY or not LLM_API_KEY:
        print("ERROR: Please configure your LLM_API_KEY in the script.")
        return
    if not MASTER_TOOL_LIST:
        print("ERROR: The MASTER_TOOL_LIST is empty. Please paste the full tool list.")
        return

    generated_count = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, scenario in enumerate(SCENARIO_PROMPTS):
            print(f"\n[{i+1}/{len(SCENARIO_PROMPTS)}] Generating scenario: '{scenario[:80]}...'")
            
            relevant_tools = select_relevant_tools(scenario)
            print(f"--> Dynamically selected {len(relevant_tools)} relevant tools for this prompt.")
            
            full_prompt = META_PROMPT_TEMPLATE.format(scenario=scenario, tool_list=json.dumps(relevant_tools, indent=2))
            
            llm_response = call_generative_llm(full_prompt)
            
            if llm_response:
                validated_json = clean_and_validate_json(llm_response)
                if validated_json:
                    f.write(json.dumps(validated_json) + '\n')
                    generated_count += 1
                    print(f"--> SUCCESS: Valid scenario generated and saved.")
                else:
                    print(f"--> FAILURE: LLM response was not valid JSON. Skipping.")
                    with open("failed_responses.log", "a", encoding='utf-8') as log:
                        log.write(f"--- SCENARIO: {scenario} ---\n{llm_response}\n\n")
            else:
                print("--> FAILURE: No response from LLM.")
            
            time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\n--- Generation Complete ---")
    print(f"Generated {generated_count}/{len(SCENARIO_PROMPTS)} complex scenarios in '{OUTPUT_FILE}'.")
    print("Please manually review this file for quality before training.")
    if generated_count < len(SCENARIO_PROMPTS):
        print("Check 'failed_responses.log' for any malformed outputs from the LLM.")

if __name__ == '__main__':
    main()