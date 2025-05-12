import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, create_tables
from app.models import Usina, Inversor, Medicao

# Caminho do arquivo de métricas
METRICS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sample/metrics.json'))

def main():
    create_tables()  # Garante que as tabelas existem
    db: Session = SessionLocal()
    try:
        with open(METRICS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Cria usinas (fixo conforme README)
        usinas = [
            Usina(id=1, nome='Usina 1', localizacao='Local 1'),
            Usina(id=2, nome='Usina 2', localizacao='Local 2'),
        ]
        for usina in usinas:
            if not db.query(Usina).filter_by(id=usina.id).first():
                db.add(usina)
        db.commit()

        # Cria inversores (IDs 1-4 para Usina 1, 5-8 para Usina 2)
        inversores = [
            Inversor(id=i, nome=f'Inversor {i}', modelo='Modelo X', usina_id=1 if i <= 4 else 2)
            for i in range(1, 9)
        ]
        for inv in inversores:
            if not db.query(Inversor).filter_by(id=inv.id).first():
                db.add(inv)
        db.commit()

        # Cria medições
        medicoes = []
        for m in data:
            medicoes.append(Medicao(
                inversor_id=m['inversor_id'],
                timestamp=datetime.fromisoformat(m['datetime']['$date'].replace('Z', '+00:00')),
                potencia_ativa=m['potencia_ativa_watt'],
                temperatura=m.get('temperatura_celsius')
            ))
        db.bulk_save_objects(medicoes)
        db.commit()
        print(f"População concluída: {len(medicoes)} medições inseridas.")
    finally:
        db.close()

if __name__ == "__main__":
    main() 