from app.core.database import SessionLocal
from sqlalchemy import func, and_
from app.models import Medicao, Inversor, Usina
from datetime import datetime, timedelta
from utils import calc_inverters_generation, TimeSeriesValue
import os
import json
import glob
from typing import Optional, List, Dict, Any, Union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results_analises')
os.makedirs(RESULTS_DIR, exist_ok=True)

def salvar_resultado(tipo, parametros, resultado):
    nome = f"{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho = os.path.join(RESULTS_DIR, nome)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump({"tipo": tipo, "parametros": parametros, "resultado": resultado}, f, ensure_ascii=False, indent=2)
    print(f"Arquivo de análise salvo em: {caminho}")
    return nome

def listar_resultados_analises(tipo: Optional[str] = None, usina_id: Optional[int] = None, 
                             inversor_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Lista todos os resultados de análises disponíveis, com filtros opcionais"""
    arquivos = glob.glob(os.path.join(RESULTS_DIR, "*.json"))
    resultados = []
    
    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            # Aplicar filtros
            if tipo and dados.get("tipo") != tipo:
                continue
                
            parametros = dados.get("parametros", {})
            if usina_id and parametros.get("usina_id") != usina_id:
                continue
                
            if inversor_id and parametros.get("inversor_id") != inversor_id:
                continue
                
            # Adicionar nome do arquivo ao resultado
            resultados.append({
                "nome_arquivo": nome_arquivo,
                "tipo": dados.get("tipo"),
                "parametros": parametros,
                "data_analise": nome_arquivo.split("_")[-2] + "_" + nome_arquivo.split("_")[-1].split(".")[0]
            })
        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
    
    # Ordenar por data de criação (mais recente primeiro)
    resultados.sort(key=lambda x: x["data_analise"], reverse=True)
    return resultados

def obter_resultado_analise(nome_arquivo: str) -> Optional[Dict[str, Any]]:
    """Obtém o conteúdo de uma análise específica por nome de arquivo"""
    caminho = os.path.join(RESULTS_DIR, nome_arquivo)
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo {caminho}: {str(e)}")
            return None
    return None

def calcular_serie_temporal_geracao(db, inversor_id, data_inicio, data_fim):
    """
    Calcula a geração diária de um inversor para o período especificado.
    Retorna uma lista de dicionários com dia e geração.
    """
    # Primeira abordagem: calcular a geração dia a dia
    data_atual = data_inicio.date()
    data_fim_date = data_fim.date()
    serie_temporal = []
    
    while data_atual <= data_fim_date:
        # Calcular início e fim do dia
        dia_inicio = datetime.combine(data_atual, datetime.min.time())
        dia_fim = datetime.combine(data_atual, datetime.max.time())
        
        # Buscar medições do dia
        medicoes = db.query(Medicao).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= dia_inicio,
            Medicao.timestamp <= dia_fim
        ).order_by(Medicao.timestamp).all()
        
        # Calcular geração do dia
        power = [TimeSeriesValue(value=m.potencia_ativa, date=m.timestamp) for m in medicoes if m.potencia_ativa is not None]
        
        if power:
            entity = type('Entity', (), {'power': power})()
            geracao_dia = calc_inverters_generation([entity])
            
            # Adicionar à série temporal
            serie_temporal.append({
                "dia": data_atual.isoformat(),
                "geracao": geracao_dia
            })
        
        # Avançar para o próximo dia
        data_atual += timedelta(days=1)
    
    return serie_temporal

def calcular_serie_temporal_potencia_temperatura(db, inversor_id, data_inicio, data_fim):
    """
    Calcula a série temporal de potência máxima e temperatura média por dia para um inversor.
    """
    resultado = db.query(
        func.date(Medicao.timestamp).label('dia'),
        func.max(Medicao.potencia_ativa).label('potencia_maxima'),
        func.avg(Medicao.temperatura).label('temperatura_media')
    ).filter(
        Medicao.inversor_id == inversor_id,
        Medicao.timestamp >= data_inicio,
        Medicao.timestamp <= data_fim
    ).group_by(func.date(Medicao.timestamp)).all()
    
    # Formatar o resultado
    serie_temporal = []
    for r in resultado:
        serie_temporal.append({
            "dia": r.dia.isoformat(),
            "potencia_maxima": r.potencia_maxima,
            "temperatura_media": r.temperatura_media
        })
    
    return serie_temporal

def processa_potencia_maxima(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        result = db.query(
            func.date(Medicao.timestamp).label('dia'),
            func.max(Medicao.potencia_ativa).label('potencia_maxima')
        ).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).group_by(func.date(Medicao.timestamp)).all()
        print(f"Potência máxima por dia: {result}")
        salvar_resultado('potencia_maxima', parametros, [dict(dia=str(r.dia), potencia_maxima=r.potencia_maxima) for r in result])
    finally:
        db.close()

def processa_media_temperatura(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        result = db.query(
            func.date(Medicao.timestamp).label('dia'),
            func.avg(Medicao.temperatura).label('media_temperatura')
        ).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).group_by(func.date(Medicao.timestamp)).all()
        print(f"Média de temperatura por dia: {result}")
        salvar_resultado('media_temperatura', parametros, [dict(dia=str(r.dia), media_temperatura=r.media_temperatura) for r in result])
    finally:
        db.close()

def processa_geracao_usina(parametros):
    db = SessionLocal()
    try:
        usina_id = parametros['usina_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        inversores = db.query(Inversor.id).filter(Inversor.usina_id == usina_id).all()
        inversor_ids = [inv.id for inv in inversores]
        entities_with_power = []
        for inversor_id in inversor_ids:
            medicoes = db.query(Medicao).filter(
                Medicao.inversor_id == inversor_id,
                Medicao.timestamp >= data_inicio,
                Medicao.timestamp <= data_fim
            ).order_by(Medicao.timestamp).all()
            power = [TimeSeriesValue(value=m.potencia_ativa, date=m.timestamp) for m in medicoes if m.potencia_ativa is not None]
            if power:
                entities_with_power.append(type('Entity', (), {'power': power})())
        geracao_total = calc_inverters_generation(entities_with_power)
        print(f"Geração total da usina (kWh): {geracao_total}")
        salvar_resultado('geracao_usina', parametros, geracao_total)
    finally:
        db.close()

def processa_geracao_inversor(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        medicoes = db.query(Medicao).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).order_by(Medicao.timestamp).all()
        power = [TimeSeriesValue(value=m.potencia_ativa, date=m.timestamp) for m in medicoes if m.potencia_ativa is not None]
        entity = type('Entity', (), {'power': power})()
        geracao_total = calc_inverters_generation([entity])
        print(f"Geração total do inversor (kWh): {geracao_total}")
        salvar_resultado('geracao_inversor', parametros, geracao_total)
    finally:
        db.close()

def normalizar_serie_temporal(serie_temporal, data_inicio, data_fim, chaves_valores=None):
    """
    Normaliza uma série temporal, garantindo que todos os dias no intervalo estejam presentes.
    Para dias sem dados, os valores são preenchidos com zeros ou valores padrão.
    
    Args:
        serie_temporal: Lista de dicionários com chave 'dia' e outras chaves de valores
        data_inicio: Data de início no formato string 'YYYY-MM-DD'
        data_fim: Data de fim no formato string 'YYYY-MM-DD'
        chaves_valores: Dicionário com chaves e valores padrão para dias sem dados
        
    Returns:
        Lista normalizada de dicionários, um para cada dia no intervalo
    """
    # Converter datas para objetos date
    try:
        inicio = datetime.fromisoformat(data_inicio).date()
        fim = datetime.fromisoformat(data_fim).date()
    except ValueError:
        # Tenta converter apenas a parte da data
        inicio = datetime.fromisoformat(data_inicio.split('T')[0]).date()
        fim = datetime.fromisoformat(data_fim.split('T')[0]).date()
    
    # Valores padrão se não fornecidos
    if chaves_valores is None:
        chaves_valores = {"geracao": 0, "potencia_maxima": 0, "temperatura_media": 0}
    
    # Criar dicionário com os dados existentes indexados por dia
    dados_por_dia = {}
    for item in serie_temporal:
        dia = item.get('dia')
        # Converter para formato ISO padrão se for uma data
        if isinstance(dia, datetime):
            dia = dia.date().isoformat()
        elif isinstance(dia, str):
            # Remover parte de hora se existir
            dia = dia.split('T')[0] if 'T' in dia else dia
        
        dados_por_dia[dia] = item
    
    # Criar série normalizada
    serie_normalizada = []
    data_atual = inicio
    
    while data_atual <= fim:
        dia_str = data_atual.isoformat()
        if dia_str in dados_por_dia:
            # Se o dia existe na série original, usar esses dados
            serie_normalizada.append(dados_por_dia[dia_str])
        else:
            # Se o dia não existe, criar um item com valores padrão
            item_padrao = {"dia": dia_str}
            for chave, valor in chaves_valores.items():
                item_padrao[chave] = valor
            serie_normalizada.append(item_padrao)
        
        # Avançar para o próximo dia
        data_atual += timedelta(days=1)
    
    return serie_normalizada

def obter_dash_mais_recente():
    """
    Obtém os dados do dashboard mais recente
    """
    arquivos = glob.glob(os.path.join(RESULTS_DIR, "dash_*.json"))
    
    if not arquivos:
        return None
    
    # Ordenar por data mais recente (baseado no nome do arquivo)
    arquivos.sort(reverse=True)
    
    try:
        with open(arquivos[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler arquivo {arquivos[0]}: {str(e)}")
        return None

def processa_gerar_dash(parametros):
    """
    Processa a geração de todos os dados necessários para o dashboard em um único arquivo.
    Este processo é mais pesado, mas gera todos os dados de uma só vez.
    """
    print(f"Iniciando processamento do dashboard para o período: {parametros}")
    db = SessionLocal()
    try:
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        
        # Estrutura para armazenar o resultado completo
        resultado_dash = {
            "periodo": {
                "data_inicio": parametros['data_inicio'],
                "data_fim": parametros['data_fim']
            },
            "geracao_timestamp": datetime.now().isoformat(),
            "metricas_globais": {
                "geracao_total": 0,
                "potencia_maxima_total": 0,
                "temperatura_media_global": 0,
                "media_diaria_geracao": 0,
                "media_diaria_potencia": 0
            },
            "usinas": [],
            "serie_temporal_total": [],
            "serie_temporal_usinas": {}
        }
        
        # Buscar todas as usinas
        usinas = db.query(Usina).all()
        if not usinas:
            print("Nenhuma usina encontrada!")
            return salvar_resultado('dash', parametros, {
                "erro": "Nenhuma usina encontrada"
            })
            
        # Dicionário para acumular dados diários globais
        dados_diarios_global = {}
        total_inversores_com_temp = 0
        soma_temp_global = 0
        
        # Processar cada usina
        for usina in usinas:
            print(f"Processando usina {usina.id} - {usina.nome}")
            
            # Dados da usina
            dados_usina = {
                "id": usina.id,
                "nome": usina.nome,
                "localizacao": usina.localizacao,
                "metricas": {
                    "geracao_total": 0,
                    "potencia_maxima_total": 0,
                    "temperatura_media": 0,
                    "media_diaria_geracao": 0
                },
                "inversores": []
            }
            
            # Inicializar série temporal da usina
            resultado_dash["serie_temporal_usinas"][str(usina.id)] = []
            
            # Buscar inversores da usina
            inversores = db.query(Inversor).filter(Inversor.usina_id == usina.id).all()
            if not inversores:
                print(f"Nenhum inversor encontrado para a usina {usina.id}")
                dados_usina["erro"] = "Nenhum inversor encontrado"
                resultado_dash["usinas"].append(dados_usina)
                continue
                
            # Dicionário para acumular dados diários da usina
            dados_diarios_usina = {}
            inversores_com_temp = 0
            soma_temp_usina = 0
            
            # Processar cada inversor
            for inversor in inversores:
                print(f"Processando inversor {inversor.id} - {inversor.nome}")
                
                # Dados do inversor
                dados_inversor = {
                    "id": inversor.id,
                    "nome": inversor.nome,
                    "modelo": inversor.modelo,
                    "metricas": {}
                }
                
                # 1. Potência máxima
                potencia_max = db.query(func.max(Medicao.potencia_ativa).label('max_pot')).filter(
                    Medicao.inversor_id == inversor.id,
                    Medicao.timestamp >= data_inicio,
                    Medicao.timestamp <= data_fim
                ).scalar() or 0
                dados_inversor["metricas"]["potencia_maxima"] = potencia_max
                dados_usina["metricas"]["potencia_maxima_total"] += potencia_max
                
                # 2. Temperatura média
                temp_media = db.query(func.avg(Medicao.temperatura).label('avg_temp')).filter(
                    Medicao.inversor_id == inversor.id,
                    Medicao.timestamp >= data_inicio,
                    Medicao.timestamp <= data_fim
                ).scalar() or 0
                
                if temp_media:
                    dados_inversor["metricas"]["temperatura_media"] = temp_media
                    soma_temp_usina += temp_media
                    inversores_com_temp += 1
                    
                    soma_temp_global += temp_media
                    total_inversores_com_temp += 1
                else:
                    dados_inversor["metricas"]["temperatura_media"] = 0
                
                # 3. Geração total (soma da geração diária)
                serie_temporal_geracao = calcular_serie_temporal_geracao(
                    db, inversor.id, data_inicio, data_fim
                )
                geracao_total_inversor = sum(item["geracao"] for item in serie_temporal_geracao)
                dados_inversor["metricas"]["geracao_total"] = geracao_total_inversor
                dados_usina["metricas"]["geracao_total"] += geracao_total_inversor
                
                # 4. Série temporal de potência e temperatura
                serie_temporal_pot_temp = calcular_serie_temporal_potencia_temperatura(
                    db, inversor.id, data_inicio, data_fim
                )
                
                # 5. Combinar e normalizar séries temporais
                serie_combinada = []
                dias_combinados = set()
                
                for item in serie_temporal_pot_temp:
                    dia = item['dia']
                    dias_combinados.add(dia)
                    item_combinado = {"dia": dia}
                    item_combinado.update(item)
                    serie_combinada.append(item_combinado)
                
                for item in serie_temporal_geracao:
                    dia = item['dia']
                    if dia in dias_combinados:
                        # Atualizar item existente
                        for i, item_existente in enumerate(serie_combinada):
                            if item_existente['dia'] == dia:
                                serie_combinada[i].update(item)
                                break
                    else:
                        # Adicionar novo item
                        item_combinado = {"dia": dia, "geracao": item['geracao']}
                        serie_combinada.append(item_combinado)
                
                # Normalizar a série (incluir todos os dias do período)
                serie_normalizada = normalizar_serie_temporal(
                    serie_combinada,
                    parametros['data_inicio'],
                    parametros['data_fim'],
                    {"geracao": 0, "potencia_maxima": 0, "temperatura_media": 0}
                )
                
                dados_inversor["serie_temporal"] = serie_normalizada
                
                # 6. Acumular dados diários para usina e global
                for item in serie_normalizada:
                    dia = item['dia']
                    
                    # Acumular para usina
                    if dia not in dados_diarios_usina:
                        dados_diarios_usina[dia] = {
                            "geracao": 0,
                            "potencia_maxima": 0,
                            "temperaturas": [],
                            "inversores_com_temp": 0
                        }
                    
                    # Acumular para global
                    if dia not in dados_diarios_global:
                        dados_diarios_global[dia] = {
                            "geracao": 0,
                            "potencia_maxima": 0,
                            "temperaturas": [],
                            "inversores_com_temp": 0,
                            "usinas": {}
                        }
                    
                    # Inicializar contagem para esta usina no global
                    if str(usina.id) not in dados_diarios_global[dia]["usinas"]:
                        dados_diarios_global[dia]["usinas"][str(usina.id)] = {
                            "geracao": 0,
                            "potencia_maxima": 0,
                            "temperatura_media": 0,
                            "nome": usina.nome
                        }
                    
                    # Transferir dados de geração
                    if 'geracao' in item and item['geracao'] > 0:
                        dados_diarios_usina[dia]["geracao"] += item['geracao']
                        dados_diarios_global[dia]["geracao"] += item['geracao']
                        dados_diarios_global[dia]["usinas"][str(usina.id)]["geracao"] += item['geracao']
                    
                    # Transferir dados de potência
                    if 'potencia_maxima' in item and item['potencia_maxima'] > 0:
                        dados_diarios_usina[dia]["potencia_maxima"] += item['potencia_maxima']
                        dados_diarios_global[dia]["potencia_maxima"] += item['potencia_maxima']
                        dados_diarios_global[dia]["usinas"][str(usina.id)]["potencia_maxima"] += item['potencia_maxima']
                    
                    # Transferir dados de temperatura
                    if 'temperatura_media' in item and item['temperatura_media'] > 0:
                        dados_diarios_usina[dia]["temperaturas"].append(item['temperatura_media'])
                        dados_diarios_usina[dia]["inversores_com_temp"] += 1
                        
                        dados_diarios_global[dia]["temperaturas"].append(item['temperatura_media'])
                        dados_diarios_global[dia]["inversores_com_temp"] += 1
                
                # Adicionar dados deste inversor à usina
                dados_usina["inversores"].append(dados_inversor)
            
            # Calcular temperatura média da usina
            if inversores_com_temp > 0:
                dados_usina["metricas"]["temperatura_media"] = soma_temp_usina / inversores_com_temp
            
            # Gerar série temporal da usina
            serie_temporal_usina = []
            for dia, dados in sorted(dados_diarios_usina.items()):
                temp_media_dia = 0
                if dados["inversores_com_temp"] > 0:
                    temp_media_dia = sum(dados["temperaturas"]) / dados["inversores_com_temp"]
                
                # Adicionar à série temporal da usina
                serie_temporal_usina.append({
                    "dia": dia,
                    "geracao": dados["geracao"],
                    "potencia_maxima": dados["potencia_maxima"],
                    "temperatura_media": temp_media_dia
                })
            
            # Ordenar série temporal da usina
            serie_temporal_usina.sort(key=lambda x: x['dia'])
            
            # Calcular média diária da usina
            total_dias_com_geracao = len([d for d in serie_temporal_usina if d["geracao"] > 0])
            if total_dias_com_geracao > 0:
                dados_usina["metricas"]["media_diaria_geracao"] = dados_usina["metricas"]["geracao_total"] / total_dias_com_geracao
            
            # Adicionar série temporal à usina
            resultado_dash["serie_temporal_usinas"][str(usina.id)] = serie_temporal_usina
            
            # Atualizar totais globais
            resultado_dash["metricas_globais"]["geracao_total"] += dados_usina["metricas"]["geracao_total"]
            resultado_dash["metricas_globais"]["potencia_maxima_total"] += dados_usina["metricas"]["potencia_maxima_total"]
            
            # Adicionar dados desta usina ao resultado final
            resultado_dash["usinas"].append(dados_usina)
        
        # Calcular temperatura média global
        if total_inversores_com_temp > 0:
            resultado_dash["metricas_globais"]["temperatura_media_global"] = soma_temp_global / total_inversores_com_temp
        
        # Gerar série temporal global
        serie_temporal_global = []
        for dia, dados in sorted(dados_diarios_global.items()):
            temp_media_dia = 0
            if dados["inversores_com_temp"] > 0:
                temp_media_dia = sum(dados["temperaturas"]) / dados["inversores_com_temp"]
            
            # Adicionar à série temporal global
            serie_temporal_global.append({
                "dia": dia,
                "geracao": dados["geracao"],
                "potencia_maxima": dados["potencia_maxima"],
                "temperatura_media": temp_media_dia,
                "usinas": dados["usinas"]
            })
        
        # Ordenar série temporal global
        serie_temporal_global.sort(key=lambda x: x['dia'])
        resultado_dash["serie_temporal_total"] = serie_temporal_global
        
        # Calcular médias diárias globais
        total_dias_com_geracao = len([d for d in serie_temporal_global if d["geracao"] > 0])
        if total_dias_com_geracao > 0:
            resultado_dash["metricas_globais"]["media_diaria_geracao"] = resultado_dash["metricas_globais"]["geracao_total"] / total_dias_com_geracao
            resultado_dash["metricas_globais"]["media_diaria_potencia"] = resultado_dash["metricas_globais"]["potencia_maxima_total"] / total_dias_com_geracao
        
        # Salvar o resultado final
        print(f"Dashboard gerado com sucesso para o período {parametros['data_inicio']} a {parametros['data_fim']}")
        nome_arquivo = f"dash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        caminho = os.path.join(RESULTS_DIR, nome_arquivo)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(resultado_dash, f, ensure_ascii=False, indent=2)
        print(f"Dashboard salvo em: {caminho}")
        
        return nome_arquivo
    except Exception as e:
        print(f"Erro ao gerar dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        salvar_resultado('dash_error', parametros, {"erro": str(e)})
        return None
    finally:
        db.close() 