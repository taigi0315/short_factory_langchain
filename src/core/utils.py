import os
import json
from datetime import datetime
from typing import Any, Dict

def save_json_output(data: Dict[str, Any], filename_prefix: str, output_dir: str = "output"):
    """Save dictionary data to a JSON file with timestamp."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath
