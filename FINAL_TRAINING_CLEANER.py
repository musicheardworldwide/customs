# filename: convert_final_dataset.py

import json
from typing import List, Dict, Any, Union

INPUT_FILE = 'complex_scenarios_dataset.jsonl'  # The new file with 10 successful scenarios
OUTPUT_FILE = 'final_complex_dataset.jsonl'

def extract_text(data: Union[Dict, str]) -> str:
    """Safely extracts a text message from various possible dictionary structures or a direct string."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ['content', 'message', 'text', 'response', 'summary']:
            if isinstance(data.get(key), str):
                return data[key]
    return ""  # Return empty string if no text is found

def parse_and_convert_scenario(data: Dict) -> List[Dict[str, Any]]:
    """
    The main parsing logic that intelligently converts a single, complex scenario
    into the correct finetuning format.
    """
    conversation = []
    
    # The generator often wraps the conversation in a 'conversations' key
    turns = data.get('conversations', [])
    if not isinstance(turns, list):
        return []

    call_id_counter = 0

    for turn in turns:
        # --- Identify Human Turn ---
        human_content = None
        for key in ['human', 'Dr. Caldwell']:
            if key in turn:
                human_content = extract_text(turn[key])
                break
        
        if human_content:
            conversation.append({"from": "human", "value": human_content})
            continue # Move to next turn after processing

        # --- Identify GPT Turn (could be thought, tool call, or final response) ---
        gpt_content = None
        gpt_data = None
        for key in ['gpt', 'Sin']:
            if key in turn:
                gpt_data = turn[key]
                gpt_content = extract_text(gpt_data)
                break
        
        if gpt_data is not None:
            tool_calls = []
            
            # Check for various tool call formats
            # Format 1: "tool_uses": [{"recipient_name": ..., "parameters": ...}]
            if "tool_uses" in gpt_data and isinstance(gpt_data["tool_uses"], list):
                for tool_use in gpt_data["tool_uses"]:
                    tool_name = tool_use.get("recipient_name", "").replace("functions.", "")
                    if tool_name:
                        tool_calls.append({
                            "id": f"call_{call_id_counter}",
                            "name": tool_name,
                            "arguments": tool_use.get("parameters", {})
                        })
                        call_id_counter += 1

            # Format 2: "tool": "tool/name", "input": {...}
            elif "tool" in gpt_data and isinstance(gpt_data.get("tool"), str):
                tool_calls.append({
                    "id": f"call_{call_id_counter}",
                    "name": gpt_data["tool"],
                    "arguments": gpt_data.get("input", {})
                })
                call_id_counter += 1

            # Add the GPT turn to the conversation
            conversation.append({
                "from": "gpt",
                "value": gpt_content or None, # Use text if available, otherwise null for pure tool call
                "tool_calls": tool_calls if tool_calls else None
            })

            # Check for corresponding tool responses in the same turn object
            # Format 1: "tool_responses": [{"name": ..., "content": ...}]
            if "tool_responses" in turn and isinstance(turn["tool_responses"], list):
                # This assumes a 1:1 mapping with tool_uses, which is a reasonable heuristic
                for i, tool_response in enumerate(turn["tool_responses"]):
                    # Find the corresponding call_id
                    corresponding_call_id = call_id_counter - len(tool_calls) + i
                    conversation.append({
                        "from": "tool",
                        "tool_call_id": f"call_{corresponding_call_id}",
                        "value": json.dumps(tool_response.get("content", {}))
                    })
            
            # Format 2: "observation": "..." or {"..."}, "error": "..."
            elif "observation" in turn or "error" in turn:
                 tool_response_content = turn.get("observation", {"error": turn.get("error", "Unknown error")})
                 conversation.append({
                     "from": "tool",
                     "tool_call_id": f"call_{call_id_counter - 1}",
                     "value": json.dumps(tool_response_content) if isinstance(tool_response_content, dict) else tool_response_content
                 })

    # Clean up any turns that don't have a valid 'from' key
    return [turn for turn in conversation if "from" in turn]


def main():
    print(f"--- Starting Final Conversion of '{INPUT_FILE}' (v4) ---")
    
    all_conversations = []
    skipped_lines = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line)
                parsed_convo = parse_and_convert_scenario(data)

                if parsed_convo and len(parsed_convo) > 1:
                    all_conversations.append({"conversations": parsed_convo})
                    print(f"Line {i+1}: Success - Converted scenario with {len(parsed_convo)} turns.")
                else:
                    print(f"Line {i+1}: Could not extract a valid conversation. Skipping.")
                    skipped_lines += 1

            except json.JSONDecodeError as e:
                print(f"Line {i+1}: Invalid JSON. Skipping. Error: {e}")
                skipped_lines += 1
            except Exception as e:
                print(f"Line {i+1}: An unexpected error occurred: {e}. Skipping.")
                skipped_lines += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for convo in all_conversations:
            f.write(json.dumps(convo) + '\n')
            
    print(f"\n--- Conversion Complete ---")
    print(f"Successfully converted {len(all_conversations)} scenarios into '{OUTPUT_FILE}'.")
    print(f"Skipped {skipped_lines} lines due to parsing errors or unrecognized formats.")
    print("This file is now in the correct format for finetuning. Please review for logical consistency.")

if __name__ == '__main__':
    main()