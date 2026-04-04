# dashboard_udare.py - Sistem AI pentru legume, arbori și arbuști
# Versiune cu fundal imagine fixat, fără avertismente de depreciere

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
    page_title="🌱 AgroAI - Sistem inteligent pentru plante",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS PERSONALIZAT CU FUNDAL IMAGINE (corectat) ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap');
    
    /* Fundal general cu imagine - selectori corectați pentru Streamlit */
    [data-testid="stAppViewContainer"] {
        background-image: url('https://images.pexels.com/photos/164504/field-grass-nature-plant-164504.jpeg?auto=compress&cs=tinysrgb&w=1920&h=1080&dpr=2');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    
    /* Overlay semi-transparent pentru lizibilitate */
    [data-testid="stAppViewContainer"] > .main {
        background-color: rgba(255, 255, 255, 0.85);
    }
    
    /* Asigură că și sidebar-ul are fundal semi-transparent */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(249,250,251,0.95) 100%);
        backdrop-filter: blur(4px);
        border-right: 1px solid #e5e7eb;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: transparent;
    }
    
    .card {
        background: linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(250,253,250,0.95) 100%);
        border-radius: 1.5rem;
        padding: 1.25rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.03), 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        margin-bottom: 1rem;
        backdrop-filter: blur(2px);
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 30px -12px rgba(16, 185, 129, 0.25);
        border-color: rgba(16, 185, 129, 0.5);
    }
    
    .metric-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(249,255,249,0.95) 100%);
        border-radius: 1.5rem;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border-bottom: 4px solid #10b981;
        transition: all 0.2s;
        backdrop-filter: blur(2px);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-bottom-width: 5px;
        border-bottom-color: #059669;
    }
    .metric-number {
        font-size: 2.2rem;
        font-weight: 800;
        color: #047857;
        margin: 0;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.5rem;
    }
    
    .warning-card {
        background: linear-gradient(145deg, #fffbeb, #fef3c7);
        border-left: 5px solid #f59e0b;
        border-radius: 1rem;
        padding: 1rem;
    }
    .danger-card {
        background: linear-gradient(145deg, #fef2f2, #fee2e2);
        border-left: 5px solid #ef4444;
        border-radius: 1rem;
        padding: 1rem;
    }
    .info-card {
        background: linear-gradient(145deg, #eff6ff, #dbeafe);
        border-left: 5px solid #3b82f6;
        border-radius: 1rem;
        padding: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(95deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 2rem;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 16px -6px #10b98180;
        background: linear-gradient(95deg, #059669 0%, #047857 100%);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #047857 0%, #10b981 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #064e3b;
        border-left: 5px solid #10b981;
        padding-left: 1rem;
        margin: 1.8rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    hr {
        margin: 1.2rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #10b981, #10b981, #10b981, transparent);
    }
    
    .dataframe {
        border-radius: 1rem;
        overflow: hidden;
        font-size: 0.85rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .dataframe th {
        background-color: #ecfdf5 !important;
        color: #064e3b;
        font-weight: 700;
    }
    .dataframe tr:hover {
        background-color: #f0fdf4 !important;
    }
    
    .streamlit-expanderHeader {
        font-weight: 600;
        background-color: #ecfdf5;
        border-radius: 0.75rem;
        color: #065f46;
    }
    .streamlit-expanderHeader:hover {
        background-color: #d1fae5;
    }
    
    .weather-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 1rem;
        padding: 0.8rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .stForm {
        background-color: rgba(255,255,255,0.9);
        padding: 0.5rem;
        border-radius: 1rem;
        border: 1px solid #d1d5db;
    }
    
    .stSlider .stSlider > div {
        color: #10b981;
    }
    .stSlider .stSlider > div > div {
        background-color: #10b981;
    }
    
    .stNumberInput input {
        border-radius: 0.5rem;
        border-color: #d1d5db;
    }
    .stNumberInput input:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 2px #10b98120;
    }
    
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNCȚII GENERALE ==========
@st.cache_data(ttl=3600)
def incarca_culturi():
    try:
        df = pd.read_csv('culturi.csv')
        required = ['nume', 'tip_cultura', 'adancime_radacina_cm', 'coeficient_evaporare',
                    'temp_opt_min', 'temp_opt_max', 'necesar_plantare', 'necesar_vegetativ',
                    'necesar_inflorire', 'necesar_maturare', 'necesar_pre_recoltare']
        for col in required:
            if col not in df.columns:
                st.warning(f"Coloana '{col}' lipsește. Se adaugă implicit.")
                if col.startswith('necesar'):
                    df[col] = 5
                elif col == 'adancime_radacina_cm':
                    df[col] = 30
                elif col == 'coeficient_evaporare':
                    df[col] = 1.0
                elif col == 'temp_opt_min':
                    df[col] = 15
                elif col == 'temp_opt_max':
                    df[col] = 30
                else:
                    df[col] = 0
        if 'suprafata_mp' not in df.columns:
            df['suprafata_mp'] = 0
        if 'numar_bucati' not in df.columns:
            df['numar_bucati'] = 0
        if 'prag_udare_litri_mp' not in df.columns:
            df['prag_udare_litri_mp'] = 20
        if 'prag_udare_litri_buc' not in df.columns:
            df['prag_udare_litri_buc'] = 0
        tratamente_cols = [
            'tratament_fertilizare_interval_zile', 'tratament_fertilizare_doza',
            'tratament_fertilizare_produs', 'tratament_fungicid_interval_zile',
            'tratament_fungicid_produs', 'tratament_insecticid_interval_zile',
            'tratament_insecticid_produs'
        ]
        for col in tratamente_cols:
            if col not in df.columns:
                df[col] = None
        return df
    except FileNotFoundError:
        st.error("Fișierul `culturi.csv` nu a fost găsit. Creează-l în folderul aplicației.")
        return pd.DataFrame()

def get_parametri_cultura(nume_cultura, df_culturi):
    row = df_culturi[df_culturi['nume'] == nume_cultura].iloc[0]
    tip = row['tip_cultura']
    return {
        'tip': tip,
        'suprafata': float(row['suprafata_mp']) if tip == 'leguma' else 0,
        'numar_bucati': int(row['numar_bucati']) if tip != 'leguma' else 0,
        'adancime_radacina': float(row['adancime_radacina_cm']),
        'coeficient_evaporare': float(row['coeficient_evaporare']),
        'temp_opt_min': float(row['temp_opt_min']),
        'temp_opt_max': float(row['temp_opt_max']),
        'necesar': {
            'Plantare': float(row['necesar_plantare']),
            'Vegetativ': float(row['necesar_vegetativ']),
            'Inflorire': float(row['necesar_inflorire']),
            'Maturare': float(row['necesar_maturare']),
            'Pre-recoltare': float(row['necesar_pre_recoltare'])
        },
        'prag_udare_litri_mp': float(row['prag_udare_litri_mp']),
        'prag_udare_litri_buc': float(row['prag_udare_litri_buc']),
        'tratament_fertilizare_interval_zile': row['tratament_fertilizare_interval_zile'] if not pd.isna(row['tratament_fertilizare_interval_zile']) else None,
        'tratament_fertilizare_doza': float(row['tratament_fertilizare_doza']) if not pd.isna(row['tratament_fertilizare_doza']) else None,
        'tratament_fertilizare_produs': row['tratament_fertilizare_produs'] if not pd.isna(row['tratament_fertilizare_produs']) else None,
        'tratament_fungicid_interval_zile': row['tratament_fungicid_interval_zile'] if not pd.isna(row['tratament_fungicid_interval_zile']) else None,
        'tratament_fungicid_produs': row['tratament_fungicid_produs'] if not pd.isna(row['tratament_fungicid_produs']) else None,
        'tratament_insecticid_interval_zile': row['tratament_insecticid_interval_zile'] if not pd.isna(row['tratament_insecticid_interval_zile']) else None,
        'tratament_insecticid_produs': row['tratament_insecticid_produs'] if not pd.isna(row['tratament_insecticid_produs']) else None
    }

def get_weather_forecast():
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
            'icon': data['weather'][0]['icon']
        }
    except:
        return None

def ajusteaza_necesar(necesar_baza, temperatura, temp_opt_min, temp_opt_max, coeficient_evaporare):
    if temperatura is None:
        return necesar_baza * coeficient_evaporare
    if temperatura < temp_opt_min:
        factor_temp = 0.8
    elif temperatura > temp_opt_max:
        factor_temp = 1.3
    else:
        factor_temp = 1.0
    return necesar_baza * factor_temp * coeficient_evaporare

def calculeaza_necesar_total(params, necesar_pe_zi_ajustat, zile_scurse):
    if params['tip'] == 'leguma':
        return params['suprafata'] * necesar_pe_zi_ajustat * zile_scurse
    else:
        return params['numar_bucati'] * necesar_pe_zi_ajustat * zile_scurse

def prag_udare_total(params):
    if params['tip'] == 'leguma':
        return params['suprafata'] * params['prag_udare_litri_mp']
    else:
        return params['numar_bucati'] * params['prag_udare_litri_buc']

def incarca_istoric(cultura):
    nume_fisier = f"istoric_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def incarca_predictii_ai(cultura):
    nume_fisier = f"predictii_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def incarca_tratamente(cultura):
    nume_fisier = f"tratamente_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salveaza_tratament(cultura, tratament):
    tratamente = incarca_tratamente(cultura)
    tratamente.append(tratament)
    nume_fisier = f"tratamente_{cultura.lower().replace(' ', '_')}.json"
    with open(nume_fisier, "w", encoding='utf-8') as f:
        json.dump(tratamente, f, indent=2, ensure_ascii=False)

# ========== BARA LATERALĂ ==========
with st.sidebar:
    st.markdown("<div style='text-align: center; margin-bottom: 1rem;'>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995572.png", width=70)
    st.markdown("<h2 style='text-align: center; color: #15803d; font-weight: 700;'>🌱 AgroAI</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    df_culturi = incarca_culturi()
    if df_culturi.empty:
        st.stop()
    
    nume_cultura = st.selectbox("🌿 **Selectează planta**", df_culturi['nume'].tolist())
    params = get_parametri_cultura(nume_cultura, df_culturi)
    
    with st.expander("📋 **Parametrii plantei**"):
        if params['tip'] == 'leguma':
            st.write(f"**Tip:** Legumă")
            st.write(f"**Suprafață:** {params['suprafata']} mp")
        else:
            st.write(f"**Tip:** {'Arbore' if params['tip'] == 'arbore' else 'Arbust'}")
            st.write(f"**Număr bucăți:** {params['numar_bucati']}")
        st.write(f"**Adâncime rădăcină:** {params['adancime_radacina']} cm")
        st.write(f"**Coeficient evaporare:** {params['coeficient_evaporare']}")
        st.write(f"**Temperatură optimă:** {params['temp_opt_min']}°C – {params['temp_opt_max']}°C")
        if params['tip'] == 'leguma':
            st.write(f"**Prag udare:** {params['prag_udare_litri_mp']} litri/mp")
        else:
            st.write(f"**Prag udare:** {params['prag_udare_litri_buc']} litri/bucată")
        st.write("**Necesar zilnic (litri/unitate):**")
        for stadiu, val in params['necesar'].items():
            st.write(f"  - {stadiu}: {val}")
    
    st.markdown("---")
    if params['tip'] == 'leguma':
        suprafata = st.number_input("📏 **Suprafață (mp)**", value=float(params['suprafata']), step=10.0)
        numar_bucati = 0
    else:
        numar_bucati = st.number_input("🌳 **Număr bucăți**", value=int(params['numar_bucati']), step=1, min_value=1)
        suprafata = 0
    debit_pompa = st.number_input("💧 **Debit pompă (l/h)**", value=5640, step=100, min_value=1)
    st.markdown("---")
    stadiu_curent = st.selectbox(
        "🌱 **Stadiul curent**",
        ["Plantare", "Vegetativ", "Inflorire", "Maturare", "Pre-recoltare"],
        index=2
    )
    ultima_udare = st.date_input("📅 **Ultima udare**", value=datetime.date.today() - datetime.timedelta(days=3))
    st.markdown("---")
    
    st.subheader("🌤️ **Prognoză meteo**")
    if st.button("🔍 Verifică vremea acum", use_container_width=False):
        with st.spinner("Se preia prognoza..."):
            weather = get_weather_forecast()
            if weather:
                st.success(f"**{weather['temperatura']:.1f}°C** | 💧 {weather['umiditate']}%")
                st.caption(f"{weather['descriere'].capitalize()}")
                st.session_state.weather = weather
            else:
                st.error("Nu s-a putut obține prognoza. Verifică cheia API.")
                st.session_state.weather = None
    else:
        if 'weather' not in st.session_state:
            st.session_state.weather = None
        if st.session_state.weather:
            st.success(f"**{st.session_state.weather['temperatura']:.1f}°C** | 💧 {st.session_state.weather['umiditate']}%")
            st.caption(f"{st.session_state.weather['descriere'].capitalize()}")
        else:
            st.info("Apasă butonul pentru prognoză.")
    
    st.markdown("---")
    st.subheader("🧪 **Înregistrează tratament**")
    with st.form("form_tratament"):
        tip_tratament = st.selectbox("Tip tratament", ["Fertilizare", "Fungicid", "Insecticit", "Altul"])
        produs = st.text_input("Produs")
        doza = st.number_input("Doză (kg/unitate sau litri)", min_value=0.0, step=0.01, format="%.2f")
        observatii = st.text_area("Observații")
        submitted = st.form_submit_button("💾 **Salvează**")
        if submitted:
            tratament = {
                "data": datetime.date.today().isoformat(),
                "tip": tip_tratament,
                "produs": produs,
                "doza": doza,
                "observatii": observatii
            }
            salveaza_tratament(nume_cultura, tratament)
            st.success(f"Tratament înregistrat pentru {nume_cultura}")
    
    st.markdown("---")
    st.subheader("📊 **Filtre grafice**")
    zile_istoric = st.slider("Perioadă istoric (zile)", 7, 90, 30)

# ========== OBȚINE DATELE METEO ==========
weather = st.session_state.get('weather', None)
temperatura = weather['temperatura'] if weather else None

# ========== CALCULE PRINCIPALE ==========
astazi = datetime.date.today()
zile_scurse = max(0, (astazi - ultima_udare).days)
necesar_pe_zi_baza = params['necesar'][stadiu_curent]
necesar_pe_zi_ajustat = ajusteaza_necesar(
    necesar_pe_zi_baza,
    temperatura,
    params['temp_opt_min'],
    params['temp_opt_max'],
    params['coeficient_evaporare']
)
if params['tip'] == 'leguma':
    params['suprafata'] = suprafata
else:
    params['numar_bucati'] = numar_bucati
necesar_total = calculeaza_necesar_total(params, necesar_pe_zi_ajustat, zile_scurse)
prag_total = prag_udare_total(params)
trebuie_udat = necesar_total >= prag_total
if debit_pompa > 0:
    timp_udare = int((necesar_total / debit_pompa) * 60) if trebuie_udat else 0
else:
    timp_udare = 0
timp_sector = (timp_udare + 1) // 2

istoric = incarca_istoric(nume_cultura)
predictii_ai = incarca_predictii_ai(nume_cultura)
tratamente = incarca_tratamente(nume_cultura)

# ========== TITLU PRINCIPAL ==========
st.markdown("<div class='main-title'>🌱 AgroAI - Sistem inteligent pentru plante</div>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: -0.5rem; color: #4b5563;'>Monitorizare udare, fertilizare și tratamente asistate de AI</p>", unsafe_allow_html=True)
st.markdown("---")

# ========== KPI-URI ==========
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='font-size: 2rem;'>📅</div>
        <div class='metric-number'>{zile_scurse}</div>
        <div class='metric-label'>zile de la ultima udare</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='font-size: 2rem;'>💧</div>
        <div class='metric-number'>{int(necesar_total):,}</div>
        <div class='metric-label'>litri necesari acumulați</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    if trebuie_udat:
        st.markdown(f"""
        <div class='metric-card' style='border-bottom-color: #ef4444;'>
            <div style='font-size: 2rem;'>🚨</div>
            <div class='metric-number' style='color: #dc2626;'>UDĂ ACUM!</div>
            <div class='metric-label'>{timp_udare} minute</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 2rem;'>🌱</div>
            <div class='metric-number'>AȘTEAPTĂ</div>
            <div class='metric-label'>udare neesențială</div>
        </div>
        """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='font-size: 2rem;'>🌡️</div>
        <div class='metric-number'>{stadiu_curent}</div>
        <div class='metric-label'>stadiu fenologic</div>
    </div>
    """, unsafe_allow_html=True)

if trebuie_udat:
    st.markdown(f"""
    <div class='card warning-card' style='margin-top: 0.5rem;'>
        💧 <strong>Recomandare udare:</strong> {timp_udare} minute total<br>
        ➤ <strong>Sector 1:</strong> {timp_sector} minute &nbsp;&nbsp;|&nbsp;&nbsp; 
        ➤ <strong>Sector 2:</strong> {timp_udare - timp_sector} minute
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== GRAFICE ȘI ANALIZE (înlocuit use_container_width cu width) ==========
st.markdown("<div class='section-title'>📈 Evoluție și tendințe</div>", unsafe_allow_html=True)
if istoric:
    df_istoric = pd.DataFrame(istoric)
    df_istoric['data'] = pd.to_datetime(df_istoric['data'])
    df_istoric = df_istoric.sort_values('data')
    df_istoric = df_istoric.tail(zile_istoric)
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.line(df_istoric, x='data', y='necesar_acumulat',
                       title='Evoluția necesarului de apă',
                       labels={'data': 'Data', 'necesar_acumulat': 'Litri'},
                       template='plotly_white')
        fig1.update_traces(line_color='#10b981', line_width=3)
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
        st.plotly_chart(fig1, width='stretch')
    with col2:
        fig2 = px.area(df_istoric, x='data', y='necesar_acumulat',
                       title='Necesar cumulat (arie)',
                       labels={'data': 'Data', 'necesar_acumulat': 'Litri'},
                       template='plotly_white')
        fig2.update_traces(fillcolor='rgba(16,185,129,0.2)', line_color='#10b981')
        st.plotly_chart(fig2, width='stretch')
else:
    st.info("Nu există date istorice pentru această plantă. Rulează scriptul de predicție.")

st.markdown("---")
st.markdown("<div class='section-title'>🤖 Analiza predicțiilor AI</div>", unsafe_allow_html=True)
if predictii_ai:
    df_pred = pd.DataFrame(predictii_ai)
    df_pred['data'] = pd.to_datetime(df_pred['data'])
    df_pred = df_pred.sort_values('data')
    df_pred = df_pred.tail(zile_istoric)
    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.line(df_pred, x='data', y='minute_recomandate',
                       title='Minute recomandate de AI',
                       labels={'data': 'Data', 'minute_recomandate': 'Minute'},
                       template='plotly_white')
        fig3.update_traces(line_color='#ef4444', line_width=3)
        st.plotly_chart(fig3, width='stretch')
    with col2:
        if 'temperatura' in df_pred.columns:
            fig4 = px.scatter(df_pred, x='temperatura', y='minute_recomandate',
                              title='Corelație temperatură - recomandare AI',
                              labels={'temperatura': 'Temperatură (°C)', 'minute_recomandate': 'Minute'},
                              trendline='ols', template='plotly_white')
            st.plotly_chart(fig4, width='stretch')
        else:
            st.info("Nu există date suficiente pentru corelație.")
else:
    st.info("Nu există predicții AI pentru această plantă.")

st.markdown("---")
if istoric:
    st.markdown("<div class='section-title'>📊 Analize avansate</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if 'zile_de_la_udare' in df_istoric.columns:
            fig5 = px.bar(df_istoric, x='data', y='zile_de_la_udare',
                          title='Zile între udări',
                          labels={'data': 'Data', 'zile_de_la_udare': 'Zile'},
                          color='zile_de_la_udare', color_continuous_scale='Viridis',
                          template='plotly_white')
            st.plotly_chart(fig5, width='stretch')
        else:
            st.info("Coloana 'zile_de_la_udare' lipsește.")
    with col2:
        fig6 = px.histogram(df_istoric, x='necesar_acumulat',
                            title='Distribuția necesarului de apă',
                            labels={'necesar_acumulat': 'Litri', 'count': 'Frecvență'},
                            nbins=20, color_discrete_sequence=['#3b82f6'],
                            template='plotly_white')
        st.plotly_chart(fig6, width='stretch')
    st.markdown("---")

if predictii_ai and len(df_pred) > 5:
    st.markdown("<div class='section-title'>🌡️ Analiză sezonieră</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        df_pred['luna'] = pd.to_datetime(df_pred['data']).dt.month
        fig7 = px.box(df_pred, x='luna', y='minute_recomandate',
                      title='Minute recomandate pe luni',
                      labels={'luna': 'Luna', 'minute_recomandate': 'Minute'},
                      template='plotly_white')
        st.plotly_chart(fig7, width='stretch')
    with col2:
        if 'temperatura' in df_pred.columns and 'minute_recomandate' in df_pred.columns and 'zile_de_la_udare' in df_pred.columns:
            df_corr = df_pred[['minute_recomandate', 'temperatura', 'zile_de_la_udare']].corr()
            fig8 = px.imshow(df_corr, text_auto=True,
                             title='Matricea de corelație',
                             color_continuous_scale='RdBu', zmin=-1, zmax=1,
                             template='plotly_white')
            st.plotly_chart(fig8, width='stretch')
        else:
            st.info("Date insuficiente pentru corelație.")
    st.markdown("---")

if predictii_ai and len(df_pred) > 5:
    st.markdown("<div class='section-title'>📈 Dashboard integrat</div>", unsafe_allow_html=True)
    fig9 = make_subplots(rows=3, cols=1,
                         subplot_titles=('Temperatură', 'Minute recomandate', 'Zile de la udare'),
                         shared_xaxes=True)
    fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['temperatura'],
                              mode='lines+markers', name='Temperatură', line=dict(color='#f59e0b', width=2)),
                   row=1, col=1)
    fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['minute_recomandate'],
                              mode='lines+markers', name='Minute udare', line=dict(color='#ef4444', width=2)),
                   row=2, col=1)
    if 'zile_de_la_udare' in df_pred.columns:
        fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['zile_de_la_udare'],
                                  mode='lines+markers', name='Zile de la udare', line=dict(color='#10b981', width=2)),
                       row=3, col=1)
    fig9.update_layout(height=800, title_text="Analiza completă a plantei", template='plotly_white')
    st.plotly_chart(fig9, width='stretch')
    st.markdown("---")

# ========== SCHEMA COMPLETĂ DE TRATAMENTE ==========
st.markdown("<div class='section-title'>📅 Schema completă de tratamente</div>", unsafe_allow_html=True)

def get_urmatorul_tratament(tratamente, tip_tratament, interval_zile, produs_recomandat, doza_recomandata, unitate):
    ultima_aplicare = None
    for t in reversed(tratamente):
        if t.get('tip') == tip_tratament:
            try:
                ultima_aplicare = datetime.date.fromisoformat(t['data'])
                break
            except:
                pass
    if ultima_aplicare is None:
        return f"📢 Nu s-a înregistrat nicio aplicare de **{tip_tratament}**. Recomandare: aplică **{produs_recomandat}** (doză {doza_recomandata} {unitate}) la fiecare {interval_zile} zile."
    else:
        zile_ultima = (datetime.date.today() - ultima_aplicare).days
        if zile_ultima >= interval_zile:
            return f"⚠️ A trecut {zile_ultima} zile de la ultima aplicare de **{tip_tratament}**. Aplică acum **{produs_recomandat}** (doză {doza_recomandata} {unitate})."
        else:
            return f"✅ Ultima aplicare de **{tip_tratament}**: acum {zile_ultima} zile. Următoarea peste {interval_zile - zile_ultima} zile."

interval_fertilizare = params.get('tratament_fertilizare_interval_zile')
doza_fertilizare = params.get('tratament_fertilizare_doza')
produs_fertilizare = params.get('tratament_fertilizare_produs')
interval_fungicid = params.get('tratament_fungicid_interval_zile')
produs_fungicid = params.get('tratament_fungicid_produs')
interval_insecticid = params.get('tratament_insecticid_interval_zile')
produs_insecticid = params.get('tratament_insecticid_produs')

unitate_doza = "kg/mp" if params['tip'] == 'leguma' else "kg/buc"

col1, col2, col3 = st.columns(3)
with col1:
    if interval_fertilizare and interval_fertilizare > 0 and produs_fertilizare:
        mesaj_fertilizare = get_urmatorul_tratament(tratamente, "Fertilizare", interval_fertilizare, produs_fertilizare, doza_fertilizare, unitate_doza)
        st.info(f"🌱 **Fertilizare**\n\n{mesaj_fertilizare}")
    else:
        st.info("🌱 **Fertilizare** – Nu există o schemă configurată.")
with col2:
    if interval_fungicid and interval_fungicid > 0 and produs_fungicid:
        mesaj_fungicid = get_urmatorul_tratament(tratamente, "Fungicid", interval_fungicid, produs_fungicid, "", "")
        st.info(f"🍄 **Tratament fungicid**\n\n{mesaj_fungicid}")
    else:
        st.info("🍄 **Tratament fungicid** – Nu există o schemă configurată.")
with col3:
    if interval_insecticid and interval_insecticid > 0 and produs_insecticid:
        mesaj_insecticid = get_urmatorul_tratament(tratamente, "Insecticit", interval_insecticid, produs_insecticid, "", "")
        st.info(f"🐛 **Tratament insecticid**\n\n{mesaj_insecticid}")
    else:
        st.info("🐛 **Tratament insecticid** – Nu există o schemă configurată.")

st.markdown("---")

# ========== ISTORIC TRATAMENTE ==========
st.markdown("<div class='section-title'>📜 Istoric tratamente</div>", unsafe_allow_html=True)
if tratamente:
    df_trat = pd.DataFrame(tratamente)
    df_trat['data'] = pd.to_datetime(df_trat['data'])
    df_trat = df_trat.sort_values('data', ascending=False)
    st.dataframe(df_trat, width='stretch')
else:
    st.info("Nu există tratamente înregistrate pentru această plantă.")

st.markdown("---")

# ========== ISTORIC UDĂRI ==========
st.markdown("<div class='section-title'>📋 Istoric complet udări</div>", unsafe_allow_html=True)
if istoric:
    df_afisare = pd.DataFrame(istoric).tail(20)
    df_afisare = df_afisare.sort_values('data', ascending=False)
    st.dataframe(df_afisare, width='stretch')
else:
    st.info("Nu există date istorice pentru această plantă.")

st.markdown("---")

# ========== RECOMANDĂRI PERSONALIZATE ==========
st.markdown("<div class='section-title'>💡 Recomandări personalizate</div>", unsafe_allow_html=True)
recomandari = {
    "Plantare": "🌱 Udează zilnic sau la 2 zile pentru a asigura prinderea rădăcinilor.",
    "Vegetativ": "🌿 Udează mai rar (1-2 ori/săptămână), dar mai abundent pentru rădăcini adânci.",
    "Inflorire": "🌸 Perioada critică! Udează frecvent (2-3 ori/săptămână) pentru a preveni căderea florilor.",
    "Maturare": "🍅 Reduce udarea treptat pentru a concentra aromele.",
    "Pre-recoltare": "🔴 Oprește complet udarea cu 2-3 săptămâni înainte de recoltare!"
}
st.success(recomandari.get(stadiu_curent, ""))

if temperatura is not None:
    st.caption(f"🌡️ Ajustare necesar: {necesar_pe_zi_baza:.1f} → {necesar_pe_zi_ajustat:.1f} litri/unitate/zi (temp. {temperatura:.1f}°C, evaporare x{params['coeficient_evaporare']})")
else:
    st.caption(f"🌡️ Ajustare necesar: {necesar_pe_zi_baza:.1f} → {necesar_pe_zi_ajustat:.1f} litri/unitate/zi (evaporare x{params['coeficient_evaporare']})")

st.markdown("---")
st.caption(f"📅 Ultima actualizare: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🌱 AgroAI - Datele sunt salvate local în fișiere JSON specifice fiecărei plante.")