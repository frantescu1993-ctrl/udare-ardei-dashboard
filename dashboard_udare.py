# dashboard_udare.py - Dashboard extins cu grafice multiple
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

# ========== CSS PERSONALIZAT ==========
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== TITLU ==========
st.title("🌶️ Sistem AI pentru Udarea Ardeiului")
st.markdown("---")

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
    
    st.subheader("🌤️ Prognoză meteo")
    oras = st.text_input("Oraș", value="Bucharest")
    api_key = st.text_input("API Key OpenWeatherMap", type="password")
    
    st.markdown("---")
    st.subheader("📊 Filtre grafice")
    zile_istoric = st.slider("Perioadă istoric (zile)", 7, 90, 30)
    
    if st.button("🔄 Actualizează datele", use_container_width=True):
        st.rerun()

# ========== FUNCȚII ==========
def get_weather(oras, api_key):
    if not api_key or api_key == "":
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={oras}&appid={api_key}&units=metric&lang=ro"
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

# ========== CALCULE PRINCIPALE ==========
astazi = datetime.date.today()
zile_scurse = max(0, (astazi - ultima_udare).days)
necesar_total, necesar_pe_zi = calculeaza_necesar(stadiu_curent, zile_scurse, suprafata)
prag_udare = suprafata * 20
trebuie_udat = necesar_total >= prag_udare
timp_udare = int((necesar_total / debit_pompa) * 60) if trebuie_udat else 0
timp_sector = (timp_udare + 1) // 2

prognoza = get_weather(oras, api_key) if api_key else None
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
    if prognoza:
        st.metric("🌡️ Temperatură", f"{prognoza['temperatura']:.1f}°C", prognoza['descriere'])
    else:
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

# ========== RÂNDUL 3 - GRAFICE PREDICȚII AI ==========
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

# ========== RÂNDUL 4 - GRAFICE NOI ==========
st.subheader("📊 Analize avansate")

if istoric:
    df_istoric = pd.DataFrame(istoric)
    df_istoric['data'] = pd.to_datetime(df_istoric['data'])
    df_istoric = df_istoric.sort_values('data')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafic cu bare - zile între udări
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
        # Distribuția necesarului
        fig6 = px.histogram(
            df_istoric, x='necesar_acumulat',
            title='Distribuția necesarului de apă',
            labels={'necesar_acumulat': 'Litri', 'count': 'Frecvență'},
            nbins=20,
            color_discrete_sequence=['#3498db']
        )
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 5 - GRAFICE TEMPERATURĂ ȘI SEZON ==========
st.subheader("🌡️ Analiză sezonieră")

if istoric:
    col1, col2 = st.columns(2)
    
    with col1:
        # Boxplot pe luni
        df_istoric['luna'] = pd.to_datetime(df_istoric['data']).dt.month
        fig7 = px.box(
            df_istoric, x='luna', y='necesar_acumulat',
            title='Necesar lunar (boxplot)',
            labels={'luna': 'Luna', 'necesar_acumulat': 'Litri'}
        )
        st.plotly_chart(fig7, use_container_width=True)
    
    with col2:
        # Heatmap corelații
        if 'temperatura' in df_predictii.columns:
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

# ========== RÂNDUL 6 - GRAFICE COMPARATIVE ==========
st.subheader("📉 Comparații și tendințe")

if predictii_ai and istoric:
    col1, col2 = st.columns(2)
    
    with col1:
        # Evoluție temperatură
        fig9 = px.line(
            df_predictii, x='data', y='temperatura',
            title='Evoluția temperaturii în timp',
            labels={'data': 'Data', 'temperatura': 'Temperatură (°C)'}
        )
        fig9.update_traces(line_color='#f39c12', line_width=2)
        st.plotly_chart(fig9, use_container_width=True)
    
    with col2:
        # Precipitații vs recomandare
        if 'precipitatii' in df_predictii.columns:
            fig10 = px.bar(
                df_predictii, x='data', y='precipitatii',
                title='Precipitații înregistrate',
                labels={'data': 'Data', 'precipitatii': 'mm'}
            )
            fig10.update_traces(marker_color='#3498db')
            st.plotly_chart(fig10, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 7 - SUBPLOT COMPLEX ==========
st.subheader("📈 Dashboard integrat")

if predictii_ai and len(predictii_ai) > 5:
    # Subplot cu 3 grafice
    fig11 = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Temperatură', 'Minute recomandate', 'Zile de la udare'),
        shared_xaxes=True
    )
    
    fig11.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['temperatura'],
                   mode='lines+markers', name='Temperatură', line=dict(color='#f39c12')),
        row=1, col=1
    )
    
    fig11.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['minute_recomandate'],
                   mode='lines+markers', name='Minute udare', line=dict(color='#e74c3c')),
        row=2, col=1
    )
    
    fig11.add_trace(
        go.Scatter(x=df_predictii['data'], y=df_predictii['zile_de_la_udare'],
                   mode='lines+markers', name='Zile de la udare', line=dict(color='#2ecc71')),
        row=3, col=1
    )
    
    fig11.update_layout(height=800, title_text="Analiza completă a culturii")
    st.plotly_chart(fig11, use_container_width=True)

st.markdown("---")

# ========== RÂNDUL 8 - ISTORIC ==========
st.subheader("📋 Istoric complet")

if istoric:
    df_afisare = pd.DataFrame(istoric).tail(20)
    df_afisare = df_afisare.sort_values('data', ascending=False)
    st.dataframe(df_afisare, use_container_width=True)
else:
    st.info("Nu există date istorice. Rulează scriptul 'predict_ai.py' pentru a genera istoric.")

st.markdown("---")

# ========== RÂNDUL 9 - RECOMANDĂRI ==========
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