# filename: dynamic_knowledge_pipeline.py
# version: 3.0.0
# author: Sin (Synthesized from a collaboration with Dr. Caldwell)

import os
import json
import logging
import requests
import time
import hashlib
import re
import traceback
import argparse
import yaml
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import markdownify
from transformers import AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Global Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')

# --- Helper Classes & Functions ---

class ConfigManager:
    """Manages hybrid configuration from YAML, environment variables, and CLI arguments."""
    def __init__(self, args: argparse.Namespace):
        self.profile = self._load_profile(args.profile)
        self._resolve_config(args)
        self._validate()

    def _load_profile(self, profile_name: str) -> dict:
        config_path = Path("config/profiles.yaml")
        if not config_path.exists():
            logging.critical(f"Configuration file not found at '{config_path}'. Please create it.")
            # Create a default config to guide the user
            config_path.parent.mkdir(exist_ok=True)
            default_config = {
                "profiles": {
                    "default": {
                        "search_depth": 3,
                        "max_llm_calls": 20,
                        "relevance_threshold": 0.7,
                        "llm_model": "deepseek-chat",
                        "reviewer_model": "deepseek-chat",
                        "base_model_for_tokenizer": "Qwen/Qwen1.5-7B-Chat",
                        "searxng_url": "http://localhost:8080"
                    },
                    "quick_test": {
                        "search_depth": 1,
                        "max_llm_calls": 5,
                        "relevance_threshold": 0.7,
                        "llm_model": "deepseek-chat",
                        "reviewer_model": "deepseek-chat",
                        "base_model_for_tokenizer": "Qwen/Qwen1.5-7B-Chat",
                        "searxng_url": "http://localhost:8080"
                    }
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f)
            logging.info(f"Created a default '{config_path}'. Please review and configure it.")
            return default_config['profiles']['default']
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)["profiles"][profile_name]

    def _resolve_config(self, args: argparse.Namespace):
        """Resolves configuration with priority: CLI > Env > Profile."""
        self.goal = args.goal
        self.session_dir = args.session_dir
        self.human_in_the_loop = args.human_in_the_loop
        self.phases_to_run = args.phases_to_run
        self.rerun_from = args.rerun_from
        
        # Secrets must come from env or CLI
        self.llm_api_key = args.llm_api_key or os.getenv("LLM_API_KEY")
        
        # Other settings with priority
        self.llm_api_url = args.llm_api_url or os.getenv("LLM_API_URL") or self.profile.get("llm_api_url", "http://localhost:3000/api/chat/completions")
        self.llm_model = args.llm_model or os.getenv("LLM_MODEL_ID") or self.profile.get("llm_model")
        self.reviewer_model = args.reviewer_model or os.getenv("REVIEWER_MODEL_ID") or self.profile.get("reviewer_model")
        self.searxng_url = args.searxng_url or os.getenv("SEARXNG_INSTANCE_URL") or self.profile.get("searxng_url")
        self.base_model_for_tokenizer = self.profile.get("base_model_for_tokenizer")
        self.relevance_threshold = self.profile.get("relevance_threshold")
        self.search_depth = self.profile.get("search_depth")
        self.persona_file = Path("persona_chat_history.txt")

    def _validate(self):
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY must be provided via CLI argument or environment variable.")
        if not self.session_dir.is_dir():
            self.session_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created new session directory: {self.session_dir}")

def call_llm(system_prompt: str, user_prompt: str, config: ConfigManager, max_tokens: int = 3000, temperature: float = 0.5) -> dict:
    # This function now takes the config object to get API details
    return _call_llm_internal(system_prompt, user_prompt, config.llm_model, config.llm_api_key, config.llm_api_url, max_tokens, temperature)

