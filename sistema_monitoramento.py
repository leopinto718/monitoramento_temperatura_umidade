import pandas as pd
import json
import os
import matplotlib.pyplot as plt
from collections import defaultdict
from statistics import mean

# =====================================================================
# ESTRUTURAS GLOBAIS
# =====================================================================

leituras = []  # Lista de todas as leituras (cada leitura é um dict)
sensores = {}  # {sensor_id: {'localizacao': str, 'leituras': []}}

# Limites padrão
# Configurados para a cultura do feijão 
LIMITE_TEMP_MIN = 12.0
LIMITE_TEMP_MAX = 29.0
LIMITE_UMIDADE_MIN = 40.0
LIMITE_UMIDADE_MAX = 70.0

# Caminho padrão para salvar relatórios
PASTA_RELATORIOS = r"C:\mba_ciencia_de_dados\programacao_para_ciencia_de_dados\projeto_10_monitoramento_temperatura_umidade\relatorios"

# Garante que a pasta exista
os.makedirs(PASTA_RELATORIOS, exist_ok=True)


# =====================================================================
# FUNÇÕES DO SISTEMA
# =====================================================================

def cadastrar_sensor(sensor_id, localizacao=None):
    """Cadastra um sensor caso ainda não exista."""
    if sensor_id not in sensores:
        sensores[sensor_id] = {
            "localizacao": localizacao,
            "leituras": []
        }
    return sensores[sensor_id]


def registrar_leitura(sensor_id, temperatura, umidade, data, hora, localizacao=None):
    """Registra nova leitura de sensor (em memória).
    Valida tipos básicos e anexa tanto em `leituras` como em `sensores[sensor_id]['leituras']`.
    """
    try:
        temperatura = float(temperatura)
    except (ValueError, TypeError):
        raise ValueError(f'Temperatura inválida: {temperatura}')
    try:
        umidade = float(umidade)
    except (ValueError, TypeError):
        raise ValueError(f'Umidade inválida: {umidade}')
    
    leitura = {
        'sensor_id': str(sensor_id),
        'temperatura': temperatura,
        'umidade': umidade,
        'data': str(data),
        'hora': str(hora),
        'localizacao': localizacao
    }

    leituras.append(leitura)
    sensor = cadastrar_sensor(sensor_id, localizacao)
    sensor['leituras'].append(leitura)
    return leitura


def carregar_csv(path, sep=";"):
    """Carrega um arquivo CSV e registra todas as leituras."""
    df = pd.read_csv(path, sep=sep)

    # limpeza: remover linhas sem sensor_id/temperatura/umidade
    df = df.dropna(subset=["sensor_id", "temperatura", "umidade"])

    for _, row in df.iterrows():
        registrar_leitura(
            sensor_id=row["sensor_id"],
            temperatura=row["temperatura"],
            umidade=row["umidade"],
            data=row["data"],
            hora=row["hora"],
            localizacao=row.get("localizacao")
        )
    return df


def calcular_estatisticas_sensor(sensor_id):
    if sensor_id not in sensores:
        return None
    
    #cria variável com as leituras do sensor indicado
    leit = sensores[sensor_id]["leituras"] 
    if not leit:
        return None

    temps = [x["temperatura"] for x in leit] # recebe as temperaturas
    ums = [x["umidade"] for x in leit] #recebe a umidade do ar 

    return {
        "sensor_id": sensor_id,
        "localizacao": sensores[sensor_id].get("localizacao"),
        "temperatura_media": mean(temps),
        "temperatura_minima": min(temps),
        "temperatura_maxima": max(temps),
        "umidade_media": mean(ums),
        "umidade_minima": min(ums),
        "umidade_maxima": max(ums),
        "total_leituras": len(leit),
        "total_alertas": len(detectar_alertas(sensor_id))
    }


def detectar_alertas(sensor_id=None):
    """Identifica leituras fora dos limites."""
    resultado = []

    sensores_alvo = [sensor_id] if sensor_id else list(sensores.keys())

    for sid in sensores_alvo:
        if sid not in sensores: # Se o sensor não existir, pula para o próximo
            continue 
        
        # iteração para ler as leituras do sensor e armazenar nos resultados, caso elas estejam fora 
        # dos limites previamente configurados
        for l in sensores[sid]["leituras"]:

            if l["temperatura"] < LIMITE_TEMP_MIN:
                resultado.append({
                    "sensor_id": sid,
                    "tipo": "Temperatura Baixa",
                    "valor": l["temperatura"],
                    "limite": LIMITE_TEMP_MIN,
                    "data": l["data"],
                    "hora": l["hora"],
                })

            elif l["temperatura"] > LIMITE_TEMP_MAX:
                resultado.append({
                    "sensor_id": sid,
                    "tipo": "Temperatura Alta",
                    "valor": l["temperatura"],
                    "limite": LIMITE_TEMP_MAX,
                    "data": l["data"],
                    "hora": l["hora"],
                })

            if l["umidade"] < LIMITE_UMIDADE_MIN:
                resultado.append({
                    "sensor_id": sid,
                    "tipo": "Umidade Baixa",
                    "valor": l["umidade"],
                    "limite": LIMITE_UMIDADE_MIN,
                    "data": l["data"],
                    "hora": l["hora"],
                })

            elif l["umidade"] > LIMITE_UMIDADE_MAX:
                resultado.append({
                    "sensor_id": sid,
                    "tipo": "Umidade Alta",
                    "valor": l["umidade"],
                    "limite": LIMITE_UMIDADE_MAX,
                    "data": l["data"],
                    "hora": l["hora"],
                })

    return resultado


