import sqlite3
from pathlib import Path
import pandas as pd
from logger_setup import setup_logger

logger = setup_logger("storage")

class ThreatStorage:
    def __init__(self, db_name: str = "threats.db"):
        self.db_path = Path(__file__).parent / db_name
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Skapar databstabellen om den inte redan finns."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE,
                    content TEXT,
                    link TEXT,
                    source TEXT,
                    published TEXT,
                    hotniva TEXT DEFAULT 'Ej analyserat',
                    category TEXT DEFAULT 'Övriga hot',
                    risk_score INTEGER DEFAULT 5,
                    summary TEXT DEFAULT '',
                    recommendation TEXT DEFAULT ''
                )
            """)
            conn.commit()

    def get_all_entries(self) -> pd.DataFrame:
        """Hämtar alla sparade poster som en Pandas DataFrame."""
        with self._get_connection() as conn:
            query = "SELECT * FROM threats"
            df = pd.read_sql(query, conn)
            return df

    def get_unique_sources(self) -> list:
        """Returnerar en lista med unika källor från databasen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source FROM threats WHERE source IS NOT NULL")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def update_analysis(
        self, 
        entry_id: int, 
        hotniva: str, 
        kategori: str, 
        risk_score: int, 
        sammanfattning: str, 
        rekommendation: str
    ):
        """Uppdaterar en specifik post med resultat från AI-analysen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE threats 
                SET hotniva = ?, category = ?, risk_score = ?, summary = ?, recommendation = ?
                WHERE id = ?
            """, (hotniva, kategori, risk_score, sammanfattning, rekommendation, entry_id))
            conn.commit()

    def insert_entry(self, title: str, content: str, link: str, source: str, published: str):
        """Sparar en nyhets- eller hotpost (duplicering förhindras av UNIQUE på titel)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO threats (title, content, link, source, published)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, content, link, source, published))
                conn.commit()
        except Exception as e:
            logger.error(f"Kunde inte spara post till databasen: {e}")