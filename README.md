Ett automatiserat system för hotanalys (Threat Intelligence) byggt med Python, Streamlit och Google Gemini AI. Systemet samlar in aktuella cybersäkerhetshot och sårbarheter från publika källor, lagrar dem lokalt och använder AI för att klassificera hotnivå, bedöma riskpoäng samt ta fram konkreta säkerhetsrekommendationer i en interaktiv dashboard.

**✨ Funktioner**

**Automatiserad datainsamling:**
Hämtar och parsa hotdata och säkerhetsnyheter från RSS-flöden (t.ex. The Hacker News och     BleepingComputer) samt sårbarhetsdatabaser.

**AI-driven hotanalys (Google Gemini):**
Analyserar rubriker och artikelinnehåll för att automatiskt generera:
  -Riskpoäng (1–10) och hotnivå
  -Kategorisering (Ransomware, Sårbarhet & CVE, Skadlig kod, Nätfiske & Social Engineering,     Övriga hot)
  -Koncis sammanfattning på svenska
  -Rekommenderade säkerhetsåtgärder

**Interaktiv Streamlit-dashboard:**
  -Översiktsmått för totalt antal hot, genomsnittlig riskpoäng och kritiska hot (Risk ≥ 8)
  -Filtrering på källa, datumintervall, hotkategori och fritextsökning i artiklar
  -Direktknapp för att synkronisera nya hot och köra batch-analys med AI

**IT-Forensik & Spårbarhet:**
Inbyggd loggvy i gränssnittet för att granska systemloggar från insamlings- och analysflödet.

**Lokal lagring:** 
Sparar insamlade poster och analysresultat i en lokal SQLite-databas (ThreatStorage) för snabb åtkomst och historik.

**🗂️ Projektstruktur**
├── dashboard.py        # Huvudapplikation och webbgränssnitt (Streamlit)
├── collector.py        # Modul för insamling av hotdata från RSS och API:er
├── analyzer.py         # AI-analysmotor kopplad till Google Gemini API
├── storage.py          # Databashantering (SQLite) för lagring och filtrering
├── requirements.txt    # Python-beroenden
├── .env                # Miljövariabler och API-nycklar (ignoreras av Git)
└── .gitignore          # Exkluderar känsliga filer, databas och loggar

**🚀 Installation & Kom igång**

1. Klona repositoryt
git clone https://github.com/awmoha/Automated-Threat-Analysis-with-Python-and-AI.git
cd Automated-Threat-Analysis-with-Python-and-AI

2. Skapa en virtuell miljö och installera beroenden
python -m venv .venv
# Aktivera på Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Aktivera på macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

(Om requirements.txt saknas kan du installera kärnpaketen manuellt: pip install streamlit pandas python-dotenv google-genai feedparser requests).

3. Konfigurera miljövariabler (.env)
Skapa en fil med namnet .env i projektets rotmapp och lägg till din Google Gemini API-nyckel:
env
GEMINI_API_KEY=din_gemini_api_nyckel_här

4. Starta applikationen
streamlit run dashboard.py
Öppna webbläsaren på adressen som visas i terminalen (vanligtvis http://localhost:8501).

**🖥️ Användning**

Hämta hotdata: 
  -Klicka på "🔄 Synkronisera / Hämta nya hot" i sidofältet för att hämta de senaste artiklarna och spara dem i databasen.
  -Filtrera: Använd kontrollpanelen till vänster för att filtrera på specifik källa, datumintervall, kategori eller nyckelord och klicka på "🔍 Kör         filtrering".
  -Analysera med AI: Välj hur många artiklar du vill analysera med reglaget och klicka på "Kör AI-analys på filtrerade poster". Resultaten sparas direkt i  databasen och uppdaterar riskpoäng samt rekommendationer.
  -Granska loggar: Byt vy i sidofältet till "IT-Forensik & Loggar" för att inspektera körningsloggar och felsöka eventuella avvikelser.

🔒 **Säkerhet & Sekretess**
API-nycklar lagras uteslutande i .env och laddas via python-dotenv.
.gitignore är konfigurerad för att förhindra att .env, lokala SQLite-databaser (*.db, *.sqlite) och systemloggar (*.log, logs/) laddas upp till versionshanteringen.

