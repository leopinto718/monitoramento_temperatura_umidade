import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Lista de municípios do Ceará para localização (exemplos)
municipios_ceara = ["Fortaleza", "Sobral", "Juazeiro do Norte", "Crato", "Iguatu",
                   "Quixadá", "Maracanaú", "Russas", "Caucaia", "Canindé"]

# Número de linhas
num_linhas = 300

# Gerar sensor_id sequencial
sensor_id = np.arange(1, num_linhas+1)

# Selecionar localizações aleatoriamente
localizacao = np.random.choice(municipios_ceara, size=num_linhas)

# Gerar datas aleatórias dentro do ano de 2025
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)
delta = end_date - start_date
random_days = np.random.randint(0, delta.days, size=num_linhas)
datas = [start_date + timedelta(days=int(day)) for day in random_days]

# Gerar horas:
# Para cerca de 1/4 dos registros (aproximadamente 75), definir horas entre 12h e 16h
# Para os demais, horas aleatórias em 24h
horas = []
for i in range(num_linhas):
    if i < int(num_linhas * 0.25):
        hora = np.random.randint(12, 17)  # Inclui 16h
        minuto = np.random.randint(0, 60)
    else:
        hora = np.random.randint(0, 24)
        minuto = np.random.randint(0, 60)
    horas.append(f"{hora:02d}:{minuto:02d}")

# Temperaturas:
# Para os horários entre 12h e 16h, temperaturas mais altas (29 a 40)
# Para os demais, temperaturas mais baixas (20 a 29)
temperatura = np.zeros(num_linhas)
for i in range(num_linhas):
    hour = int(horas[i].split(':')[0])
    if 12 <= hour <= 16:
        temperatura[i] = np.random.uniform(29, 40)
    else:
        temperatura[i] = np.random.uniform(20, 29)

temperatura = np.round(temperatura, 1)

# Umidade:
# Para os horários entre 12h e 16h, umidade mais baixa (20 a 40)
# Para os demais, umidade mais alta (40 a 70)
umidade = np.zeros(num_linhas)
for i in range(num_linhas):
    hour = int(horas[i].split(':')[0])
    if 12 <= hour <= 16:
        umidade[i] = np.random.uniform(20, 40)
    else:
        umidade[i] = np.random.uniform(40, 70)

umidade = np.round(umidade, 1)

# Montar dataframe
df = pd.DataFrame({
    "sensor_id": sensor_id,
    "localizacao": localizacao,
    "temperatura": temperatura,
    "umidade": umidade,
    "data": [d.strftime("%Y-%m-%d") for d in datas],
    "hora": horas
})


# Obter lista de municípios únicos, ordenados
municipios_unicos = sorted(set(localizacao))
# Criar um dicionário de mapeamento de município para número sequencial
municipio_para_numero = {municipio: f"SENSOR{index+1:03d}" for index, municipio in enumerate(municipios_unicos)}

# Atribuir o sensor_id baseado no município
df['sensor_id'] = df['localizacao'].map(municipio_para_numero)

# Salvar em CSV com separador ";"
file_name = "dados/dados_feijao_ceara.csv"
df.to_csv(file_name, sep=";", index=False, encoding='utf-8-sig')

print(f"Arquivo '{file_name}' criado com sucesso!")
