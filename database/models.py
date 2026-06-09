import os
import psycopg2
from psycopg2.extras import DictCursor

class DatabaseManager:
    def __init__(self):
        # Connexion à PostgreSQL via l'URL de votre fichier .env
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=DictCursor)

    def init_db(self):
        """Crée la table d'historique si elle n'existe pas."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    role VARCHAR(10),
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

    def save_message(self, user_id: str, role: str, content: str):
        """Enregistre un message (user ou assistant) dans la base."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (%s, %s, %s);",
                (user_id, role, content)
            )
            self.conn.commit()

    def get_context(self, user_id: str, limit=10) -> list:
        """Récupère les derniers messages pour donner de la mémoire au LLM."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT role, content FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s;",
                (user_id, limit)
            )
            rows = cur.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
