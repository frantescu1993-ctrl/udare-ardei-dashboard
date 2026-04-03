# dashboard_udare.py - Sistem AI pentru legume, arbori și arbuști
# Suportă calcul pe suprafață (mp) sau pe bucată

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

# ========== CSS PERSONALIZAT ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    .card {
        background-color: white;
        border-radius: 1rem;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
    .metric-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 5px solid #22c55e;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
    }
    .warning-card { background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%); border-left: 5px solid #eab308; }
    .danger-card { background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-left: 5px solid #ef4444; }
    .info-card { background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); border-left: 5px solid #0ea5e9; }
    .stButton > button {
        background-color: #22c55e;
        color: white;
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover { background-color: #16a34a; transform: scale(1.02); box-shadow: 0 2px 8px rgba(34,197,94,0.3); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #166534; }
    .dataframe { border-radius: 0.75rem; overflow: hidden; font-size: 0.9rem; }
    .dataframe th { background-color: #f1f5f9 !important; color: #0f172a; font-weight: 600; }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #15803d, #4ade80);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #14532d;
        border-left: 4px solid #22c55e;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
    hr { margin: 1rem 0; border: 0; height: 1px; background: linear-gradient(90deg, #e2e8f0, #22c55e, #e2e8f0); }
    .weather-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; border-radius: 1rem; padding: 1rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ========== FUNCȚII GENERALE ==========
@st.cache_data(ttl=3600)
def incarca_culturi():
    try:
        df = pd.read_csv('culturi.csv')
        # Normalizare coloane
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
        # Coloane specifice
        if 'suprafata_mp' not in df.columns:
            df['suprafata_mp'] = 0
        if 'numar_bucati' not in df.columns:
            df['numar_bucati'] = 0
        if 'prag_udare_litri_mp' not in df.columns:
            df['prag_udare_litri_mp'] = 20
        if 'prag_udare_litri_buc' not in df.columns:
            df['prag_udare_litri_buc'] = 0
        optional = ['fertilizare_frecventa_zile', 'fertilizare_doza_kg_mp', 'fertilizare_doza_kg_buc',
                    'fertilizare_produs', 'tratamente_fungicide', 'tratamente_insecticide']
        for col in optional:
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
        'fertilizare_frecventa_zile': row['fertilizare_frecventa_zile'] if not pd.isna(row['fertilizare_frecventa_zile']) else None,
        'fertilizare_doza_kg_mp': float(row['fertilizare_doza_kg_mp']) if not pd.isna(row['fertilizare_doza_kg_mp']) else None,
        'fertilizare_doza_kg_buc': float(row['fertilizare_doza_kg_buc']) if not pd.isna(row['fertilizare_doza_kg_buc']) else None,
        'fertilizare_produs': row['fertilizare_produs'] if not pd.isna(row['fertilizare_produs']) else None,
        'tratamente_fungicide': row['tratamente_fungicide'] if not pd.isna(row['tratamente_fungicide']) else None,
        'tratamente_insecticide': row['tratamente_insecticide'] if not pd.isna(row['tratamente_insecticide']) else None
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
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995572.png", width=60)
    st.markdown("<h2 style='text-align: center; color: #15803d;'>🌱 AgroAI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    df_culturi = incarca_culturi()
    if df_culturi.empty:
        st.stop()
    
    nume_cultura = st.selectbox("🌿 Selectează planta", df_culturi['nume'].tolist())
    params = get_parametri_cultura(nume_cultura, df_culturi)
    
    with st.expander("📋 Parametrii plantei"):
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
        suprafata = st.number_input("📏 Suprafață (mp)", value=float(params['suprafata']), step=10.0)
        numar_bucati = 0
    else:
        numar_bucati = st.number_input("🌳 Număr bucăți", value=int(params['numar_bucati']), step=1, min_value=1)
        suprafata = 0
    debit_pompa = st.number_input("💧 Debit pompă (l/h)", value=5640, step=100, min_value=1)
    st.markdown("---")
    stadiu_curent = st.selectbox(
        "🌱 Stadiul curent",
        ["Plantare", "Vegetativ", "Inflorire", "Maturare", "Pre-recoltare"],
        index=2
    )
    ultima_udare = st.date_input("📅 Ultima udare", value=datetime.date.today() - datetime.timedelta(days=3))
    st.markdown("---")
    
    st.subheader("🌤️ Prognoză meteo")
    if st.button("🔍 Verifică vremea acum", use_container_width=True):
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
    st.subheader("🧪 Înregistrează tratament")
    with st.form("form_tratament"):
        tip_tratament = st.selectbox("Tip tratament", ["Fertilizare", "Fungicid", "Insecticit", "Altul"])
        produs = st.text_input("Produs")
        doza = st.number_input("Doză (kg/unitate sau litri)", min_value=0.0, step=0.01, format="%.2f")
        observatii = st.text_area("Observații")
        submitted = st.form_submit_button("💾 Salvează")
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
    st.subheader("📊 Filtre grafice")
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
# Suprascrie cantitatea (suprafata sau nr bucati) cu valorile din UI
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
st.caption("Monitorizare udare, fertilizare și tratamente asistate de AI")

# ========== KPI-URI ==========
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <h3 style='margin:0; color:#15803d;'>📅 {zile_scurse}</h3>
        <p style='margin:0; color:#14532d;'>zile de la ultima udare</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <h3 style='margin:0; color:#15803d;'>💧 {int(necesar_total):,}</h3>
        <p style='margin:0; color:#14532d;'>litri necesari acumulați</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    if trebuie_udat:
        st.markdown(f"""
        <div class='metric-card danger-card'>
            <h3 style='margin:0; color:#dc2626;'>🚨 UDĂ ACUM!</h3>
            <p style='margin:0;'>{timp_udare} minute</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='metric-card'>
            <h3 style='margin:0; color:#15803d;'>🌱 AȘTEAPTĂ</h3>
            <p style='margin:0;'>udare neesențială</p>
        </div>
        """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <h3 style='margin:0; color:#15803d;'>🌡️ {stadiu_curent}</h3>
        <p style='margin:0;'>stadiu fenologic</p>
    </div>
    """, unsafe_allow_html=True)

if trebuie_udat:
    st.markdown(f"""
    <div class='card warning-card' style='margin-top: 0.5rem;'>
        💧 <strong>Recomandare udare:</strong> {timp_udare} minute total<br>
        ➤ Sector 1: {timp_sector} minute &nbsp;&nbsp;|&nbsp;&nbsp; ➤ Sector 2: {timp_udare - timp_sector} minute
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== GRAFICE ȘI ANALIZE (identice cu versiunea anterioară) ==========
# ... păstrează aici toate secțiunile de grafice, predicții AI, analize avansate, etc.
# Pentru a economisi spațiu, le includ din nou mai jos (sunt aceleași ca în codul anterior).

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
        fig1.update_traces(line_color='#22c55e', line_width=3)
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.area(df_istoric, x='data', y='necesar_acumulat',
                       title='Necesar cumulat (arie)',
                       labels={'data': 'Data', 'necesar_acumulat': 'Litri'},
                       template='plotly_white')
        fig2.update_traces(fillcolor='rgba(34,197,94,0.2)', line_color='#22c55e')
        st.plotly_chart(fig2, use_container_width=True)
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
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        if 'temperatura' in df_pred.columns:
            fig4 = px.scatter(df_pred, x='temperatura', y='minute_recomandate',
                              title='Corelație temperatură - recomandare AI',
                              labels={'temperatura': 'Temperatură (°C)', 'minute_recomandate': 'Minute'},
                              trendline='ols', template='plotly_white')
            st.plotly_chart(fig4, use_container_width=True)
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
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Coloana 'zile_de_la_udare' lipsește.")
    with col2:
        fig6 = px.histogram(df_istoric, x='necesar_acumulat',
                            title='Distribuția necesarului de apă',
                            labels={'necesar_acumulat': 'Litri', 'count': 'Frecvență'},
                            nbins=20, color_discrete_sequence=['#3b82f6'],
                            template='plotly_white')
        st.plotly_chart(fig6, use_container_width=True)
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
        st.plotly_chart(fig7, use_container_width=True)
    with col2:
        if 'temperatura' in df_pred.columns and 'minute_recomandate' in df_pred.columns and 'zile_de_la_udare' in df_pred.columns:
            df_corr = df_pred[['minute_recomandate', 'temperatura', 'zile_de_la_udare']].corr()
            fig8 = px.imshow(df_corr, text_auto=True,
                             title='Matricea de corelație',
                             color_continuous_scale='RdBu', zmin=-1, zmax=1,
                             template='plotly_white')
            st.plotly_chart(fig8, use_container_width=True)
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
    st.plotly_chart(fig9, use_container_width=True)
    st.markdown("---")

# ========== RECOMANDĂRI FERTILIZARE ȘI TRATAMENTE ==========
st.markdown("<div class='section-title'>🧪 Recomandări tratamente și fertilizare</div>", unsafe_allow_html=True)
frecventa_fertilizare = params.get('fertilizare_frecventa_zile')
if frecventa_fertilizare is not None and frecventa_fertilizare > 0:
    ultima_fertilizare = None
    if tratamente:
        for t in reversed(tratamente):
            if t.get('tip') == 'Fertilizare':
                try:
                    ultima_fertilizare = datetime.date.fromisoformat(t['data'])
                    break
                except:
                    pass
    doza_recomandata = params['fertilizare_doza_kg_buc'] if params['tip'] != 'leguma' else params['fertilizare_doza_kg_mp']
    unitate = "kg/buc" if params['tip'] != 'leguma' else "kg/mp"
    if ultima_fertilizare is None:
        st.warning(f"📢 Nu s-a înregistrat nicio fertilizare pentru {nume_cultura}. Recomandare: aplică **{params['fertilizare_produs']}** (doză {doza_recomandata} {unitate}) la fiecare {frecventa_fertilizare} zile.")
    else:
        zile_ultima = (datetime.date.today() - ultima_fertilizare).days
        if zile_ultima >= frecventa_fertilizare:
            st.error(f"⚠️ A trecut {zile_ultima} zile de la ultima fertilizare. Aplică acum **{params['fertilizare_produs']}** (doză {doza_recomandata} {unitate}).")
        else:
            st.success(f"✅ Ultima fertilizare: acum {zile_ultima} zile. Următoarea peste {frecventa_fertilizare - zile_ultima} zile.")
else:
    st.info("Nu există recomandări de fertilizare configurate pentru această plantă.")

if params.get('tratamente_fungicide') and not pd.isna(params['tratamente_fungicide']):
    st.info(f"🍄 **Recomandare fungicid:** {params['tratamente_fungicide']}")
if params.get('tratamente_insecticide') and not pd.isna(params['tratamente_insecticide']):
    st.info(f"🐛 **Recomandare insecticid:** {params['tratamente_insecticide']}")

# ========== ISTORIC TRATAMENTE ==========
st.markdown("<div class='section-title'>📜 Istoric tratamente</div>", unsafe_allow_html=True)
if tratamente:
    df_trat = pd.DataFrame(tratamente)
    df_trat['data'] = pd.to_datetime(df_trat['data'])
    df_trat = df_trat.sort_values('data', ascending=False)
    st.dataframe(df_trat, use_container_width=True)
else:
    st.info("Nu există tratamente înregistrate pentru această plantă.")

st.markdown("---")

# ========== ISTORIC UDĂRI ==========
st.markdown("<div class='section-title'>📋 Istoric complet udări</div>", unsafe_allow_html=True)
if istoric:
    df_afisare = pd.DataFrame(istoric).tail(20)
    df_afisare = df_afisare.sort_values('data', ascending=False)
    st.dataframe(df_afisare, use_container_width=True)
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