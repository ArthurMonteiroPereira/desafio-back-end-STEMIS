import json
from datetime import datetime, timedelta

# Parâmetros gerais
data_inicio = datetime(2025, 2, 1)
dias = 7
inversores = [1,2,3,4,5,6,7,8]

# Perfis dos inversores (fator multiplicativo)
perfis = {
    1: 1.2,  # mais forte
    2: 0.9,  # mais fraco
    3: 1.0,
    4: 1.0,
    5: 1.2,  # mais forte
    6: 0.9,  # mais fraco
    7: 1.0,
    8: 1.0
}

# Curva base de potência por hora (0h a 23h)
potencia_base = [
    0,0,0,0,0,0,200,400,800,1200,1600,2000,2200,2200,2100,1800,1400,1000,600,300,0,0,0,0
]
# Curva base de temperatura por hora (°C)
temperatura_base = [21,21,20,20,20,20,22,23,25,27,29,32,36,38,39,38,35,32,29,27,25,24,23,22]

def is_weekend(dt):
    return dt.weekday() >= 5

def main():
    registros = []
    for dia in range(dias):
        data = data_inicio + timedelta(days=dia)
        for hora in range(24):
            for inv in inversores:
                fator = perfis[inv]
                potencia = potencia_base[hora] * fator
                # Reduz 10% aos finais de semana
                if is_weekend(data):
                    potencia *= 0.9
                # Temperatura base + variação por inversor
                temp = temperatura_base[hora] + (inv-4.5)*0.5
                # Pequena variação aleatória
                temp += ((hora%3)-1)*0.3
                registro = {
                    "inversor_id": inv,
                    "datetime": {"$date": f"{data.strftime('%Y-%m-%d')}T{hora:02d}:00:00Z"},
                    "potencia_ativa_watt": round(potencia,2),
                    "temperatura_celsius": round(temp,1)
                }
                registros.append(registro)
    with open("sample/metrics_sintetico.json", "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)
    print(f"Arquivo gerado com {len(registros)} registros.")

if __name__ == "__main__":
    main() 