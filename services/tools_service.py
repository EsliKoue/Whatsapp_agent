import datetime

def get_current_time():
    """Donne l'heure et la date actuelle au format texte."""
    maintenant = datetime.datetime.now()
    return maintenant.strftime("Nous sommes le %A %d %B %Y et il est %H:%M.")

def create_reminder(task_name: str, time_str: str):
    """Simule la programmation d'un rappel pour l'utilisateur."""
    print(f"📌 [OUTIL] Rappel programmé : '{task_name}' à {time_str}")
    return f"C'est noté avec plaisir ! J'ai planifié votre rappel pour '{task_name}' à {time_str}."

# Dictionnaire de correspondance pour l'exécution dynamique
AVAILABLE_TOOLS = {
    "get_current_time": get_current_time,
    "create_reminder": create_reminder
}

# Déclarations JSON pour l'API Groq
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "À utiliser dès que l'utilisateur demande l'heure, la date ou le jour actuel.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "À utiliser pour programmer un rappel, une tâche ou un rendez-vous spécifique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {"type": "string", "description": "Le titre ou la description de la tâche."},
                    "time_str": {"type": "string", "description": "L'heure ou le moment (ex: 15h30, demain matin)."}
                },
                "required": ["task_name", "time_str"]
            }
        }
    }
]
