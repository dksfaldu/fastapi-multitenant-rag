import os
import json
import datetime
from app.engine import STORAGE_ROOT

def log_project_action(project_id: str, action: str, details: str):
    """
    Appends an API action layout specifically tracked to a target project's log footprint.
    """
    persist_dir = os.path.join(STORAGE_ROOT, project_id)
    os.makedirs(persist_dir, exist_ok=True)
    
    log_file = os.path.join(persist_dir, "activity.jsonl")
    
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "details": details
    }
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to write log for {project_id}: {e}")

def get_project_logs(project_id: str):
    """
    Fetch all logs connected to the project.
    """
    persist_dir = os.path.join(STORAGE_ROOT, project_id)
    log_file = os.path.join(persist_dir, "activity.jsonl")
    
    if not os.path.exists(log_file):
        return []
        
    logs = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    # Reverse to show newest first
    return logs[::-1]

def get_all_projects_stats():
    """
    Retrieves internal stats regarding project sizes, scanning LlamaIndex docstores.
    """
    stats = []
    if not os.path.exists(STORAGE_ROOT):
        return stats
        
    for project_id in os.listdir(STORAGE_ROOT):
        persist_dir = os.path.join(STORAGE_ROOT, project_id)
        if os.path.isdir(persist_dir):
            docstore_path = os.path.join(persist_dir, "docstore.json")
            doc_count = 0
            if os.path.exists(docstore_path):
                try:
                    with open(docstore_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # LlamaIndex stores document tracking references under docstore/ref_doc_info
                        ref_doc_info = data.get("docstore/ref_doc_info", {})
                        doc_count = len(ref_doc_info)
                except Exception:
                    pass
            
            stats.append({
                "project_id": project_id,
                "document_count": doc_count
            })
            
    return stats
