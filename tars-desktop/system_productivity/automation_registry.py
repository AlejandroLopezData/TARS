import sys
import os
import configparser
import shutil
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system_core/database")))
APPLICATIONS_DIR = "/usr/share/applications"
import db_manager

try:
    from system_context import get_windows
except ImportError:
    def get_windows():
        return [
            {"titulo": "Google Chrome", "clase": "google-chrome", "workspace": 2},
            {"titulo": "Steam Launcher", "clase": "steam", "workspace": 5}
        ]

def add_app(name: str, command: str, workspace: str = None, aliases: list = None, url: str = None, url_base: str = None) -> str:
    name = name.strip().lower()
    command = command.split()[0]
    aliases = aliases or []
    final_workspace = workspace if workspace is not None else "current"

    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO apps (name, command, url, url_base, default_workspace)
            VALUES (?, ?, ?, ?, ?)
        """, (name, command, url, url_base, final_workspace))
        
        app_id = cursor.lastrowid

        if name not in aliases:
            aliases.append(name)

        for alias in aliases:
            alias = alias.strip().lower()
            cursor.execute("""
                INSERT OR IGNORE INTO app_aliases (app_id, alias)
                VALUES (?, ?)
            """, (app_id, alias))
        
        conn.commit()
        return f"App '{name}' added successfully to workspace '{final_workspace}'."
    except Exception as e:
        conn.rollback()
        return f"Error adding app: {e}"
    finally:
        conn.close()

def delete_app(name_or_alias: str) -> str:
    name_or_alias = name_or_alias.strip().lower()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name FROM apps WHERE name = ?
            UNION
            SELECT app_id, (SELECT name FROM apps WHERE id = app_aliases.app_id) 
            FROM app_aliases WHERE alias = ?
        """, (name_or_alias, name_or_alias))
        
        result = cursor.fetchone()
        if not result:
            return f"App or alias '{name_or_alias}' not found."
        
        app_id, app_name = result
        
        cursor.execute("DELETE FROM apps WHERE id = ?", (app_id,))
        conn.commit()
        
        return f"App '{app_name}' completely removed."
    except Exception as e:
        conn.rollback()
        return f"Error deleting app: {e}"
    finally:
        conn.close()

def add_environment(name: str) -> str:
    name = name.strip().lower()
    windows = get_windows()
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name FROM apps")
        apps = cursor.fetchall()
        
        apps_data = []
        for app_id, app_name in apps:
            cursor.execute("SELECT alias FROM app_aliases WHERE app_id = ?", (app_id,))
            aliases = [row[0] for row in cursor.fetchall()]
            apps_data.append({"id": app_id, "name": app_name, "aliases": aliases})
        
        captured = []
        for w in windows:
            title_lower = w["titulo"].lower()
            class_lower = w["clase"].lower()
            
            best_id = None
            best_len = 0
            is_title_match = False
            
            for app in apps_data:
                terms = [app["name"]] + app["aliases"]
                for t in terms:
                    t = t.lower()
                    if t in title_lower and len(t) > best_len:
                        best_len = len(t)
                        best_id = app["id"]
                        is_title_match = True
                    elif not is_title_match and t in class_lower and len(t) > best_len:
                        best_len = len(t)
                        best_id = app["id"]
            
            if best_id and not any(c["id"] == best_id for c in captured):
                captured.append({"id": best_id, "workspace": w["workspace"]})
        
        if not captured:
            return "No recognized open applications found to save into the environment."
            
        cursor.execute("INSERT OR IGNORE INTO environments (name) VALUES (?)", (name,))
        cursor.execute("SELECT id FROM environments WHERE name = ?", (name,))
        env_id = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM environment_apps WHERE environment_id = ?", (env_id,))
        
        for c in captured:
            cursor.execute("""
                INSERT INTO environment_apps (environment_id, app_id, workspace)
                VALUES (?, ?, ?)
            """, (env_id, c["id"], str(c["workspace"])))
            
        conn.commit()
        return f"Environment '{name}' successfully saved with {len(captured)} apps."
    except Exception as e:
        conn.rollback()
        return f"Error saving environment: {e}"
    finally:
        conn.close()

