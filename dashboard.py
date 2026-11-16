from datetime import datetime, date
import os
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Läs in miljövariabler från .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Hämta Gemini API-nyckel
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Importera egna moduler
try:
    from analyzer import ThreatAnalyzer
    from collector import ThreatCollector
    from storage import ThreatStorage
except ImportError as e:
    st.error(f"Kunde inte importera moduler: {e}")

# Sidkonfiguration
st.set_page_config(
    page_title="Hotanalys Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Initiera lagring
storage = ThreatStorage()

# --- Sidofält (Sidebar) ---
st.sidebar.title("Vyer & Kontrollpanel")

# Knapp för att synkronisera / hämta nya hot direkt i gränssnittet
if st.sidebar.button("🔄 Synkronisera / Hämta nya hot", type="primary"):
    with st.spinner("Hämtar färska hot från RSS, CISA och NIST..."):
        try:
            feeds = {
                "The Hacker News": "https://thehackernews.com/feeds/posts/default",
                "BleepingComputer": "https://www.bleepingcomputer.com/feed/"
            }
            collector = ThreatCollector(rss_feeds=feeds)
            entries = collector.fetch_all()
            
            for entry in entries:
                storage.insert_entry(
                    title=entry["title"],
                    content=entry["summary"],
                    link=entry["link"],
                    source=entry["source_name"],
                    published=entry["published"]
                )
            st.sidebar.success(f"Synk klar! Hämtade {len(entries)} poster.")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Kunde inte synkronisera: {e}")

st.sidebar.markdown("---")
view = st.sidebar.radio(
    "Välj vy",
    [
        "Dashboard & Hotanalys",
        "Laboration & Experiment (1-4)",
        "IT-Forensik & Loggar",
    ],
)

# --- Filtrering (endast för Dashboard-vyn) ---
if view == "Dashboard & Hotanalys":
    st.sidebar.markdown("---")
    sources = ["Alla källor"] + storage.get_unique_sources()
    min_date = date(2016, 11, 10)
    max_date = date.today()

    categories = [
        "Choose options",
        "Ransomware",
        "Sårbarhet & CVE",
        "Skadlig kod",
        "Nätfiske & Social Engineering",
        "Övriga hot",
    ]

    # Initiera session state för filter
    if "filtered_source" not in st.session_state:
        st.session_state.filtered_source = "Alla källor"
        st.session_state.num_to_analyze = 50
        st.session_state.from_date = min_date
        st.session_state.to_date = max_date
        st.session_state.selected_category = "Choose options"
        st.session_state.search_keyword = ""

    with st.sidebar.form("filter_form"):
        st.subheader("Filtrering")
        
        selected_source = st.selectbox(
            "Källa", 
            sources, 
            index=sources.index(st.session_state.filtered_source) if st.session_state.filtered_source in sources else 0
        )
        num_to_analyze = st.slider("Antal artiklar att analysera med AI", 5, 50, st.session_state.num_to_analyze)
        from_date = st.date_input("Från datum", st.session_state.from_date)
        to_date = st.date_input("Till datum", st.session_state.to_date)
        selected_category = st.selectbox(
            "Kategori", 
            categories, 
            index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0
        )
        search_keyword = st.text_input("Sök nyckelord i hela artikeln", value=st.session_state.search_keyword, placeholder="t.ex. barracuda, phishing, cve...")
        
        submit_filters = st.form_submit_button("🔍 Kör filtrering", type="primary")
        
        if submit_filters:
            st.session_state.filtered_source = selected_source
            st.session_state.num_to_analyze = num_to_analyze
            st.session_state.from_date = from_date
            st.session_state.to_date = to_date
            st.session_state.selected_category = selected_category
            st.session_state.search_keyword = search_keyword
            st.rerun()

# --- Huvudvy ---
if view == "Dashboard & Hotanalys":
    st.title("🛡️ Automatiserad Hotanalys (Threat Intelligence) med Python & AI")
    st.markdown(
        "Visar alla insamlade artiklar, datumfilter och AI-kategorisering från flera källor."
    )

    if not API_KEY:
        st.error(
            "⚠️ GEMINI_API_KEY saknas i .env-filen! AI-analysen kommer inte att fungera."
        )

    df = storage.get_all_entries()

    if df.empty:
        st.warning(
            "Inga hot hittades i databasen. Klicka på 'Synkronisera / Hämta nya hot' i sidofältet!"
        )
    else:
        filtered_df = df.copy()

        # 1. Filtrera på Källa
        if st.session_state.filtered_source != "Alla källor":
            filtered_df = filtered_df[
                filtered_df["source"] == st.session_state.filtered_source
            ]

        # 2. Filtrera på Sökord
        if st.session_state.search_keyword:
            kw = st.session_state.search_keyword
            filtered_df = filtered_df[
                filtered_df["title"].str.contains(kw, case=False, na=False)
                | filtered_df["summary"].str.contains(kw, case=False, na=False)
            ]

        # 3. Filtrera på Kategori
        if st.session_state.selected_category != "Choose options":
            cat_col = "category" if "category" in filtered_df.columns else ("kategori" if "kategori" in filtered_df.columns else None)
            if cat_col:
                filtered_df = filtered_df[
                    filtered_df[cat_col] == st.session_state.selected_category
                ]

        # 4. Filtrera på Datumintervall (med utc=True för att undvika tidszonkrasch)
        if "published" in filtered_df.columns:
            filtered_df["pub_date"] = pd.to_datetime(filtered_df["published"], errors="coerce", utc=True).dt.date
            from_dt = st.session_state.from_date
            to_dt = st.session_state.to_date
            filtered_df = filtered_df[
                (filtered_df["pub_date"] >= from_dt) & (filtered_df["pub_date"] <= to_dt)
            ]

        total_posts = len(filtered_df)
        avg_risk = (
            filtered_df["risk_score"].mean()
            if "risk_score" in filtered_df.columns and not filtered_df.empty
            else 0.0
        )
        critical_posts = (
            len(filtered_df[filtered_df["risk_score"] >= 8])
            if "risk_score" in filtered_df.columns and not filtered_df.empty
            else 0
        )

        st.markdown(f"### 📊 Sammanställning ({total_posts} hot hittade)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totalt antal poster", total_posts)
        with col2:
            st.metric("Genomsnittlig riskpoäng", f"{avg_risk:.1f}/10")
        with col3:
            st.metric("Kritiska hot (Risk ≥ 8)", critical_posts)

        st.markdown("---")

        if st.button("Kör AI-analys på filtrerade poster", type="primary"):
            if not API_KEY:
                st.error(
                    "Kan inte köra analys utan en giltig GEMINI_API_KEY i .env!"
                )
            else:
                analyzer = ThreatAnalyzer(api_key=API_KEY)
                progress_bar = st.progress(0)
                status_text = st.empty()

                posts_to_process = filtered_df.head(st.session_state.num_to_analyze)
                total = len(posts_to_process)

                for idx, row in enumerate(posts_to_process.itertuples()):
                    status_text.text(
                        f"Analyserar ({idx+1}/{total}): {row.title[:50]}..."
                    )
                    analysis = analyzer.analyze(row.title, row.content)

                    storage.update_analysis(
                        row.id,
                        hotniva=analysis.get("hotniva", "Hög"),
                        kategori=analysis.get("kategori", "Övriga hot"),
                        risk_score=analysis.get("risk_score", 5),
                        sammanfattning=analysis.get("sammanfattning", ""),
                        rekommendation=analysis.get("rekommendation", "")
                    )
                    progress_bar.progress((idx + 1) / total)

                status_text.text("AI-analys klar!")
                st.success("Alla poster har analyserats klart av Gemini!")
                st.rerun()

        # Visar ALLA filtrerade poster utan .head()-begränsning
        st.markdown(f"### Aktuella Hot ({total_posts} st)")
        for row in filtered_df.itertuples():
            risk = getattr(row, "risk_score", 5)
            icon = "🔴" if risk >= 8 else ("🟡" if risk >= 5 else "🟢")

            with st.expander(
                f"{icon} [{risk}/10] {row.title} ({row.source})"
            ):
                st.markdown(f"**Kategori:** {getattr(row, 'category', getattr(row, 'kategori', 'Ej klassificerad'))}")
                st.markdown(f"**Sammanfattning:** {getattr(row, 'summary', row.content[:200])}")
                st.markdown(f"**Rekommendation:** {getattr(row, 'recommendation', 'Ingen åtgärd angiven.')}")
                st.markdown(f"[Läs originalartikel]({row.link})")

elif view == "Laboration & Experiment (1-4)":
    st.title("🧪 Laboration & Experiment")
    st.info("Här kan du bygga ut med egna laborationer och tester för cybersäkerhet.")

elif view == "IT-Forensik & Loggar":
    st.title("🔍 IT-Forensik & Loggar")
    st.markdown("Här visas systemloggar och spårbarhet från insamlings- och AI-pipelinen.")

    # Sök efter loggar i både 'logs/'-mappen och i rotmappen
    logs_dir = Path(__file__).parent / "logs"
    log_files = []
    
    if logs_dir.exists():
        log_files.extend(list(logs_dir.glob("*.log")))
    log_files.extend(list(Path(__file__).parent.glob("*.log")))

    if log_files:
        log_files = list(set(log_files))
        log_names = [f.name for f in log_files]
        selected_log_name = st.selectbox("Välj loggfil", log_names)
        
        target_path = next(f for f in log_files if f.name == selected_log_name)

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🔄 Uppdatera loggar"):
                st.rerun()

        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                log_lines = f.readlines()

            recent_logs = "".join(log_lines[-200:]) if log_lines else "Loggfilen är tom."
            st.text_area(
                f"Systemlogg ({selected_log_name} - senaste 200 raderna)",
                recent_logs,
                height=500,
            )
        except Exception as e:
            st.error(f"Kunde inte läsa loggfilen: {e}")
    else:
        st.warning(
            "Inga `.log`-filer hittades i projektet eller `logs/`-mappen."
        )