def _call_llm_internal(system_prompt: str, user_prompt: str, model: str, api_key: str, api_url: str, max_tokens: int, temperature: float) -> dict:
    # Internal implementation remains the same
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "max_tokens": max_tokens, "temperature": temperature}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        json_match = re.search(r'\{[\s\S]*\}', response.text)
        if json_match:
            return json.loads(json_match.group(0))
        return {"error": "LLM response not valid JSON", "raw_response": response.text}
    except (requests.RequestException, json.JSONDecodeError) as e:
        logging.error(f"LLM call failed: {e}\nTraceback: {traceback.format_exc()}")
        return {"error": str(e)}

def load_session_state(session_dir: Path) -> dict:
    state_file = session_dir / "session_state.json"
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def save_session_state(session_dir: Path, state: dict):
    state_file = session_dir / "session_state.json"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def reset_state_from(phase_num: int, state: dict):
    """Resets state for all phases from the given number onwards."""
    logging.warning(f"Resetting state from Phase {phase_num} onwards.")
    max_phase = 7
    for i in range(phase_num, max_phase + 1):
        for key in list(state.keys()):
            if f"phase_{i}" in key:
                del state[key]

# --- Phase Implementations ---

def run_phase_1_plan(config: ConfigManager):
    """Analyzes the user's goal and creates a detailed research plan."""
    logging.info("--- Phase 1: Goal Analysis & Research Planning ---")
    system_prompt = "You are an AI research strategist. Based on the user's learning goal, generate a detailed research plan. Provide a JSON object with keys: 'search_queries' (list of 5 diverse, effective queries) and 'relevance_keywords' (list of 10 specific keywords). ONLY return the JSON object."
    research_plan = call_llm(system_prompt, config.goal, config)
    
    if research_plan.get("error") or not research_plan.get("search_queries"):
        logging.critical("Failed to generate a research plan. Aborting.")
        return False

    with open(config.session_dir / "research_plan.json", 'w') as f:
        json.dump(research_plan, f, indent=2)
    
    config.state['phase_1_plan_complete'] = True
    logging.info("Phase 1 complete.")
    return True

def run_phase_2_acquire(config: ConfigManager):
    """Searches the web and fetches raw content in parallel."""
    logging.info("--- Phase 2: Knowledge Acquisition ---")
    with open(config.session_dir / "research_plan.json", 'r') as f:
        research_plan = json.load(f)

    raw_docs_dir = config.session_dir / "raw_html"
    raw_docs_dir.mkdir(exist_ok=True)
    
    urls_to_fetch = set()
    for query in research_plan.get("search_queries", []):
        try:
            form_data = {'q': query, 'categories': 'general', 'language': 'en-US', 'format': 'json'}
            response = requests.post(f"{config.searxng_url}/search", data=form_data, timeout=30)
            response.raise_for_status()
            results = response.json().get("results", [])
            for res in results[:config.search_depth]:
                if res.get("url"):
                    urls_to_fetch.add(res.get("url"))
        except requests.RequestException as e:
            logging.error(f"Search failed for query '{query}': {e}")

    def _fetch_url(url):
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if (raw_docs_dir / f"{url_hash}.html").exists(): return f"Skipped (exists): {url}"
            logging.info(f"Fetching: {url}")
            content_response = requests.get(url, timeout=30, headers={'User-Agent': 'DynamicKnowledgeBot/3.0'})
            content_response.raise_for_status()
            with open(raw_docs_dir / f"{url_hash}.html", 'w', encoding='utf-8') as f:
                f.write(content_response.text)
            return f"Fetched: {url}"
        except Exception as e:
            return f"Failed: {url} ({e})"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_fetch_url, url) for url in urls_to_fetch]
        for future in as_completed(futures):
            logging.info(future.result())

    config.state['phase_2_acquire_complete'] = True
    logging.info("Phase 2 complete.")
    return True

