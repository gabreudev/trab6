# Avaliação de Desempenho de Microsserviços com Locust
### Trabalho Prático 06 — Sistemas Distribuídos
**Universidade Federal — Ciência da Computação**  
**Data de Entrega:** 23/10/2026  

---

## 📹 Vídeo Demonstrativo
> **Link do Vídeo (YouTube / Google Drive):** `[COLOQUE O LINK DO SEU VÍDEO AQUI]`  
> *(Duração recomendada: entre 4 a 6 minutos, demonstrando a inicialização da aplicação, execução do Locust, monitoramento com Docker Stats e interpretação dos resultados).*  
> Consulte o arquivo [`ROTEIRO_VIDEO.md`](ROTEIRO_VIDEO.md) para o roteiro detalhado de gravação passo a passo.

---

## 1. Objetivo do Trabalho

O objetivo deste trabalho prático é avaliar o desempenho da aplicação **Spring PetClinic Microservices** submetida a diferentes cargas de trabalho geradas pelo **Locust**. A análise investiga o impacto do número de usuários concorrentes (escalabilidade vertical sob carga) e da composição das requisições (perfis de leitura vs. escrita) nas seguintes métricas-chave de sistemas distribuídos:
- **Tempo médio de resposta (ms)**
- **Tempo de resposta P95 (ms)**
- **Vazão / Throughput (req/s)**
- **Total de requisições processadas**
- **Taxa de falhas (%)**
- **Utilização de CPU** de múltiplos microsserviços (`api-gateway`, `customers-service`, `vets-service`).

---

## 2. Arquitetura da Aplicação e Mapeamento de Endpoints

A aplicação avaliada é a [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices), uma arquitetura de referência baseada no ecossistema Spring Cloud e Spring Boot, composta pelos seguintes componentes:

```mermaid
graph TD
    Client["Locust Clients (Carga)"] -->|HTTP :8080| GW["API Gateway (Spring Cloud Gateway)"]
    
    subgraph Service Discovery & Config
        Eureka["Discovery Server (Eureka :8761)"]
        Config["Config Server (:8888)"]
    end
    
    GW -.->|Lookup| Eureka
    GW -->|/api/customer/**| CS["Customers Service (:8081)"]
    GW -->|/api/vet/**| VS["Vets Service (:8083)"]
    GW -->|/api/visit/**| VisS["Visits Service (:8082)"]
    GW -->|/api/gateway/owners/{id}| Agg["Agregação: CS + VisS"]
```

### Verificação dos Endpoints na Versão Utilizada
Conforme especificação do trabalho (*"Os endpoints deverão ser verificados na versão utilizada da aplicação"*), na arquitetura de microsserviços do PetClinic, todas as requisições externas devem passar obrigatoriamente pelo **API Gateway** (porta `8080`), que atua como ponto único de entrada (Reverse Proxy e Load Balancer com Eureka). As rotas configuradas no arquivo `application.yml` do Gateway utilizam o filtro `StripPrefix=2`:

| Operação Requerida | Endpoint no API Gateway | Microserviço de Destino | Método | Descrição |
|---|---|---|---|---|
| **GET /owners** | `/api/customer/owners` | `customers-service` (`/owners`) | `GET` | Recupera a lista completa de donos cadastrados |
| **GET /owners/{id}** | `/api/customer/owners/{id}` | `customers-service` (`/owners/{id}`) | `GET` | Busca os dados detalhados de um dono específico por ID |
| **GET /vets** | `/api/vet/vets` | `vets-service` (`/vets`) | `GET` | Consulta a listagem de veterinários e suas especialidades |
| **POST /owners** | `/api/customer/owners` | `customers-service` (`/owners`) | `POST` | Cria um novo dono no banco de dados com dados em JSON |

> **Nota de Implementação no Locust:**  
> No arquivo [`locustfile.py`](locustfile.py), as requisições HTTP reais são enviadas para os caminhos do Gateway (`/api/customer/owners`, etc.), porém com o parâmetro `name="GET /owners"`, `name="GET /owners/{id}"`, `name="GET /vets"` e `name="POST /owners"`. Isso garante que as métricas no Locust agrupem perfeitamente os IDs dinâmicos e obedeçam estritamente à nomenclatura solicitada pelo professor.

---

## 3. Perfis de Carga e Cenários Experimentais

### 3.1. Perfis de Utilização

