# dashboard_udare.py - Dashboard cu prognoză meteo online
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
    page_title="🌶️ Sistem Udare Ardei",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCȚIE PROGNOZĂ METEO ==========
def get_weather_forecast():
    """Fetch current weather using OpenWeatherMap API (works with st.secrets on cloud)."""
    try:
        # Pe cloud, citește din st.secrets
        api_key = st.secrets["6aba5e7b4cf5ad67ff42cbe8e7cd240b"]
    except:
        # Dacă rulezi local fără secrets, returnează None
        return None
    
    city = "Fardea"  # Schimbă cu orașul tău
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

# ========== FUNCȚII AJUTĂTOARE ==========
def calculeaza_necesar(stadiu, zile_scurse, suprafata):
    necesar_zilnic = {
        "Plantare": 4, "Vegetativ": 5, "Inflorire": 7,
        "Maturare": 3, "Pre-recoltare": 0
    }
    necesar_pe_zi = necesar_zilnic.get(stadiu, 5)
    necesar_total = suprafata * necesar_pe_zi * zile_scurse
    return necesar_total, necesar_pe_zi

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
    
    suprafata = st.number_input("Suprafață (mp)", value=350, step=10)
    debit_pompa = st.number_input("Debit pompă (l/h)", value=5640, step=100)
    
    st.markdown("---")
    
    stadiu_curent = st.selectbox(
        "Stadiul curent",
        ["Plantare", "Vegetativ", "Inflorire", "Maturare", "Pre-recoltare"],
        index=2
    )
    
    ultima_udare = st.date_input(
        "Ultima udare",
        value=datetime.date(2025, 3, 28)
    )
    
    st.markdown("---")
    
    st.subheader("🌤️ Prognoză meteo în timp real")
    if st.button("🔍 Verifică vremea acum", use_container_width=True):
        with st.spinner("Se preia prognoza..."):
            weather_data = get_weather_forecast()
            if weather_data:
                st.success(f"**{weather_data['temperatura']:.1f}°C** | 💧 {weather_data['umiditate']}%")
                st.caption(f"📝 {weather_data['descriere'].capitalize()}")
            else:
                st.error("Nu s-a putut obține prognoza. Verifică cheia API în Secrets.")
    else:
        st.info("Apasă butonul de mai sus pentru a vedea prognoza actualizată.")
    
    st.markdown("---")
    st.subheader("📊 Filtre grafice")
    zile_istoric = st.slider("Perioadă istoric (zile)", 7, 90, 30)

# ========== CALCULE PRINCIPALE ==========
astazi = datetime.date.today()
zile_scurse = max(0, (astazi - ultima_udare).days)
necesar_total, necesar_pe_zi = calculeaza_necesar(stadiu_curent, zile_scurse, suprafata)
prag_udare = suprafata * 20
trebuie_udat = necesar_total >= prag_udare
timp_udare = int((necesar_total / debit_pompa) * 60) if trebuie_udat else 0
timp_sector = (timp_udare + 1) // 2

istoric = incarca_istoric()
predictii_ai = incarca_predictii_ai()

# ========== RÂNDUL 1 - KPI-uri ==========
st.subheader("📊 Starea curentă")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📅 Zile de la ultima udare", f"{zile_scurse} zile")
with col2:
    st.metric("💧 Necesar acumulat", f"{int(necesar_total):,} litri")
with col3:
    if trebuie_udat:
        st.metric("🚨 Recomandare", "UDĂ ACUM!", delta=f"{timp_udare} minute")
    else:
        st.metric("🌱 Recomandare", "AȘTEAPTĂ")
with col4:
    st.metric("🌱 Stadiu", stadiu_curent)

if trebuie_udat:
    st.info(f"💧 **Recomandare udare:** {timp_udare} minute total\n\n- Sector 1: {timp_sector} minute\n- Sector 2: {timp_udare - timp_sector} minute")

st.markdown("---")

# ========== RÂNDUL 2 - GRAFICE PRINCIPALE ==========
st.subheader("📈 Evoluție și tendințe")

