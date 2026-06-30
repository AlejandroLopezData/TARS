import sys
import os
import json

# Añadimos las carpetas del core al path para la importación
sys.path.append(os.path.abspath("system_core/brain"))
sys.path.append(os.path.abspath("system_core/prompts"))

from llm import ask_llm
from prompt import build_system_prompt  

# =====================================================================
# ENTORNO DE PRUEBA ACTUALIZADO
# =====================================================================
MOCK_AGENTS = {
    "coder": {
        "description": "Expert in writing, refactoring, and debugging Python/Bash code."
    },
    "web_researcher": {
        "description": "Specialized in scraping websites, searching the web, and summarizing online articles."
    }
}

TEST_CASES = [
    # Caso 1: Forzar inferencia de comando (Debería deducir 'gimp' o 'gimp-2.10' y meter 5 aliases)
    "agrega el programa gimp porfa",
    
    # Caso 2: Otra inferencia sin comando explícito (Debería deducir 'code' o 'vlc')
    "añade vlc",
    
    # Caso 3: Sincronización con la nueva descripción
    "haz un sync de las apps del sistema",
    
    # Caso 4: Delegación
    "necesito optimizar un bucle for en python que tarda mucho"
]

def run_tests():
    print("🤖 Generando System Prompt dinámico con descripciones y reglas de aliases...")
    system_prompt = build_system_prompt(MOCK_AGENTS)
    
    print(f"\n🚀 Iniciando nueva batería de pruebas con qwen3.5:4b...")
    print("-" * 60)

    for i, user_input in enumerate(TEST_CASES, 1):
        print(f"\n📝 TEST {i}: \"{user_input}\"")
        
        result = ask_llm(system_prompt, user_input)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("-" * 60)

if __name__ == "__main__":
    run_tests()