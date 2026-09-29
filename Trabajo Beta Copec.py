import pandas as pd
from pathlib import Path
# Como el Indice IPSA cambió de S&P a MCSI en septiembre tuve problemas para encontrar datos
# por lo que tomé hasta agosto datos encontrados en Findic.com

CARPETA = Path(r"D:\VSCODE1")

def leer_copec(archivo):
    df = pd.read_csv(archivo, encoding= "utf-8-sig", dtype= str)
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d.%m.%Y")
    df["Precio"] = df ["Último"].str.replace(".", "", regex= False).str.replace(",", ".", regex=False).astype(float)
    return df.set_index("Fecha")["Precio"].sort_index()
def leer_ipsa(archivo):
    df = pd.read_csv(archivo, sep=";", parse_dates=["fecha"])
    return df.set_index("fecha")["valor"].sort_index()
copec_d = leer_copec(CARPETA / "copec_diario.csv")
copec_s = leer_copec(CARPETA / "copec_semanal.csv")
copec_m = leer_copec(CARPETA / "copec_mensual.csv")

ipsa_d = leer_ipsa(CARPETA / "ipsa_diaria.csv")
ipsa_s = leer_ipsa(CARPETA / "ipsa_semanal.csv")
ipsa_m = leer_ipsa(CARPETA / "ipsa_mensual.csv")

corte = min(copec_d.index.max(), ipsa_d.index.max())

diario = pd.concat([copec_d, ipsa_d], axis=1, join = "inner", keys = ["copec", "ipsa"])
diario = diario.loc[:corte]

copec_s.index = (copec_s.index + pd.Timedelta(days=1)).to_period("W")
ipsa_s.index = ipsa_s.index.to_period("W")
semanal = pd.concat([copec_s, ipsa_s], axis=1, join="inner", keys=["copec", "ipsa"])
semanal = semanal[semanal.index.start_time + pd.Timedelta(days=4) <= corte]

copec_m.index = copec_m.index.to_period("M")
ipsa_m.index = ipsa_m.index.to_period("M")
mensual = pd.concat([copec_m, ipsa_m], axis=1, join="inner", keys=["copec", "ipsa"])
mensual = mensual[mensual.index.end_time.normalize() <= corte]  

resultados = {}
for nombre, precios in [("Diaria", diario), ("Semanal", semanal), ("Mensual", mensual)]:
    ret = precios.pct_change().dropna()
    cov = ret["copec"].cov(ret["ipsa"])
    var_m = ret["ipsa"].var()
    beta = cov / var_m

    corr = ret["copec"].corr(ret["ipsa"])
    r2 = corr ** 2 
    alfa = ret["copec"].mean() - beta * ret["ipsa"].mean()

    resultados[nombre] = {
        "Observaciones": len(ret),
        "Covarianza": cov,
        "Varianza mercado": var_m,
        "Beta": beta,
        "Correlacion": corr,
        "R2": r2,
        "Alfa": alfa
    }
tabla = pd.DataFrame(resultados)
print(tabla.round(6))
print()
for nombre in tabla.columns:
    b = tabla.loc["Beta", nombre]
    if b > 1:
        tipo = "más volátil que el mercado (agresiva)"
    elif b < 1:
        tipo = "menos volátil que el mercado (defensiva)"
    else:
        tipo = "igual de volátil que el mercado"
    print(f"{nombre}: beta = {b:.3f} -> Copec es {tipo}. "
          f"El IPSA explica {tabla.loc['R2', nombre]:.1%} de sus movimientos.")