if istoric:
    df_istoric = pd.DataFrame(istoric)
    df_istoric['data'] = pd.to_datetime(df_istoric['data'])
    df_istoric = df_istoric.sort_values('data')
    df_istoric = df_istoric.tail(zile_istoric)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.line(
            df_istoric, x='data', y='necesar_acumulat',
            title='Evoluția necesarului de apă',
            labels={'data': 'Data', 'necesar_acumulat': 'Necesar (litri)'}
        )
        fig1.update_traces(line_color='#2ecc71', line_width=2)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.area(
            df_istoric, x='data', y='necesar_acumulat',
            title='Necesar cumulat (arie)',
            labels={'data': 'Data', 'necesar_acumulat': 'Litri'}
        )
        fig2.update_traces(fillcolor='rgba(46,204,113,0.3)', line_color='#2ecc71')
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 3 - PREDICȚII AI ==========
if predictii_ai:
    st.subheader("🤖 Analiza predicțiilor AI")
    
    df_predictii = pd.DataFrame(predictii_ai)
    df_predictii['data'] = pd.to_datetime(df_predictii['data'])
    df_predictii = df_predictii.sort_values('data')
    df_predictii = df_predictii.tail(zile_istoric)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig3 = px.line(
            df_predictii, x='data', y='minute_recomandate',
            title='Minute recomandate de AI',
            labels={'data': 'Data', 'minute_recomandate': 'Minute'}
        )
        fig3.update_traces(line_color='#e74c3c', line_width=2)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        fig4 = px.scatter(
            df_predictii, x='temperatura', y='minute_recomandate',
            title='Corelație temperatură - recomandare AI',
            labels={'temperatura': 'Temperatură (°C)', 'minute_recomandate': 'Minute'},
            trendline='ols'
        )
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 4 - ANALIZE AVANSATE ==========
st.subheader("📊 Analize avansate")

if istoric:
    col1, col2 = st.columns(2)
    
    with col1:
        if 'zile_de_la_udare' in df_istoric.columns:
            fig5 = px.bar(
                df_istoric, x='data', y='zile_de_la_udare',
                title='Zile între udări',
                labels={'data': 'Data', 'zile_de_la_udare': 'Zile'},
                color='zile_de_la_udare',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig5, use_container_width=True)
    
    with col2:
        fig6 = px.histogram(
            df_istoric, x='necesar_acumulat',
            title='Distribuția necesarului de apă',
            labels={'necesar_acumulat': 'Litri', 'count': 'Frecvență'},
            nbins=20,
            color_discrete_sequence=['#3498db']
        )
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 5 - TEMPERATURĂ ȘI SEZON ==========
st.subheader("🌡️ Analiză sezonieră")

if predictii_ai:
    col1, col2 = st.columns(2)
    
    with col1:
        # Boxplot pe luni
        df_predictii['luna'] = pd.to_datetime(df_predictii['data']).dt.month
        fig7 = px.box(
            df_predictii, x='luna', y='minute_recomandate',
            title='Minute recomandate pe luni (boxplot)',
            labels={'luna': 'Luna', 'minute_recomandate': 'Minute'}
        )
        st.plotly_chart(fig7, use_container_width=True)
    
    with col2:
        # Matrice corelație
        df_corr = df_predictii[['minute_recomandate', 'temperatura', 'zile_de_la_udare']].corr()
        fig8 = px.imshow(
            df_corr,
            text_auto=True,
            title='Matricea de corelație',
            color_continuous_scale='RdBu',
            zmin=-1, zmax=1
        )
        st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 6 - SUBPLOT COMPLEX ==========
if predictii_ai and len(predictii_ai) > 5:
    st.subheader("📈 Dashboard integrat")
    
    fig9 = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Temperatură', 'Minute recomandate', 'Zile de la udare'),
        shared_xaxes=True
    )
    
    fig9.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['temperatura'],
                   mode='lines+markers', name='Temperatură', line=dict(color='#f39c12')),
        row=1, col=1
    )
    
    fig9.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['minute_recomandate'],
                   mode='lines+markers', name='Minute udare', line=dict(color='#e74c3c')),
        row=2, col=1
    )
    
    fig9.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['zile_de_la_udare'],
                   mode='lines+markers', name='Zile de la udare', line=dict(color='#2ecc71')),
        row=3, col=1
    )
    
    fig9.update_layout(height=800, title_text="Analiza completă a culturii")
    st.plotly_chart(fig9, use_container_width=True)

st.markdown("---")

# ========== ISTORIC ==========
st.subheader("📋 Istoric complet")

if istoric:
    df_afisare = pd.DataFrame(istoric).tail(20)
    df_afisare = df_afisare.sort_values('data', ascending=False)
    st.dataframe(df_afisare, use_container_width=True)
else:
    st.info("Nu există date istorice. Rulează scriptul 'predict_ai.py' pentru a genera istoric.")

st.markdown("---")

# ========== RECOMANDĂRI ==========
st.subheader("💡 Recomandări personalizate")

recomandari = {
    "Plantare": "🌱 Udează zilnic sau la 2 zile pentru a asigura prinderea rădăcinilor.",
    "Vegetativ": "🌿 Udează mai rar (1-2 ori/săptămână), dar mai abundent pentru rădăcini adânci.",
    "Inflorire": "🌸 Perioada critică! Udează frecvent (2-3 ori/săptămână) pentru a preveni căderea florilor.",
    "Maturare": "🍅 Reduce udarea treptat pentru a concentra aromele.",
    "Pre-recoltare": "🔴 Oprește complet udarea cu 2-3 săptămâni înainte de recoltare!"
}
st.success(recomandari.get(stadiu_curent, ""))

# ========== FOOTER ==========
st.markdown("---")
st.caption(f"📅 Ultima actualizare: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🌶️ Sistem AI pentru udarea ardeiului - Datele sunt salvate local")