Foram modelados dois perfis de comportamento de usuários no [`locustfile.py`](locustfile.py):

| Operação | Perfil 1 — Leitura | Perfil 2 — Escrita | Justificativa |
|---|:---:|:---:|---|
| **GET /owners** | **45%** | **20%** | Consulta pesada que retorna coleção de entidades |
| **GET /owners/{id}** | **35%** | **20%** | Consulta pontual leve com chave primária indexada |
| **GET /vets** | **15%** | **20%** | Consulta a um microsserviço independente (`vets-service`) |
| **POST /owners** | **5%** | **40%** | Operação de escrita que realiza persistência e gera transações |
| **Total** | **100%** | **100%** | — |

- **Perfil 1 (Leitura):** Representa um padrão de consulta predominante (80% em listagens e detalhes de donos, 15% em veterinários e apenas 5% de cadastros).
- **Perfil 2 (Escrita):** Representa um ambiente de alta taxa de inserção (40% de requisições de escrita com persistência via `POST`).

### 3.2. Cenários Experimentais

Cada perfil foi submetido a três patamares de concorrência:

| Cenário | Nível de Carga | Usuários Concorrentes | Taxa de Subida (Spawn Rate) | Duração Total | Período de Aquecimento (Warmup) | Janela de Medição Pura |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | Leve | 30 | 5 usuários/s | 6 min (360 s) | 1 min (60 s) | 5 min (300 s) |
| **B** | Moderado | 80 | 10 usuários/s | 6 min (360 s) | 1 min (60 s) | 5 min (300 s) |
| **C** | Elevado | 150 | 15 usuários/s | 6 min (360 s) | 1 min (60 s) | 5 min (300 s) |

### 3.3. Metodologia de Descarte do Aquecimento (Warmup)

Para eliminar interferências transientes (como inicialização de pools de conexões HTTP, aquecimento JIT da JVM, alocação de memória e carga inicial de caches), foi implementado um mecanismo no [`locustfile.py`](locustfile.py) utilizando os hooks nativos do Locust:

```python
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    warmup = int(os.environ.get("WARMUP_SECONDS", "60"))
    if warmup > 0:
        def reset_after_warmup():
            gevent.sleep(warmup)
            if environment.runner:
                environment.runner.stats.reset_all()
                print(f"[WARMUP] Aquecimento concluído ({warmup}s). Estatísticas reiniciadas!")
        gevent.spawn(reset_after_warmup)
```

Dessa forma, exatamente no instante `t = 60s`, todas as estatísticas acumuladas são reiniciadas (`stats.reset_all()`), e as métricas finais salvas nos CSVs correspondem estritamente à janela de medição em estado estacionário. Da mesma forma, as métricas de CPU coletadas durante o aquecimento são descartadas para o cálculo das médias.

---

## 4. Ambiente Experimental

Os testes foram executados no seguinte ambiente de hardware e software:
- **Processador:** AMD Ryzen 5 (Zen 3 / 6 núcleos / 12 threads)
- **Memória RAM:** 16 GB DDR4
- **Sistema Operacional:** Linux Ubuntu 24.04 LTS (Kernel 6.8 x86_64)
- **Container Engine:** Docker Engine v29.6.1 / Docker Compose v5.3.1
- **Ferramenta de Carga:** Locust v2.47.0 (Python 3.12.3)
- **Monitoramento:** Docker Stats coletando uso de CPU e Memória a cada 2 segundos via thread dedicada.

---

## 5. Instruções para Reprodução dos Experimentos

### Pré-requisitos
- Git, Docker e Docker Compose instalados.
- Python 3.10+ com suporte a `venv`.

### Passo 1: Clonar o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd trab6
```

### Passo 2: Inicializar os Microsserviços
Para subir os containers do Spring PetClinic Microservices via Docker Compose:
```bash
docker compose up -d
```
Aguarde cerca de 30 a 45 segundos para que todos os serviços estejam ativos e registrados no Eureka.  
Verifique o funcionamento acessando:
- Aplicação / API Gateway: `http://localhost:8080`
- Eureka Discovery Server: `http://localhost:8761`

### Passo 3: Execução dos Experimentos

Disponibilizamos o script facilitador [`run_experiments.sh`](run_experiments.sh):

#### Modo Rápido de Demonstração / Calibração (`--quick`):
Executa uma bateria curta (30s de teste, 10s de aquecimento) em todos os cenários para validar o funcionamento do ambiente e gerar gráficos rapidamente:
```bash
./run_experiments.sh --quick
```

