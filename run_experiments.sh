#!/usr/bin/env bash
# ==============================================================================
# Script de Execucao dos Experimentos de Desempenho com Locust
# Trabalho Pratico 06 - Sistemas Distribuidos
# Spring PetClinic Microservices
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores para saida no terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}   Trabalho Prático 06 - Avaliação de Desempenho com Locust       ${NC}"
echo -e "${BLUE}   Spring PetClinic Microservices                                 ${NC}"
echo -e "${BLUE}==================================================================${NC}"

# 1. Verifica se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[!] Ambiente virtual não encontrado. Criando venv e instalando dependências...${NC}"
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# 2. Verifica se a aplicação está rodando no Docker
echo -e "${BLUE}[*] Verificando status dos microsserviços PetClinic...${NC}"
if ! curl -s -f http://localhost:8080/api/vet/vets > /dev/null 2>&1; then
    echo -e "${YELLOW}[!] PetClinic não responde em http://localhost:8080.${NC}"
    echo -e "${BLUE}[*] Iniciando microsserviços via Docker Compose...${NC}"
    docker compose up -d
    echo -e "${YELLOW}[*] Aguardando 30 segundos para inicialização dos serviços e registro no Eureka...${NC}"
    sleep 30
fi

# Valida se agora responde
if curl -s -f http://localhost:8080/api/vet/vets > /dev/null 2>&1; then
    echo -e "${GREEN}[OK] API Gateway ativo e respondendo com sucesso!${NC}"
else
    echo -e "${RED}[ERRO] Não foi possível conectar ao API Gateway em http://localhost:8080.${NC}"
    echo -e "${RED}Verifique os logs dos containers com 'docker compose logs'.${NC}"
    exit 1
fi

# 3. Executa opcao selecionada
if [ "$1" == "--plots-only" ]; then
    echo -e "${BLUE}[*] Regenerando gráficos e tabelas a partir dos resultados existentes...${NC}"
    ./venv/bin/python3 generate_plots.py
    echo -e "${GREEN}[OK] Gráficos e tabelas atualizados em results/!${NC}"
    exit 0
fi

echo -e "${GREEN}[*] Iniciando orquestrador de experimentos...${NC}"
./venv/bin/python3 run_experiments.py "$@"

echo -e "\n${GREEN}==================================================================${NC}"
echo -e "${GREEN}[SUCESSO] Bateria de testes concluída com sucesso!${NC}"
echo -e "${GREEN}Resultados salvos na pasta 'results/':${NC}"
echo -e " - CSVs brutos:       results/raw/"
echo -e " - Resumo agregado:   results/aggregated_summary.csv"
echo -e " - Gráficos gerados:  results/charts/"
echo -e " - Tabelas Markdown:  results/tables/"
echo -e "${GREEN}==================================================================${NC}"
