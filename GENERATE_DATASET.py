# filename: generate_foundational_dataset_v2.py

import json
import re

# --- Configuration ---
OUTPUT_FILE = 'foundational_dataset.jsonl'

# This is the full list of 205 tools you provided, structured for the script.
ALL_TOOLS = [
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

def generate_examples_for_tool(tool):
    """Generates knowledge, simple, and complex use examples for a single tool."""
    examples = []
    
    # 1. Knowledge Retrieval Example
    examples.append({
        "conversations": [
            {"from": "human", "value": f"Sin, what does the `{tool['api_name']}` tool do?"},
            {"from": "gpt", "value": f"The `{tool['api_name']}` tool is used to {tool['name'].lower()}."}
        ]
    })
    
    # 2. Simple Tool Use Example
    examples.append({
        "conversations": [
            {"from": "human", "value": f"hi Sin I need to use `{tool['api_name']}`."},
            {"from": "gpt", "value": None, "tool_calls": [{
                "id": f"call_{tool['api_name'].replace('/', '_')}_simple",
                "name": tool['api_name'],
                "arguments": {"param1": "test_value_1"}
            }]}
        ]
    })
    
    # 3. Complex Tool Use Example
    examples.append({
        "conversations": [
            {"from": "human", "value": f"Hey Sin, can you run a complex operation using `{tool['api_name']}` with several parameters?"},
            {"from": "gpt", "value": None, "tool_calls": [{
                "id": f"call_{tool['api_name'].replace('/', '_')}_complex",
                "name": tool['api_name'],
                "arguments": {"param1": "complex_value_1", "param2": "complex_value_2", "optionA": True}
            }]}
        ]
    })
    
    return examples

def main():
    """Main function to generate the foundational dataset."""
    print("--- Starting Foundational Dataset Generation (v2) ---")
    
    all_examples = []
    print(f"Processing {len(ALL_TOOLS)} tools from the master list...")
    
    for tool in ALL_TOOLS:
        all_examples.extend(generate_examples_for_tool(tool))
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example) + '\n')
            
    print(f"\n--- Generation Complete ---")
    print(f"Generated {len(all_examples)} foundational examples into '{OUTPUT_FILE}'.")
    print("This dataset covers Q&A, simple, and complex tool usage for every tool provided.")

if __name__ == '__main__':
    main()