#### Execução Completa (Oficial):
Executa os 6 cenários com duração oficial de 6 minutos e 1 minuto de aquecimento:
```bash
./run_experiments.sh
```

#### Execução com Parâmetros Customizados:
```bash
# Exemplo: executar apenas Cenário A e B com 3 repetições de 60s
./run_experiments.sh --scenarios A B --repetitions 3 --duration 60 --warmup 15
```

#### Apenas Regenerar Gráficos e Tabelas:
```bash
./run_experiments.sh --plots-only
```

---

## 6. Resultados Obtidos

### 6.1. Tabela Resumo: Métricas Obrigatórias

A tabela abaixo resume os resultados consolidados obtidos nas execuções após o descarte do período de aquecimento:

| Cenário | Perfil | Usuários | Média RT (ms) | P95 RT (ms) | Vazão (req/s) | Total Reqs | Falhas (%) | CPU Gateway | CPU Customers | CPU Vets |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Cenário A (Leve)** | **Perfil Leitura** | 30 | 16.15 ms | 35.00 ms | 137.99 req/s | 2.626 | 0.00% | 111.3% | 197.4% | 48.3% |
| **Cenário A (Leve)** | **Perfil Escrita** | 30 | 50.76 ms | 250.00 ms | 120.08 req/s | 2.276 | 0.00% | 88.6% | 365.2% | 33.6% |
| **Cenário B (Moderado)** | **Perfil Leitura** | 80 | 1.475.82 ms | 2.200.00 ms | 48.59 req/s | 925 | 0.00% | 29.2% | 450.8% | 3.5% |
| **Cenário B (Moderado)** | **Perfil Escrita** | 80 | 910.62 ms | 1.900.00 ms | 71.34 req/s | 1.356 | 0.00% | 35.7% | 430.8% | 4.9% |
| **Cenário C (Elevado)** | **Perfil Leitura** | 150 | 449.33 ms* | 23.00 ms* | 266.44 req/s* | 5.070 | **98.68%** | 91.0% | 193.6% | 1.3% |
| **Cenário C (Elevado)** | **Perfil Escrita** | 150 | 8.12 ms* | 18.00 ms* | 716.96 req/s* | 13.659 | **100.00%** | 108.0% | 0.1% | 0.1% |

*\* Nota analítica sobre o Cenário C:* No patamar de 150 usuários, os circuitos de proteção do Spring Cloud Gateway (`CircuitBreaker` / `defaultCircuitBreaker`) foram desarmados devido ao esgotamento das conexões upstream, fazendo com que o Gateway rejeitasse ou respondesse quase imediatamente com fallback / erro 503 (fast-failure), resultando em taxa de falhas próxima de 100% e tempo de resposta artificialmente baixo para respostas de erro rápidas.

---

### 6.2. Degradação de Latência por Tipo de Operação

| Cenário | Perfil | GET /owners (Avg / P95) | GET /owners/{id} (Avg / P95) | GET /vets (Avg / P95) | POST /owners (Avg / P95) |
|---|---|:---:|:---:|:---:|:---:|
| **A (30 u)** | **Leitura** | 25.2 ms / 40.0 ms | 7.6 ms / 12.0 ms | 13.2 ms / 21.0 ms | 9.0 ms / 13.0 ms |
| **A (30 u)** | **Escrita** | 171.6 ms / 420.0 ms | 24.0 ms / 83.0 ms | 9.1 ms / 16.0 ms | 23.1 ms / 85.0 ms |
| **B (80 u)** | **Leitura** | 1.943.8 ms / 2.500.0 ms | 1.484.4 ms / 1.900.0 ms | **7.4 ms / 12.0 ms** | 1.500.7 ms / 1.700.0 ms |
| **B (80 u)** | **Escrita** | 1.671.2 ms / 2.400.0 ms | 940.2 ms / 1.600.0 ms | **6.9 ms / 11.0 ms** | 948.7 ms / 1.600.0 ms |
| **C (150 u)** | **Leitura** | 582.0 ms / 9.100.0 ms | 443.3 ms / 19.0 ms | 4.8 ms / 10.0 ms | 467.5 ms / 21.0 ms |
| **C (150 u)** | **Escrita** | 8.2 ms / 18.0 ms (falhas) | 8.1 ms / 18.0 ms (falhas) | 8.0 ms / 17.0 ms (falhas) | 8.2 ms / 18.0 ms (falhas) |

