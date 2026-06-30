import os
import json
import importlib.util

PLUGINS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../tars-plugins"))


def _load_manifest(plugin_path: str) -> dict:
    manifest_path = os.path.join(plugin_path, "manifest.json")
    if not os.path.isfile(manifest_path):
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_entrypoint(plugin_path: str, entrypoint: str):
    module_name, func_name = entrypoint.split(".")
    module_path = os.path.join(plugin_path, f"{module_name}.py")

    if not os.path.isfile(module_path):
        return None

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except Exception:
        return None

    return getattr(module, func_name, None)


def discover_agents() -> dict:
    agents = {}

    if not os.path.isdir(PLUGINS_DIR):
        return agents

    for entry in os.listdir(PLUGINS_DIR):
        plugin_path = os.path.join(PLUGINS_DIR, entry)
        if not os.path.isdir(plugin_path):
            continue

        manifest = _load_manifest(plugin_path)
        if not manifest:
            continue

        name = manifest.get("name")
        entrypoint = manifest.get("entrypoint")
        description = manifest.get("description", "")

        if not name or not entrypoint:
            continue

        run_func = _load_entrypoint(plugin_path, entrypoint)
        if not run_func:
            continue

        agents[name] = {
            "description": description,
            "run": run_func
        }

    return agents