def calcular_media_por_hora(sensor_id):
    """Calcula média de temperatura por hora."""
    if sensor_id not in sensores:
        return {}

    horas = defaultdict(list)

    for l in sensores[sensor_id]["leituras"]:
        try:
            h = int(str(l["hora"]).split(":")[0])
        except:
            continue
        horas[h].append(l["temperatura"])

    return {h: mean(vals) for h, vals in horas.items()}


def identificar_extremos():
    """Procura valores extremos globais."""
    if not leituras:
        return {}

    df = pd.DataFrame(leituras)

    return {
        "temperatura_max": df.loc[df["temperatura"].idxmax()].to_dict(),
        "temperatura_min": df.loc[df["temperatura"].idxmin()].to_dict(),
        "umidade_max": df.loc[df["umidade"].idxmax()].to_dict(),
        "umidade_min": df.loc[df["umidade"].idxmin()].to_dict(),
    }


def gerar_relatorio_sensor(sensor_id):
    est = calcular_estatisticas_sensor(sensor_id)
    medias = calcular_media_por_hora(sensor_id)
    alertas = detectar_alertas(sensor_id)
    leit = sensores[sensor_id]["leituras"]

    rel = {
        "estatisticas": est,
        "medias_por_hora": medias,
        "alertas": alertas,
        "leituras": leit
    }

    # =========================================================================
    # CRIA PASTA DO SENSOR
    # =========================================================================
    pasta = os.path.join(PASTA_RELATORIOS, f"sensor_{sensor_id}")
    os.makedirs(pasta, exist_ok=True)

    # =========================================================================
    # GRÁFICO 1 – Histograma de Temperatura
    # =========================================================================
    temps = [l["temperatura"] for l in leit]
    plt.hist(temps, bins=15)
    salvar_grafico(os.path.join(pasta, "temperatura_hist.png"),
                   f"Histograma de Temperatura - {sensor_id}")

    # =========================================================================
    # GRÁFICO 2 – Histograma de Umidade
    # =========================================================================
    ums = [l["umidade"] for l in leit]
    plt.hist(ums, bins=15)
    salvar_grafico(os.path.join(pasta, "umidade_hist.png"),
                   f"Histograma de Umidade - {sensor_id}")

    # =========================================================================
    # GRÁFICO 3 – Temperatura por hora (média)
    # =========================================================================
    if medias:
        horas = sorted(medias.keys())
        valores = [medias[h] for h in horas]

        plt.plot(horas, valores, marker="o")
        plt.xlabel("Hora")
        plt.ylabel("Temperatura (°C)")
        salvar_grafico(os.path.join(pasta, "temperatura_por_hora.png"),
                       f"Média de Temperatura por Hora - {sensor_id}")

    # Caminho do JSON
    nome_arquivo = f"rel_{sensor_id}.json"
    destino = os.path.join(PASTA_RELATORIOS, nome_arquivo)

    with open(destino, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)

    return rel, destino