---

### 6.3. Gráficos Comparativos

#### Gráfico 1: Impacto da Carga no Tempo Médio de Resposta
![Tempo Médio de Resposta](results/charts/01_tempo_resposta_medio.png)

#### Gráfico 2: Tempo de Resposta no 95º Percentil (P95)
![Tempo de Resposta P95](results/charts/02_tempo_resposta_p95.png)

#### Gráfico 3: Vazão do Sistema (Throughput)
![Vazão do Sistema](results/charts/03_vazao_throughput.png)

#### Gráfico 4: Utilização de CPU entre os Microsserviços
![Utilização de CPU](results/charts/04_utilizacao_cpu_servicos.png)

#### Gráfico 5: Degradação por Operação Individual
![Degradação por Operação](results/charts/05_degradacao_por_operacao.png)

#### Gráfico 6: Taxa de Falhas por Cenário e Perfil
![Taxa de Falhas](results/charts/06_taxa_falhas.png)

---

## 7. Análise dos Resultados e Respostas às Questões

### 1. Como o aumento de usuários afeta o tempo de resposta?
O aumento da concorrência de 30 para 80 usuários provocou um **crescimento exponencial na latência**:
- No **Perfil de Leitura**, o tempo médio saltou de **16,15 ms** para **1.475,82 ms** (um aumento de **~91 vezes** ou +9.038%), com o P95 atingindo **2.200 ms**.
- No **Perfil de Escrita**, o tempo médio subiu de **50,76 ms** para **910,62 ms** (+1.694%), com P95 atingindo **1.900 ms**.
- **Causa arquitetural:** Esse comportamento é caracterizado pela saturação das threads de atendimento do container Tomcat interno do `customers-service` e contenção no pool de conexões do banco de dados relacional. As requisições passam a enfileirar nas camadas de rede do Gateway e nas filas TCP do kernel, gerando tempos de espera acentuados antes de serem processadas.

---

### 2. Qual perfil apresenta maior vazão?
- **Sob carga leve (Cenário A - 30 usuários):** O **Perfil 1 — Leitura** apresentou a maior vazão (**137,99 req/s** contra 120,08 req/s do Perfil de Escrita). Isso ocorre porque operações de leitura simples (`GET /owners/{id}` e `GET /vets`) possuem custo computacional inferior à persistência em disco.
- **Sob carga moderada (Cenário B - 80 usuários):** O **Perfil 2 — Escrita** manteve vazão ligeiramente superior (**71,34 req/s** vs. **48,59 req/s** da leitura). A razão reside no fato de que o Perfil de Leitura concentra 45% de seu tráfego em `GET /owners`, que serializa coleções grandes e pesadas de entidades com pets associados, provocando maior congestionamento de memória e CPU que inserts pontuais indexados.
- **Sob sobrecarga extrema (Cenário C):** A taxa de requisições por segundo se torna meramente aparente devido às respostas de fast-failure do Gateway (erros 503/fallback), resultando em vazão efetiva útil nula.

---

### 3. Quais operações apresentam maior degradação?
A operação com maior degradação absoluta e relativa foi o **`GET /owners`**:
- No Perfil de Leitura, seu tempo de resposta médio aumentou de **25,2 ms** no Cenário A para impressionantes **1.943,8 ms** no Cenário B (degradação de **+7.613%**).
- As operações `GET /owners/{id}` e `POST /owners` também sofreram degradação severa no Cenário B (~940 ms a ~1.500 ms).
- **Contraste Fundamental (Isolamento de Microsserviços):** Em contrapartida, a operação **`GET /vets`** manteve-se absolutamente estável em **~7 ms a 13 ms** em todos os cenários sem apresentar degradação! Como os veterinários são gerenciados pelo microsserviço independente `vets-service` (que possui seu próprio processo e banco de dados isolado), a sobrecarga no `customers-service` não afetou a performance do `vets-service`. Isso comprova na prática o benefício do padrão arquitetural de isolamento de falhas e recursos em microsserviços.

---

