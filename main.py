import os
import threading
from dotenv import load_dotenv
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv, event as neonize_event

from database.models import DatabaseManager
from services.ai_service import AIService

# Charger les variables d'environnement (.env)
load_dotenv()

# Instanciation de nos modules professionnels
db = DatabaseManager()
ai = AIService()
client = NewClient("session_whatsapp.db")

message_buffers = {}
buffer_timers = {}
AGGR_TIMEOUT = 3.0  # Fenêtre d'agrégation temporelle (Debounce)

def process_aggregated_messages(chat_jid):
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    if user_key not in message_buffers: return
    
    full_user_input = " ".join(message_buffers[user_key])
    del message_buffers[user_key]
    if user_key in buffer_timers: del buffer_timers[user_key]
        
    print(f"🤖 Traitement des messages pour {user_key} : {full_user_input}")
    db.save_message(user_key, "user", full_user_input)
    
    history = db.get_context(user_key)
    try:
        ai_response = ai.generate_response(history)
        db.save_message(user_key, "assistant", ai_response)
        print(f"📤 [ENVOI WHATSAPP] -> {user_key}")
        client.send_message(chat_jid, ai_response)
    except Exception as e:
        print(f"❌ Erreur génération/envoi : {e}")

def handle_incoming_message(chat_jid, content, is_audio=False, audio_path=None):
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    if is_audio and audio_path:
        content = ai.transcribe(audio_path)
        if not content: return
            
    if user_key not in message_buffers: message_buffers[user_key] = []
    message_buffers[user_key].append(content)
    
    if user_key in buffer_timers: buffer_timers[user_key].cancel()
    timer = threading.Timer(AGGR_TIMEOUT, process_aggregated_messages, args=[chat_jid])
    buffer_timers[user_key] = timer
    timer.start()

@client.event(ConnectedEv)
def on_connected(client: NewClient, event: ConnectedEv):
    print("\n🎉 Votre Assistant Premium est en ligne sur WhatsApp !\n")

@client.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    if message.Info.MessageSource.IsFromMe: return
    chat_jid = message.Info.MessageSource.Chat
    user_key = f"{chat_jid.User}@{chat_jid.Server}"
    
    if "broadcast" in user_key or "g.us" in user_key: return

    # Réception de messages textuels
    if message.Message.conversation:
        handle_incoming_message(chat_jid, message.Message.conversation)
    elif message.Message.extendedTextMessage and message.Message.extendedTextMessage.text:
        handle_incoming_message(chat_jid, message.Message.extendedTextMessage.text)
    
    # Réception de messages vocaux
    elif message.Message.audioMessage:
        try:
            audio_data = client.download_any(message.Message.audioMessage)
            if audio_data:
                audio_path = f"vocal_{user_key.replace('@', '_').replace('.', '_')}.ogg"
                with open(audio_path, "wb") as f: f.write(audio_data)
                handle_incoming_message(chat_jid, content="", is_audio=True, audio_path=audio_path)
        except Exception:
            pass

if __name__ == "__main__":
    db.init_db()
    print("Démarrage du client WhatsApp...")
    client.connect()
    neonize_event.wait()