def gerar_relatorio_geral():
    rel_sensores = [calcular_estatisticas_sensor(sid) for sid in sensores]
    alertas = detectar_alertas()
    extremos = identificar_extremos()

    rel = {
        "total_sensores": len(sensores),
        "total_leituras": len(leituras),
        "relatorios_sensores": rel_sensores,
        "total_alertas": len(alertas),
        "alertas": alertas,
        "extremos": extremos,
    }

    # =========================================================================
    # PASTA GERAL
    # =========================================================================
    pasta = os.path.join(PASTA_RELATORIOS, "geral")
    os.makedirs(pasta, exist_ok=True)

    # =========================================================================
    # GRÁFICO 1 – Hist temperatura geral
    # =========================================================================
    df = pd.DataFrame(leituras)

    plt.hist(df['temperatura'].dropna(), bins=20)
    salvar_grafico(os.path.join(pasta, "hist_temp_geral.png"),
                   "Histograma de Temperatura - Geral")

    # =========================================================================
    # GRÁFICO 2 – Hist umidade geral
    # =========================================================================
    plt.hist(df['umidade'].dropna(), bins=20)
    salvar_grafico(os.path.join(pasta, "hist_umidade_geral.png"),
                   "Histograma de Umidade - Geral")

    # =========================================================================
    # GRÁFICO 3 – Alertas por sensor
    # =========================================================================
    sensores_ids = [s["sensor_id"] for s in rel_sensores]
    qtd_alertas = [s["total_alertas"] for s in rel_sensores]

    plt.bar(sensores_ids, qtd_alertas)
    plt.xticks(rotation=90)
    plt.ylabel("Quantidade de Alertas")
    salvar_grafico(os.path.join(pasta, "alertas_por_sensor.png"),
                   "Alertas por Sensor")

    # Salvar JSON
    destino = os.path.join(PASTA_RELATORIOS, "rel_geral.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)

    return rel, destino


def salvar_grafico(caminho, titulo):
    plt.title(titulo)
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()



# =====================================================================
# MENU INTERATIVO
# =====================================================================

def menu_principal():
    print("\n" + "="*55)
    print("              SISTEMA DE MONITORAMENTO")
    print("="*55)
    print("1 - Carregar leituras de um arquivo CSV")
    print("2 - Inserir leitura manualmente")
    print("3 - Gerar relatório de um sensor")
    print("4 - Gerar relatório geral")
    print("5 - Configurar limites")
    print("6 - Sair")
    print("="*55)
    return input("Escolha uma opção: ").strip()


def main():
    print("=== SISTEMA DE MONITORAMENTO AMBIENTAL ===")

    dados_carregados = False

    while True:
        opcao = menu_principal()

        # ------------------------------------------------------------------
        # 1) CARREGAR CSV
        # ------------------------------------------------------------------
        if opcao == "1":
            caminho = input("Caminho do arquivo CSV: ").strip()
            separador = input("Separador (padrão ';'): ").strip() or ";"

            try:
                carregar_csv(caminho, sep=separador)
                print("CSV carregado com sucesso!")
                print(f"Leituras: {len(leituras)}, Sensores: {len(sensores)}")
                dados_carregados = True
            except Exception as e:
                print("Erro ao carregar CSV:", e)

        # ------------------------------------------------------------------
        # 2) INSERIR MANUALMENTE
        # ------------------------------------------------------------------
        elif opcao == "2":
            print("\n--- Inserção Manual ---")
            try:
                sensor = input("ID do sensor: ")
                local = input("Localização: ")
                temp = float(input("Temperatura: "))
                umid = float(input("Umidade: "))
                data = input("Data (AAAA-MM-DD): ")
                hora = input("Hora (HH:MM): ")

                registrar_leitura(sensor, temp, umid, data, hora, local)
                print("Leitura registrada!")
                dados_carregados = True

            except ValueError:
                print("Erro: valores inválidos.")

        # ------------------------------------------------------------------
        # 3) RELATÓRIO DE SENSOR
        # ------------------------------------------------------------------
        elif opcao == "3":
            if not dados_carregados:
                print("Primeiro carregue dados!")
                continue

            sid = input("ID do sensor: ").strip()

            if sid not in sensores:
                print("Sensor não encontrado.")
                continue

            rel, destino = gerar_relatorio_sensor(sid)
            print("\n=== ESTATÍSTICAS ===")
            print(json.dumps(rel["estatisticas"], indent=2, ensure_ascii=False))
            print("Alertas:", len(rel["alertas"]))
            print(f"\nRelatório salvo automaticamente em:\n{destino}")

        # ------------------------------------------------------------------
        # 4) RELATÓRIO GERAL
        # ------------------------------------------------------------------
        elif opcao == "4":
            if not dados_carregados:
                print("⚠️ Primeiro carregue dados!")
                continue

            rel, destino = gerar_relatorio_geral()
            print("\n=== RELATÓRIO GERAL ===")
            print("Total sensores:", rel["total_sensores"])
            print("Total leituras:", rel["total_leituras"])
            print("Total alertas:", rel["total_alertas"])
            print(f"\nRelatório salvo automaticamente em:\n{destino}")

        # ------------------------------------------------------------------
        # 5) CONFIGURAR LIMITES
        # ------------------------------------------------------------------
        elif opcao == "5":
            global LIMITE_TEMP_MIN, LIMITE_TEMP_MAX
            global LIMITE_UMIDADE_MIN, LIMITE_UMIDADE_MAX

            print("\n--- Alterar Limites ---")

            try:
                tmin = input(f"Temp. mínima ({LIMITE_TEMP_MIN}): ")
                tmax = input(f"Temp. máxima ({LIMITE_TEMP_MAX}): ")
                umin = input(f"Umidade mínima ({LIMITE_UMIDADE_MIN}): ")
                umax = input(f"Umidade máxima ({LIMITE_UMIDADE_MAX}): ")

                if tmin: LIMITE_TEMP_MIN = float(tmin)
                if tmax: LIMITE_TEMP_MAX = float(tmax)
                if umin: LIMITE_UMIDADE_MIN = float(umin)
                if umax: LIMITE_UMIDADE_MAX = float(umax)

                print("Limites atualizados!")

            except ValueError:
                print("Valores inválidos. Nenhuma alteração feita.")

        # ------------------------------------------------------------------
        # 6) SAIR
        # ------------------------------------------------------------------
        elif opcao == "6":
            print("Encerrando...")
            break

        else:
            print("Opção inválida.")


# Executa o sistema
if __name__ == "__main__":
    main()
