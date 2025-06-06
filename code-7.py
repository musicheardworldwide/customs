# filename: generate_dataset.py

import os
import re
import json
import glob
from typing import List, Dict, Any

# --- Configuration ---
# This directory should contain all your .md and .json knowledge files.
KNOWLEDGE_BASE_PATH = './ingest' 
OUTPUT_FILE = 'foundational_dataset.jsonl'

def create_conversation_json(conversation_list: List[Dict[str, Any]]) -> Dict:
    """Formats a list of conversation turns into the final JSON structure."""
    return {"conversations": conversation_list}

def parse_api_doc(content: str) -> List[Dict[str, Any]]:
    """Parses a markdown API doc to extract tool endpoints."""
    # Regex to find h3 or h4 headers for endpoints like ### /tool/action or #### `POST`
    endpoint_pattern = re.compile(r"###\s+`?(/[\w/-]+)`?|####\s+`POST`\s+([\s\S]*?)\n\n", re.MULTILINE)
    description_pattern = re.compile(r"Description\s*:\s*([\s\S]*?)\n\n|Description\s*([\s\S]*?)\n\n", re.MULTILINE)
    
    tools = []
    
    # Simple parsing logic for this example. A real one might be more robust.
    # This is a placeholder for a more sophisticated parsing strategy based on your doc's structure.
    # For now, we'll manually define a few based on the provided files.
    # A real script would use the regex above to find all tools.
    
    # Example manual definitions based on your docs:
    tools.append({"name": "github/create_repository", "description": "Create a new GitHub repository.", "params": ["name", "description", "private"]})
    tools.append({"name": "filesystem/read_file", "description": "Read the contents of a file.", "params": ["path"]})
    tools.ap pend({"name": "taskmanager/request_planning", "description": "Register a new user request and plan its associated tasks.", "params": ["originalRequest", "tasks"]})
    tools.append({"name": "graphlit/webSearch", "description": "Performs web or podcast search based on search query.", "params": ["query"]})
    
    return tools

def generate_tool_use_examples(tool: Dict[str, Any]) -> List[Dict]:
    """Generates simple and complex tool use examples."""
    examples = []
    
    # Simple call with required params
    human_simple = f"I need to use the {tool['name']} tool."
    # A more sophisticated version would know which params are required vs. optional
    simple_args = {p: f"sample_{p}" for p in tool.get('params', [])[:1]}
    if not simple_args: return [] # Skip if no params
    
    assistant_simple = [{"from": "gpt", "value": None, "tool_calls": [{"id": f"call_{tool['name'].replace('/','_')}_1", "name": tool['name'], "arguments": simple_args}]}]
    examples.append(create_conversation_json([{"from": "human", "value": human_simple}] + assistant_simple))
    
    return examples

def generate_knowledge_examples(tool: Dict[str, Any]) -> List[Dict]:
    """Generates Q&A examples about a tool's function."""
    examples = []
    
    # Question about the tool's purpose
    human_q = f"What does the {tool['name']} tool do?"
    assistant_a = tool['description']
    examples.append(create_conversation_json([{"from": "human", "value": human_q}, {"from": "gpt", "value": assistant_a}]))
    
    return examples

def parse_n8n_workflow(filepath: str) -> List[Dict]:
    """Parses an n8n JSON workflow to create analysis examples."""
    examples = []
    with open(filepath, 'r', encoding='utf-8') as f:
        workflow_data_str = f.read()
        
    try:
        # Find the full JSON documentation block
        full_doc_match = re.search(r"## Full Documentation\n(\{.*?\n\})", workflow_data_str, re.DOTALL)
        if not full_doc_match:
            return []
            
        workflow_json = json.loads(full_doc_match.group(1))
        
        workflow_name = workflow_json.get('name', 'Unnamed Workflow')
        nodes = workflow_json.get('nodes', [])
        node_names = [node.get('name', 'unnamed node') for node in nodes]
        
        # Example 1: Summarize the workflow
        human_q1 = f"Can you give me a high-level summary of the '{workflow_name}' n8n workflow?"
        assistant_a1 = f"The '{workflow_name}' workflow involves the following steps: " + " -> ".join(node_names) + ". Its primary purpose seems to be [AI would infer purpose based on node types, e.g., 'data extraction and storage']."
        examples.append(create_conversation_json([{"from": "human", "value": human_q1}, {"from": "gpt", "value": assistant_a1}]))

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Skipping malformed n8n file {filepath}: {e}")
    
    return examples


def main():
    all_examples = []
    
    # Process API docs
    md_files = glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, '*.md'))
    for filepath in md_files:
        print(f"Processing Markdown file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # This is a placeholder for your more robust parsing logic.
        # For this script, we'll use a manually curated list of tools for reliability.
    
    # Using a predefined tool list extracted from your docs
    all_tools = [
        {"name": "github/create_repository", "description": "Create a new GitHub repository in your account.", "params": ["name", "description", "private"]},
        {"name": "filesystem/read_file", "description": "Read the complete contents of a file from the file system.", "params": ["path"]},
        {"name": "taskmanager/request_planning", "description": "Register a new user request and plan its associated tasks.", "params": ["originalRequest", "tasks"]},
        {"name": "graphlit/webSearch", "description": "Performs web or podcast search based on search query.", "params": ["query"]},
        {"name": "obsidian/obsidian_simple_search", "description": "Simple search for documents matching a specified text query across all files in the vault.", "params": ["query"]},
        {"name": "sqlite/read_query", "description": "Execute a SELECT query on the SQLite database.", "params": ["query"]},
    ]
    
    for tool in all_tools:
        all_examples.extend(generate_tool_use_examples(tool))
        all_examples.extend(generate_knowledge_examples(tool))
        
    # Process n8n workflows
    n8n_files = glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, '*.md')) # Assuming n8n JSON is inside MD
    for filepath in n8n_files:
        # Simple check if it's likely an n8n doc
        with open(filepath, 'r', encoding='utf-8') as f:
            if "## Full Documentation" in f.read():
                print(f"Processing n8n workflow file: {filepath}")
                all_examples.extend(parse_n8n_workflow(filepath))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example) + '\n')
            
    print(f"\nGenerated {len(all_examples)} foundational examples in '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    main()