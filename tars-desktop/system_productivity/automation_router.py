import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system_core/brain")))

from tracer import emit
import automation_registry as app_manager


def execute_automation(action: str, params: dict) -> str:
    emit(f"Running: {action}", "action")

    if action == "add_app":
        return app_manager.add_app(
            name=params.get("name", ""),
            command=params.get("command", ""),
            workspace=params.get("workspace"),
            aliases=params.get("aliases", []),
            url=params.get("url", ""),
            url_base=params.get("url_base", "")
        )

    elif action == "delete_app":
        return app_manager.delete_app(params.get("name", ""))

    elif action == "add_environment":
        return app_manager.add_environment(params.get("name", ""))

    elif action == "delete_environment":
        return app_manager.delete_environment(params.get("name", ""))

    elif action == "list_configured_apps":
        result = app_manager.list_configured_apps_tars()
        if not result:
            return "No apps configured yet."
        names = ", ".join(a["name"] for a in result)
        return f"Configured apps: {names}."

    elif action == "sync_installed_apps":
        return app_manager.sync_installed_apps()

    elif action == "list_environments":
        result = app_manager.list_environments()
        if not result:
            return "No environments saved yet."
        names = ", ".join(e["name"] for e in result)
        return f"Saved environments: {names}."

    elif action in ("chat", "unknown", "error"):
        return ""

    else:
        return f"Unknown action: {action}"