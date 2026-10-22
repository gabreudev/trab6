#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "results/raw_executions.csv" ]; then
    echo "Nenhuma execução registrada ainda."
    exit 0
fi

TOTAL_CONCLUIDAS=$(tail -n +2 results/raw_executions.csv | wc -l)
echo "=========================================================="
echo " Progresso dos Testes Oficiais: $TOTAL_CONCLUIDAS / 60 execuções"
echo "=========================================================="

echo -e "\nÚltimas 5 execuções finalizadas:"
./venv/bin/python3 -c "
import pandas as pd
df = pd.read_csv('results/raw_executions.csv')
cols = ['scenario', 'profile', 'repetition', 'throughput_rps', 'avg_response_time_ms', 'failure_rate_pct']
print(df[cols].tail(5).to_string(index=False))
"

echo -e "\nÚltimas linhas do log de execução em tempo real:"
tail -n 12 experiments.log
