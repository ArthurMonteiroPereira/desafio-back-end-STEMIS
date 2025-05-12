from datetime import datetime
from app.core.database import SessionLocal, ajustar_sequencias
from app.models import Medicao, Inversor, Usina

def processa_ingestao(dados):
    db = SessionLocal()
    try:
        # Descobrir usinas e inversores usados no arquivo
        inversor_ids = set()
        usinas_info = {}
        for m in dados:
            if 'inversor_id' in m:
                inversor_ids.add(m['inversor_id'])
            if 'usina_id' in m:
                usinas_info[m['usina_id']] = m.get('usina_nome', f'Usina {m["usina_id"]}')
        # Criar usinas dinamicamente
        for usina_id, usina_nome in usinas_info.items():
            if not db.query(Usina).filter_by(id=usina_id).first():
                db.add(Usina(id=usina_id, nome=usina_nome, localizacao=f'Local {usina_id}'))
        db.commit()
        # Criar inversores dinamicamente
        for inversor_id in inversor_ids:
            if not db.query(Inversor).filter_by(id=inversor_id).first():
                # Tenta descobrir usina_id do inversor no arquivo
                usina_id = None
                for m in dados:
                    if m.get('inversor_id') == inversor_id and 'usina_id' in m:
                        usina_id = m['usina_id']
                        break
                if usina_id is None:
                    usina_id = 1  # fallback se não houver info
                db.add(Inversor(id=inversor_id, nome=f'Inversor {inversor_id}', modelo='Modelo X', usina_id=usina_id))
        db.commit()
        # Inserir medições
        medicoes = []
        for m in dados:
            if (
                'inversor_id' not in m or
                'datetime' not in m or
                '$date' not in m['datetime']
            ):
                print(f"Registro ignorado (dados faltando): {m}")
                continue
            medicoes.append(Medicao(
                inversor_id=m['inversor_id'],
                timestamp=datetime.fromisoformat(m['datetime']['$date'].replace('Z', '+00:00')),
                potencia_ativa=m.get('potencia_ativa_watt'),
                temperatura=m.get('temperatura_celsius')
            ))
        db.bulk_save_objects(medicoes)
        db.commit()
        # Ajustar sequências após ingestão
        ajustar_sequencias()
        print(f"{len(medicoes)} medições inseridas com sucesso.")
    except Exception as e:
        print(f"Erro ao processar ingestão: {e}")
    finally:
        db.close() 