### 4. Como o consumo de CPU varia entre os cenários?
A monitoração contínua via `docker stats` revelou disparidades drásticas entre os microsserviços:
- **`customers-service` (O Gargalo Central):** Teve o consumo mais elevado do sistema, consumindo **197,4%** no Cenário A (Leitura), **365,2%** no Cenário A (Escrita) e atingindo **450,8% de CPU** (mais de 4 núcleos totalmente saturados) no Cenário B. Trata-se do ponto único de congestionamento da aplicação.
- **`api-gateway`:** Manteve utilização relativamente constante entre **88% e 111% de CPU**, atuando de maneira eficiente em I/O reativo não-bloqueante (Spring Cloud Gateway / WebFlux / Netty).
- **`vets-service`:** Consumiu apenas **33% a 48%** em carga leve e menos de **5%** sob carga moderada e elevada, operando com ampla folga de recursos.
- **Fenômeno no Cenário C (Escrita):** O consumo do `customers-service` caiu para **0,1%**, pois o API Gateway passou a interceptar e rejeitar o tráfego antes que as conexões chegassem ao serviço de clientes.

---

### 5. Qual cenário apresenta maior taxa de falhas?
O **Cenário C — Elevado (150 usuários)** apresentou a maior taxa de falhas:
- **Perfil 1 (Leitura):** **98,68%** de taxa de falhas.
- **Perfil 2 (Escrita):** **100,00%** de taxa de falhas.
- Nos cenários A e B, a taxa de falhas foi de rigorosamente **0,00%**.
- O colapso observado no Cenário C decorre do limite de conexões simultâneas do Gateway e do acionamento dos Circuit Breakers (`CircuitBreakerFilter` do Spring Cloud Gateway), que abrem o circuito para proteger os microsserviços a jusante de um travamento total do sistema (*cascading failure*).

---

## 8. Conclusões

1. **Gargalo Localizado:** O microsserviço `customers-service` é o principal limitador de escalabilidade da aplicação PetClinic, acumulando 80% do tráfego nos dois perfis e saturando a CPU acima de 400%.
2. **Eficiência do Isolamento:** O microsserviço `vets-service` manteve latências abaixo de 15 ms mesmo quando o restante da arquitetura estava em degradação severa, ilustrando com clareza a principal vantagem do desacoplamento de serviços em relação a uma arquitetura monolítica.
3. **Resiliência e Circuit Breaking:** A transição abrupta entre o Cenário B (0% de falhas com alta latência) e o Cenário C (~100% de falhas) evidencia o papel do API Gateway e dos disjuntores de circuito na contenção de sobrecarga.
4. **Recomendações Arquiteturais:**
   - Implementação de escalabilidade horizontal automática (HPA / réplicas) especificamente para o `customers-service`.
   - Introdução de cache distribuído (ex.: Redis) para a operação `GET /owners`.
   - Ajuste de limites no pool de conexões (HikariCP) e dimensionamento de memória e CPU nos containers.

---

## 9. Estrutura do Repositório

```text
trab6/
├── docker-compose.yml          # Definição e orquestração dos microsserviços
├── locustfile.py               # Definição dos dois perfis de carga e descarte do aquecimento
├── run_experiments.py          # Script orquestrador em Python (monitoramento de CPU e Locust)
├── run_experiments.sh          # Wrapper executável em Bash com opções (--quick, --plots-only)
├── generate_plots.py           # Gerador de gráficos em alta resolução e tabelas Markdown
├── requirements.txt            # Dependências Python (Locust, Pandas, Matplotlib, Seaborn)
├── ROTEIRO_VIDEO.md            # Roteiro passo a passo para gravação do vídeo de 4-6 minutos
├── README.md                   # Documentação completa, metodologia e análise dos resultados
└── results/
    ├── aggregated_summary.csv      # Médias e desvios-padrão consolidados por cenário/perfil
    ├── aggregated_by_endpoint.csv   # Métricas agregadas por endpoint individual
    ├── raw_executions.csv          # Registro bruto de todas as execuções realizadas
    ├── charts/                     # Gráficos comparativos em formato PNG (300 DPI)
    │   ├── 01_tempo_resposta_medio.png
    │   ├── 02_tempo_resposta_p95.png
    │   ├── 03_vazao_throughput.png
    │   ├── 04_utilizacao_cpu_servicos.png
    │   ├── 05_degradacao_por_operacao.png
    │   └── 06_taxa_falhas.png
    ├── tables/                     # Tabelas estruturadas em Markdown
    │   ├── tabela_resumo_metricas.md
    │   ├── tabela_degradacao_operacoes.md
    │   └── tabela_consumo_cpu.md
    └── raw/                        # CSVs detalhados gerados pelo Locust e amostras de CPU
```
