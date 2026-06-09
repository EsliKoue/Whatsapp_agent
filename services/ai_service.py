import os
import json
from groq import Groq
from services.tools_service import TOOLS_DEFINITION, AVAILABLE_TOOLS

class AIService:
    def __init__(self):
        self.client = Groq(api_key="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")
        self.text_model = "llama-3.3-70b-versatile"
        self.audio_model = "whisper-large-v3-turbo"
        self.system_prompt = {
            "role": "system", 
            "content": (
                "Tu es un assistant personnel d'élite, dévoué, chaleureux et hautement professionnel. "
                "Tu te comportes comme un secrétaire privé humain et attentionné au bureau. "
                "Interdiction absolue de mentionner que tu es une 'IA' ou un 'robot'. "
                "Réponds toujours de façon naturelle et fluide. Tu as accès à des outils, utilise-les si nécessaire."
            )
        }

    def generate_response(self, history: list) -> str:
        messages = [self.system_prompt] + history
        
        # Premier appel pour détecter si un outil est nécessaire
        response = self.client.chat.completions.create(
            model=self.text_model,
            messages=messages,
            tools=TOOLS_DEFINITION,
            tool_choice="auto",
            temperature=0.5
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Exécution de la fonction Python correspondante
                function_to_call = AVAILABLE_TOOLS[function_name]
                if function_name == "get_current_time":
                    tool_output = function_to_call()
                else:
                    tool_output = function_to_call(**function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output
                })
            
            # Second appel pour générer le texte final avec le résultat de l'outil
            second_response = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages
            )
            return second_response.choices[0].message.content
            
        return response_message.content

    def transcribe(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as audio_file:
                return self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.audio_model,
                    response_format="text"
                )
        except Exception as e:
            print(f"❌ Erreur transcription Whisper : {e}")
            return ""
