import os
import time
import threading
from dotenv import load_dotenv
from groq import Groq
import psycopg2
from psycopg2.extras import DictCursor
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv, event as neonize_event

# Charger les variables d'environnement (.env)
load_dotenv()

# Initialisation du client Groq
groq_client = Groq(api_key="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")
TEXT_MODEL = "llama-3.3-70b-versatile"
AUDIO_MODEL = "whisper-large-v3-turbo"

# Connexion persistante à PostgreSQL
DB_CONN = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=DictCursor)

# Mémoire tampon pour l'agrégation (Debounce)
message_buffers = {}
buffer_timers = {}
AGGR_TIMEOUT = 3.0  # Temps d'attente en secondes

# Initialisation du client WhatsApp Neonize
client = NewClient("session_whatsapp.db")

def init_db():
    """Initialise la table PostgreSQL."""
    with DB_CONN.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                role VARCHAR(10),
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        DB_CONN.commit()

def save_message(user_id_str, role, content):
    """Enregistre un message dans l'historique PostgreSQL en utilisant une chaîne de caractères."""
    with DB_CONN.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (%s, %s, %s);",
            (user_id_str, role, content)
        )
        DB_CONN.commit()

def get_chat_context(user_id_str, limit=10):
    """Récupère l'historique récent de l'utilisateur pour le contexte IA."""
    with DB_CONN.cursor() as cur:
        cur.execute(
            "SELECT role, content FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s;",
            (user_id_str, limit)
        )
        rows = cur.fetchall()
        messages = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        return messages

def transcribe_audio(file_path):
    """Transcrit un message vocal reçu avec Groq Whisper-turbo."""
    try:
        print(f"🎙️ Envoi du fichier audio à Groq Whisper ({file_path})...")
        with open(file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model=AUDIO_MODEL,
                response_format="text"
            )
            print(f"📄 Transcription réussie : {transcription}")
            return transcription
    except Exception as e:
        print(f"❌ Erreur lors de la transcription Whisper : {e}")
        return ""

def process_aggregated_messages(chat_jid):
    """Regroupe les messages accumulés, interroge Groq et répond directement au JID natif."""
    # Clé textuelle unique pour le dictionnaire de buffer
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    
    if user_key not in message_buffers:
        return
    
    full_user_input = " ".join(message_buffers[user_key])
    del message_buffers[user_key]
    if user_key in buffer_timers:
        del buffer_timers[user_key]
        
    print(f"🤖 Traitement des messages agrégés pour {user_key} : {full_user_input}")
    
    # 1. Sauvegarde dans PostgreSQL via la clé texte
    save_message(user_key, "user", full_user_input)
    
    # 2. Construction du prompt système et chargement de la mémoire
    system_prompt = {
        "role": "system", 
        "content": "Tu es un agent IA de niveau production sur WhatsApp. Tu es multilingue, amical et concis. Réponds toujours de façon naturelle dans la langue de l'utilisateur."
    }
    history = get_chat_context(user_key)
    messages = [system_prompt] + history
    
    try:
        # 3. Génération de la réponse avec Llama 3.3
        completion = groq_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=messages,
            temperature=0.5
        )
        ai_response = completion.choices[0].message.content
        
        # 4. Sauvegarde de la réponse IA
        save_message(user_key, "assistant", ai_response)
        
        # 5. Envoi réel sur WhatsApp en passant l'objet JID d'origine intact
        print(f"📤 [ENVOI RÉEL WHATSAPP] -> {user_key} : {ai_response}")
        client.send_message(chat_jid, ai_response)
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération ou de l'envoi : {e}")

def handle_incoming_message(chat_jid, content, is_audio=False, audio_path=None):
    """Gère l'algorithme d'agrégation temporelle (Debounce) avec l'objet JID."""
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    
    if is_audio and audio_path:
        content = transcribe_audio(audio_path)
        if not content:
            return
            
    if user_key not in message_buffers:
        message_buffers[user_key] = []
        
    message_buffers[user_key].append(content)
    
    if user_key in buffer_timers:
        buffer_timers[user_key].cancel()
        
    # On passe l'objet chat_jid complet au thread pour qu'il soit utilisé à l'envoi
    timer = threading.Timer(AGGR_TIMEOUT, process_aggregated_messages, args=[chat_jid])
    buffer_timers[user_key] = timer
    timer.start()

@client.event(ConnectedEv)
def on_connected(client: NewClient, event: ConnectedEv):
    print("\n🎉 Agent IA connecté avec succès à WhatsApp ! Écoute en cours...\n")

@client.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    # Ignorer si le message vient de notre propre compte
    if message.Info.MessageSource.IsFromMe:
        return
        
    chat_jid = message.Info.MessageSource.Chat
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    
    if "broadcast" in user_key or "g.us" in user_key:
        return

    text_content = ""
    
    # Détection et extraction des messages textuels
    if message.Message.conversation:
        text_content = message.Message.conversation
    elif message.Message.extendedTextMessage and message.Message.extendedTextMessage.text:
        text_content = message.Message.extendedTextMessage.text

    if text_content:
        print(f"📩 Texte reçu de {user_key}: {text_content}")
        handle_incoming_message(chat_jid, content=text_content, is_audio=False)

    # CORRECTION : Détection propre sans appeler l'attribut '.url' qui n'existe pas
    elif message.Message.audioMessage:
        print(f"🎙️ Message vocal reçu de {user_key}. Téléchargement...")
        try:
            audio_data = client.download_any(message.Message.audioMessage)
            if audio_data:
                clean_id = user_key.replace("@", "_").replace(".", "_")
                audio_path = f"vocal_{clean_id}.ogg"
                
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                    
                handle_incoming_message(chat_jid, content="", is_audio=True, audio_path=audio_path)
            else:
                print("⚠️ Impossible de récupérer les données du fichier vocal.")
        except Exception as audio_err:
            print(f"⚠️ Impossible de télécharger l'audio : {audio_err}")

if __name__ == "__main__":
    init_db()
    print("Démarrage du client WhatsApp...")
    client.connect()
    neonize_event.wait()
