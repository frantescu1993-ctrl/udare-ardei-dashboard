# predict_ai.py - Suport pentru multiple culturi
import datetime
import requests
import json
import os
import pandas as pd

# ========== CONFIGURAȚIE ==========
POMPA_DEBIT_LH = 5640

# Încarcă lista culturilor
def incarca_culturi():
    df = pd.read_csv('culturi.csv')
    return df

# Alege cultura activă (poți modifica aici sau citi dintr-un fișier)
nume_cultura = "Ardei"   # <--- schimbă aici sau citește din fișier

df_culturi = incarca_culturi()
row = df_culturi[df_culturi['nume'] == nume_cultura].iloc[0]
suprafata = row['suprafata']
necesar_pe_stadiu = {
    'Plantare': row['necesar_plantare'],
    'Vegetativ': row['necesar_vegetativ'],
    'Inflorire': row['necesar_inflorire'],
    'Maturare': row['necesar_maturare'],
    'Pre-recoltare': row['necesar_pre_recoltare']
}
prag_udare_litri_mp = row['prag_udare_litri_mp']

# ========== DATELE CUREnte ==========
ULTIMA_UDARE = datetime.date(2025, 3, 28)  # actualizează manual
STADIUL = "Inflorire"
ORAS = "Bucharest"
API_KEY_WEATHER = ""  # opțional

def get_prognoza():
    if not API_KEY_WEATHER:
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={ORAS}&appid={API_KEY_WEATHER}&units=metric"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return data['main']['temp']
    except:
        return None

def calculeaza():
    astazi = datetime.date.today()
    zile_scurse = max(0, (astazi - ULTIMA_UDARE).days)
    necesar_pe_zi = necesar_pe_stadiu[STADIUL]
    necesar_total = suprafata * necesar_pe_zi * zile_scurse
    prag = suprafata * prag_udare_litri_mp
    trebuie = necesar_total >= prag
    timp = int((necesar_total / POMPA_DEBIT_LH) * 60) if trebuie else 0
    return {
        'data': astazi.isoformat(),
        'minute_recomandate': timp,
        'zile_scurse': zile_scurse,
        'necesar_total': int(necesar_total),
        'trebuie_udare': trebuie,
        'cultura': nume_cultura
    }

def salveaza_istoric(rezultat):
    istoric = []
    if os.path.exists('predictii_ai.json'):
        with open('predictii_ai.json', 'r') as f:
            istoric = json.load(f)
    istoric.append(rezultat)
    with open('predictii_ai.json', 'w') as f:
        json.dump(istoric, f, indent=2)

def main():
    rez = calculeaza()
    print(f"Cultura: {rez['cultura']}")
    print(f"Zile de la ultima udare: {rez['zile_scurse']}")
    print(f"Necesar acumulat: {rez['necesar_total']} litri")
    if rez['trebuie_udare']:
        print(f"Recomandare: UDĂ {rez['minute_recomandate']} minute")
    else:
        print("Nu este necesară udarea acum.")
    salveaza_istoric(rez)

if __name__ == "__main__":
    main()