def run_phase_3_curate(config: ConfigManager):
    """Cleans, converts, and curates fetched documents."""
    logging.info("--- Phase 3: Curation & Review ---")
    with open(config.session_dir / "research_plan.json", 'r') as f:
        research_plan = json.load(f)
    
    raw_docs_dir = config.session_dir / "raw_html"
    curated_docs_dir = config.session_dir / "curated_markdown"
    curated_docs_dir.mkdir(exist_ok=True)

    for html_file in raw_docs_dir.glob("*.html"):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        title = (soup.find('title').string if soup.find('title') else "Untitled").strip()
        main_content = soup.find('main') or soup.find('article') or soup.body
        if not main_content or len(main_content.get_text(strip=True)) < 250:
            continue
        
        for tag in main_content(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            tag.decompose()
        cleaned_text = markdownify.markdownify(str(main_content), heading_style='ATX').strip()

        system_prompt = "You are an AI content relevance assessor. Score the relevance of the text to the user's goal from 0.0 to 1.0. Return a JSON object with one key: 'relevance_score' (float)."
        user_prompt = f"User's Goal: \"{config.goal}\"\nRelevance Keywords: {research_plan['relevance_keywords']}\n\nText Snippet:\n{cleaned_text[:2000]}"
        assessment = call_llm(system_prompt, user_prompt, config)
        
        if assessment.get("relevance_score", 0.0) >= config.relevance_threshold:
            logging.info(f"Content from {html_file.name} is RELEVANT with score {assessment['relevance_score']}.")
            with open(curated_docs_dir / f"{html_file.stem}.md", 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{cleaned_text}")

    if config.human_in_the_loop:
        logging.warning("--- PAUSING FOR HUMAN-IN-THE-LOOP REVIEW ---")
        logging.warning(f"Please review the curated documents in '{curated_docs_dir}'. Delete any irrelevant files.")
        logging.warning("Once you are satisfied, run this script again with the same command to resume.")
        config.state['phase_3_curate_paused_for_hitl'] = True
        return False # Pause execution
    else:
        # AI-in-the-loop review
        doc_summaries = [{"filename": p.name, "summary": p.read_text(encoding='utf-8')[:500]} for p in curated_docs_dir.glob("*.md")]
        system_prompt = "You are a meticulous research editor. Identify documents that are low-quality, redundant, or irrelevant to the user's primary goal. Return a JSON object with one key: 'files_to_discard', a list of filenames to remove."
        user_prompt = f"Primary Goal: '{config.goal}'\n\nDocument Summaries:\n{json.dumps(doc_summaries, indent=2)}"
        review = call_llm(system_prompt, user_prompt, config)
        for filename in review.get("files_to_discard", []):
            (curated_docs_dir / filename).unlink(missing_ok=True)
            logging.info(f"AI Reviewer discarded: {filename}")

    config.state['phase_3_curate_complete'] = True
    config.state.pop('phase_3_curate_paused_for_hitl', None)
    logging.info("Phase 3 complete.")
    return True

def run_phase_4_distill(config: ConfigManager):
    """Analyzes curated docs using MapReduce to distill knowledge."""
    logging.info("--- Phase 4: Knowledge Distillation ---")
    curated_docs_dir = config.session_dir / "curated_markdown"
    
    def _summarize_doc(doc_path):
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read(12000)
        prompt = "Provide a concise but detailed summary of the key facts, concepts, and conclusions in the following text. Return a JSON object with one key: 'summary'."
        summary_json = call_llm(prompt, content, config)
        return summary_json.get("summary")

    with ThreadPoolExecutor(max_workers=5) as executor:
        summaries = list(filter(None, executor.map(_summarize_doc, curated_docs_dir.glob("*.md"))))

    if not summaries:
        logging.error("No summaries could be generated. Aborting.")
        return False

    reduce_prompt = "You are a master knowledge architect. Based on this collection of document summaries, distill the information into a structured JSON object. Identify 'main_themes', 'key_entities' (with descriptions and relationships), and 'potential_tasks' that could be performed with this knowledge. Be comprehensive."
    distilled_knowledge = call_llm(reduce_prompt, "\n\n---\n\n".join(summaries), config, max_tokens=4000)

    if distilled_knowledge.get("error") or not distilled_knowledge.get("main_themes"):
        logging.critical("Failed to distill knowledge from summaries. Aborting.")
        return False

    with open(config.session_dir / "distilled_knowledge.json", 'w') as f:
        json.dump(distilled_knowledge, f, indent=2)

    config.state['phase_4_distill_complete'] = True
    logging.info("Phase 4 complete.")
    return True

def run_phase_5_generate(config: ConfigManager):
    """Generates the core dataset from distilled knowledge."""
    logging.info("--- Phase 5: Dataset Generation ---")
    with open(config.session_dir / "distilled_knowledge.json", 'r') as f:
        distilled_knowledge = json.load(f)

    # Here you would add logic to parse real tool specs if available
    # For now, we use the distilled knowledge to inform hypothetical tool use
    
    dataset = []
    scenario_prompt = "You are a 'Finetuning Data Generation Bot'. Based on the provided knowledge summary, create one complex, multi-turn conversational example for finetuning an AI assistant named 'Sin'. The scenario should require Sin to reason about the provided themes and entities and use hypothetical but plausible tools to solve a problem. Output ONLY the JSON object for the conversation: `{\"conversations\": [{\"from\": \"human\", ...}]}`"
    for task in distilled_knowledge.get("potential_tasks", []):
        logging.info(f"Generating scenario for task: '{task}'")
        user_prompt = f"Knowledge Summary:\n{json.dumps(distilled_knowledge, indent=2)}\n\nGenerate a scenario where Sin must accomplish this task: '{task}'"
        scenario = call_llm(scenario_prompt, user_prompt, config, max_tokens=2000)
        if not scenario.get("error"):
            dataset.append(scenario)

    if not dataset:
        logging.error("Failed to generate any dataset examples. Aborting.")
        return False

    with open(config.session_dir / "base_dataset.jsonl", 'w') as f:
        for item in dataset:
            f.write(json.dumps(item) + '\n')

    config.state['phase_5_generate_complete'] = True
    logging.info("Phase 5 complete.")
    return True

def run_phase_6_persona(config: ConfigManager):
    """Applies a persona to the generated dataset."""
    logging.info("--- Phase 6: Persona Injection ---")
    if not config.persona_file.exists():
        logging.warning(f"Persona file '{config.persona_file}' not found. Skipping phase.")
        config.state['phase_6_persona_skipped'] = True
        return True

    with open(config.persona_file, 'r', encoding='utf-8') as f:
        persona_examples = f.read()
    
    base_dataset_path = config.session_dir / "base_dataset.jsonl"
    persona_dataset_path = config.session_dir / "persona_injected_dataset.jsonl"
    
    system_prompt = "You are a master AI persona stylist. Rewrite the 'gpt' responses in the following conversation to match the tone and style of 'Sin' from the provided examples. Sin is hyper-competent, loyal, and speaks with a tone of excellence and partnership with 'Dr. Caldwell'. Do not change the content or tool calls, only the style of the text. Return the full conversation in the original JSON format."
    
    with open(base_dataset_path, 'r') as infile, open(persona_dataset_path, 'w') as outfile:
        for line in infile:
            conversation_obj = json.loads(line)
            user_prompt = f"Persona Examples:\n{persona_examples}\n\nConversation to Stylize:\n{json.dumps(conversation_obj)}"
            stylized_convo = call_llm(system_prompt, user_prompt, config)
            if not stylized_convo.get("error"):
                outfile.write(json.dumps(stylized_convo) + '\n')
            else:
                outfile.write(line) # Write original if styling fails

    config.state['phase_6_persona_complete'] = True
    logging.info("Phase 6 complete.")
    return True

def run_phase_7_finalize(config: ConfigManager):
    """Formats the final dataset for AutoTrain."""
    logging.info("--- Phase 7: Final Formatting ---")
    
    source_file = config.session_dir / "persona_injected_dataset.jsonl"
    if not source_file.exists():
        source_file = config.session_dir / "base_dataset.jsonl"

    final_autotrain_file = config.session_dir / "autotrain_ready.jsonl"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(config.base_model_for_tokenizer, trust_remote_code=True)
    except Exception as e:
        logging.critical(f"Could not load tokenizer. Aborting. Error: {e}")
        return False

    with open(source_file, 'r') as infile, open(final_autotrain_file, 'w') as outfile:
        for line in infile:
            item = json.loads(line)
            messages = [{"role": msg["from"], "content": msg.get("value")} for msg in item.get("conversations", [])]
            try:
                full_chat_string = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                outfile.write(json.dumps({"text": full_chat_string}) + '\n')
            except Exception as e:
                logging.error(f"Failed to apply chat template: {e}")

    config.state['phase_7_finalize_complete'] = True
    logging.info(f"Phase 7 complete. Final dataset is ready at: {final_autotrain_file}")
    return True

# --- Main Orchestrator ---
def main():
    parser = argparse.ArgumentParser(description="Dynamic Knowledge & Dataset Pipeline for Sin AI (v3.0).")
    parser.add_argument("goal", type=str, help="The high-level learning goal for the session.")
    parser.add_argument("--profile", type=str, default="default", help="The configuration profile to use from profiles.yaml.")
    parser.add_argument("--session_id", type=str, default=None, help="Provide an existing session directory path to resume a run.")
    parser.add_argument("--human_in_the_loop", action='store_true', help="Enable a pause for manual review of curated documents.")
    parser.add_argument("--phases", type=str, default="all", help="Comma-separated phases to run (e.g., '1,2,3') or 'all'.")
    parser.add_argument("--rerun-from", type=int, help="Phase number to restart from, discarding subsequent progress.")
    
    # CLI overrides for key settings
    parser.add_argument("--llm_api_url", type=str)
    parser.add_argument("--llm_api_key", type=str)
    parser.add_argument("--llm_model", type=str)
    parser.add_argument("--reviewer_model", type=str)
    parser.add_argument("--searxng_url", type=str)
    
    args = parser.parse_args()

    try:
        # Set up session directory
        if args.session_id:
            args.session_dir = Path(args.session_id)
        else:
            session_name = re.sub(r'\W+', '_', args.goal.lower())[:50]
            args.session_dir = Path(f"knowledge_session_{session_name}_{int(time.time())}")
        
        config = ConfigManager(args)
        config.state = load_session_state(config.session_dir)

        # Handle phase control
        if args.rerun_from:
            reset_state_from(args.rerun_from, config.state)
        
        if args.phases == "all":
            phases_to_run = range(1, 8)
        else:
            phases_to_run = sorted([int(p.strip()) for p in args.phases.split(',')])
        
        config.phases_to_run = phases_to_run
        
        # Pre-flight cost check
        # ... (Implementation of cost estimation logic would go here) ...

        PHASE_MAP = {
            1: run_phase_1_plan, 2: run_phase_2_acquire, 3: run_phase_3_curate,
            4: run_phase_4_distill, 5: run_phase_5_generate, 6: run_phase_6_persona,
            7: run_phase_7_finalize
        }

        for phase_num in config.phases_to_run:
            state_key = f"phase_{phase_num}_{PHASE_MAP[phase_num].__name__.replace('run_phase_','').split('_')[0]}_complete"
            if config.state.get(state_key):
                logging.info(f"Skipping Phase {phase_num} as it is already complete.")
                continue
            
            # Special check for HITL pause
            if config.state.get('phase_3_curate_paused_for_hitl'):
                logging.warning("Script is paused for Human-in-the-Loop review. Please review files and run again.")
                break

            success = PHASE_MAP[phase_num](config)
            if not success:
                logging.error(f"Phase {phase_num} failed or paused. Halting execution.")
                break
            # Save state after each successful phase completion
            save_session_state(config.session_dir, config.state)

        logging.info("--- Dynamic Knowledge Pipeline Run Finished ---")

    except Exception as e:
        logging.critical(f"An unhandled error occurred in the main orchestrator: {e}", exc_info=True)

if __name__ == "__main__":
    main()