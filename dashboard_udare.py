# dashboard_udare.py - Suport pentru multiple culturi
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import json
import os
import requests

# ========== CONFIGURAȚIE PAGINĂ ==========
st.set_page_config(
    page_title="🌱 Sistem AI pentru Legume",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCȚII GENERALE ==========
@st.cache_data(ttl=3600)
def incarca_culturi():
    """Încarcă fișierul culturi.csv și returnează un DataFrame."""
    try:
        df = pd.read_csv('culturi.csv')
        return df
    except FileNotFoundError:
        st.error("Fișierul `culturi.csv` nu a fost găsit. Creează-l în folderul aplicației.")
        return pd.DataFrame()

def get_parametri_cultura(nume_cultura, df_culturi):
    """Returnează un dicționar cu parametrii specifici culturii."""
    row = df_culturi[df_culturi['nume'] == nume_cultura].iloc[0]
    return {
        'suprafata': row['suprafata'],
        'necesar': {
            'Plantare': row['necesar_plantare'],
            'Vegetativ': row['necesar_vegetativ'],
            'Inflorire': row['necesar_inflorire'],
            'Maturare': row['necesar_maturare'],
            'Pre-recoltare': row['necesar_pre_recoltare']
        },
        'prag_udare_litri_mp': row['prag_udare_litri_mp']
    }

def get_weather_forecast():
    """Obține prognoza meteo folosind OpenWeatherMap API (necesită secret)."""
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
    except:
        return None
    city = "Bucharest"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ro"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('cod') != 200:
            return None
        return {
            'temperatura': data['main']['temp'],
            'umiditate': data['main']['humidity'],
            'descriere': data['weather'][0]['description'],
        }
    except:
        return None

def calculeaza_necesar(suprafata, necesar_pe_zi, zile_scurse):
    return suprafata * necesar_pe_zi * zile_scurse

def incarca_istoric():
    if os.path.exists("istoric_udari.json"):
        try:
            with open("istoric_udari.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def incarca_predictii_ai():
    if os.path.exists("predictii_ai.json"):
        try:
            with open("predictii_ai.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# ========== BARA LATERALĂ ==========
with st.sidebar:
    st.header("⚙️ Configurație")
    
    # Încarcă lista de culturi
    df_culturi = incarca_culturi()
    if df_culturi.empty:
        st.stop()
    
    nume_cultura = st.selectbox("🌿 Selectează cultura", df_culturi['nume'].tolist())
    params = get_parametri_cultura(nume_cultura, df_culturi)
    
    # Afișează parametrii specifici (doar pentru informare)
    with st.expander("📋 Parametrii culturii"):
        st.write(f"**Suprafață:** {params['suprafata']} mp")
        st.write(f"**Prag udare:** {params['prag_udare_litri_mp']} litri/mp")
        st.write("**Necesar zilnic (litri/mp/zi):**")
        for stadiu, val in params['necesar'].items():
            st.write(f"  - {stadiu}: {val}")
    
    st.markdown("---")
    
    # Suprafața poate fi ajustată manual (opțional)
    suprafata = st.number_input("Suprafață (mp)", value=float(params['suprafata']), step=10.0)
    
    debit_pompa = st.number_input("Debit pompă (l/h)", value=5640, step=100)
    
    st.markdown("---")
    
    stadiu_curent = st.selectbox(
        "Stadiul curent",
        ["Plantare", "Vegetativ", "Inflorire", "Maturare", "Pre-recoltare"],
        index=2
    )
    
    ultima_udare = st.date_input(
        "Ultima udare",
        value=datetime.date.today() - datetime.timedelta(days=3)
    )
    
    st.markdown("---")
    
    st.subheader("🌤️ Prognoză meteo")
    if st.button("🔍 Verifică vremea acum", use_container_width=True):
        with st.spinner("Se preia prognoza..."):
            weather = get_weather_forecast()
            if weather:
                st.success(f"**{weather['temperatura']:.1f}°C** | 💧 {weather['umiditate']}%")
                st.caption(f"{weather['descriere'].capitalize()}")
            else:
                st.error("Nu s-a putut obține prognoza. Verifică cheia API în Secrets.")
    
    st.markdown("---")
    st.subheader("📊 Filtre grafice")
    zile_istoric = st.slider("Perioadă istoric (zile)", 7, 90, 30)

# ========== CALCULE PRINCIPALE ==========
astazi = datetime.date.today()
zile_scurse = max(0, (astazi - ultima_udare).days)

necesar_pe_zi = params['necesar'][stadiu_curent]
necesar_total = calculeaza_necesar(suprafata, necesar_pe_zi, zile_scurse)
prag_udare_total = suprafata * params['prag_udare_litri_mp']
trebuie_udat = necesar_total >= prag_udare_total
timp_udare = int((necesar_total / debit_pompa) * 60) if trebuie_udat else 0
timp_sector = (timp_udare + 1) // 2

istoric = incarca_istoric()
predictii_ai = incarca_predictii_ai()

# ========== KPI ==========
st.subheader(f"📊 Starea curentă – {nume_cultura}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📅 Zile de la ultima udare", f"{zile_scurse} zile")
with col2:
    st.metric("💧 Necesar acumulat", f"{int(necesar_total):,} litri")
with col3:
    if trebuie_udat:
        st.metric("🚨 Recomandare", "UDĂ ACUM!", delta=f"{timp_udare} min")
    else:
        st.metric("🌱 Recomandare", "AȘTEAPTĂ")
with col4:
    st.metric("🌡️ Stadiu", stadiu_curent)

if trebuie_udat:
    st.info(f"💧 **Recomandare udare:** {timp_udare} minute total\n\n- Sector 1: {timp_sector} min\n- Sector 2: {timp_udare - timp_sector} min")

st.markdown("---")

# ========== GRAFICE (adaptate la cultura selectată) ==========
# Restul codului pentru grafice rămâne neschimbat, deoarece folosește datele din istoric.
# Dacă dorești să filtrezi istoricul după cultură, va trebui să adaugi o coloană 'cultura' în fișierele JSON.
# Momentan păstrăm varianta simplă.

st.subheader("📈 Evoluție necesar apă")
if istoric:
    df_istoric = pd.DataFrame(istoric)
    df_istoric['data'] = pd.to_datetime(df_istoric['data'])
    df_istoric = df_istoric.sort_values('data').tail(zile_istoric)
    fig = px.line(df_istoric, x='data', y='necesar_acumulat', title=f"Necesar apă - {nume_cultura}")
    st.plotly_chart(fig, use_container_width=True)

# ========== Și mai jos poți adăuga restul graficelor tale (celelalte figuri) ==========
# ... (păstrează codul tău anterior pentru celelalte grafice) ...

st.markdown("---")
st.caption(f"📅 Ultima actualizare: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🌱 Sistem AI pentru legume - Datele sunt locale momentan")