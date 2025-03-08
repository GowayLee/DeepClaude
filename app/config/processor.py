"""Config processing functions"""

import time
from pathlib import Path

import yaml

from app.utils.config.manager import ModelConfigManager


def generate_shown_models(output_path: Path):
    """Generate a list of models to be shown based on deep_models in model_config"""

    models = []
    for deep_model in ModelConfigManager.get_model_config().deep_models:
        model_id = deep_model.name
        permission_id = f"modelperm-{model_id}"
        create_time = int(time.time())

        model_entry = {
            "id": model_id,
            "object": "model",
            "created": create_time,
            "owned_by": "deepclaude",
            "permission": [
                {
                    "id": permission_id,
                    "object": "model_permission",
                    "created": create_time,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False,
                }
            ],
            "root": model_id,
            "parent": None,
        }
        models.append(model_entry)

    # Construct output data structure
    output_data = {"models": models}

    # Write to output file
    with open(output_path, "w") as f:
        yaml.dump(output_data, f, sort_keys=False, default_flow_style=False)