def delete_environment(name: str) -> str:
    name = name.strip().lower()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM environments WHERE name = ?", (name,))
        result = cursor.fetchone()
        if not result:
            return f"Environment '{name}' not found."
            
        env_id = result[0]
        cursor.execute("DELETE FROM environments WHERE id = ?", (env_id,))
        conn.commit()
        
        return f"Environment '{name}' completely removed."
    except Exception as e:
        conn.rollback()
        return f"Error deleting environment: {e}"
    finally:
        conn.close()


def _list_installed_apps() -> list[dict]:
    apps = []
    if not os.path.isdir(APPLICATIONS_DIR):
        return apps

    for file in os.listdir(APPLICATIONS_DIR):
        if not file.endswith(".desktop"):
            continue
        path = os.path.join(APPLICATIONS_DIR, file)

        try:
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            parser.read(path, encoding="utf-8")

            if "Desktop Entry" not in parser:
                continue
            entry = parser["Desktop Entry"]
            if entry.get("NoDisplay", "false").lower() == "true":
                continue

            name = entry.get("Name", "")
            exec_raw = entry.get("Exec", "")

            if not name or not exec_raw:
                continue
            command = os.path.basename(exec_raw.split()[0])
            apps.append({
                "name": name,
                "command": command
            })
        except Exception:
            continue
    return apps

def list_configured_apps_tars() -> list[dict]:
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT a.name, al.alias
            FROM apps a
            LEFT JOIN app_aliases al ON a.id = al.app_id
            WHERE a.name != 'searches'
        """)
        rows = cursor.fetchall()
        
        apps_data = {}
        for app_name, alias in rows:
            if app_name not in apps_data:
                apps_data[app_name] = []
            if alias and alias != app_name:
                apps_data[app_name].append(alias)
                
        return [{"name": name, "aliases": aliases} for name, aliases in apps_data.items()]
    except Exception:
        return []
    finally:
        conn.close()

def list_environments() -> list[dict]:
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.name, a.name, ea.workspace
            FROM environments e
            LEFT JOIN environment_apps ea ON e.id = ea.environment_id
            LEFT JOIN apps a ON ea.app_id = a.id
        """)
        rows = cursor.fetchall()

        envs_data = {}
        for env_name, app_name, workspace in rows:
            if env_name not in envs_data:
                envs_data[env_name] = []
            if app_name:
                envs_data[env_name].append({"name": app_name, "workspace": workspace})

        return [{"name": name, "apps": apps} for name, apps in envs_data.items()]
    except Exception:
        return []
    finally:
        conn.close()


def _is_command_valid(command: str, is_website: bool = False) -> bool:
    if not command:
        return False
        
    binary = command.split()[0]
    
    if binary.startswith("/") or binary.startswith("./"):
        return os.path.isfile(binary) and os.path.access(binary, os.X_OK)
        
    return shutil.which(binary) is not None



def validate_and_correct_payload(system_prompt: str, app_raw_name: str, app_raw_cmd: str, llm_result: dict, retries=1) -> dict:
    for attempt in range(retries + 1):
        params = llm_result.get("params", {})
        aliases = params.get("aliases", [])
        command = params.get("command")
        is_web = params.get("url") is not None
        
        errors = []
        if llm_result.get("action") != "add_app":
            errors.append("Action must be 'add_app'")
        if not isinstance(aliases, list) or len(aliases) != 5:
            errors.append(f"The 'aliases' array must have EXACTLY 5 elements")
        if params.get("name") and params.get("name") != params.get("name").lower():
            errors.append("The 'name' parameter must be strictly lowercased")
            
        # 🔍 NUEVA VERIFICACIÓN: Comprobamos si el comando es real en tu Linux
        if command and not _is_command_valid(command, is_web):
            errors.append(f"The command '{command}' does not exist or is not executable on this system")

        if not errors:
            return llm_result

        # Si hay errores, le pasamos el feedback exacto al modelo para que lo arregle
        if attempt < retries:
            error_feedback = f"Validation failed: {', '.join(errors)}. Please fix the 'command' or parameters and generate a valid JSON."
            history = [
                {"role": "user", "content": f"añade la app '{app_raw_name}'"},
                {"role": "assistant", "content": str(llm_result)}
            ]
            llm_result = ask_llm(system_prompt, error_feedback, history=history)
    
    # Si después de los reintentos sigue fallando el comando, devolvemos un fallback seguro
    # o marcamos el comando original del sistema operativo como el válido por defecto
    return None