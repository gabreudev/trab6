# Roteiro de Gravação do Vídeo Demonstrativo
### Trabalho Prático 06 — Sistemas Distribuídos
**Duração Alvo:** Entre 4 a 6 minutos  
**Critério Atendido:** *"Link de um vídeo demonstrativo (4 a 6 minutos), incluído no README.md, mostrando a aplicação, a execução do Locust, o monitoramento dos serviços e os resultados obtidos."*

---

## 🛠️ Preparação Prévia (Antes de Iniciar a Gravação)

1. **Janelas Abertas e Organizadas na Área de Trabalho:**
   - **Terminal 1:** Na pasta do projeto (`/home/gabriel/Documentos/8periodo/sd/trab6`), com o comando pronto para mostrar containers e rodar o Locust.
   - **Terminal 2 (ou aba lado a lado):** Pronto com o comando de monitoramento:
     ```bash
     docker stats api-gateway customers-service vets-service
     ```
   - **Navegador Web:**
     - Aba 1: Aplicação Spring PetClinic (`http://localhost:8080`)
     - Aba 2: Eureka Discovery Server (`http://localhost:8761`)
     - Aba 3: Interface Web do Locust (`http://localhost:8089`) — opcional
     - Aba 4: O `README.md` renderizado no GitHub ou visualizador Markdown com os gráficos.
2. **Software de Gravação:** OBS Studio, SimpleScreenRecorder ou Gravador de Tela do GNOME (Ctrl + Alt + Shift + R).
3. **Microfone:** Teste o áudio antes de gravar. Fale de forma pausada, clara e confiante.

---

## ⏱️ Cronograma Passo a Passo do Vídeo

---

### [0:00 - 0:45] Bloco 1: Introdução e Apresentação do Ambiente
- **O que Mostrar na Tela:** O terminal com `docker ps` e o navegador na aba do PetClinic (`http://localhost:8080`).
- **O que Falar (Sugestão de Fala):**
  > *"Olá professor! Meu nome é Gabriel e esta é a apresentação do Trabalho Prático 06 da disciplina de Sistemas Distribuídos: Avaliação de Desempenho de Microsserviços com Locust.*  
  > *Aqui no terminal temos a aplicação Spring PetClinic Microservices rodando via Docker Compose. Os principais microsserviços em execução são o API Gateway na porta 8080, o Eureka Discovery Server na 8761, o Customers Service, Vets Service e Visits Service.*  
  > *No navegador podemos ver a interface web funcionando normalmente através do API Gateway, consultando donos e veterinários."*
- **Ação:** Clique em "Find Owners" e "Veterinarians" no navegador rapidamente para mostrar que o sistema está funcional e responsivo.

---

### [0:45 - 1:45] Bloco 2: Perfis de Carga e locustfile.py
- **O que Mostrar na Tela:** Abra o arquivo `locustfile.py` no VS Code ou terminal (`cat locustfile.py`).
- **O que Falar:**
  > *"Para atender aos requisitos do trabalho, implementamos no `locustfile.py` dois perfis de carga:*  
  > *O Perfil 1, voltado à Leitura, com 45% das requisições em GET /owners, 35% em GET /owners/{id}, 15% em GET /vets e 5% em POST /owners.*  
  > *E o Perfil 2, voltado à Escrita, com 40% de tráfego em POST /owners e 20% distribuídos igualmente entre as três operações de leitura.*  
  > *Como a aplicação utiliza Spring Cloud Gateway, os endpoints reais mapeados no Gateway são `/api/customer/owners`, `/api/customer/owners/{id}` e `/api/vet/vets`, e usamos o parâmetro `name` do Locust para manter a nomenclatura exata da especificação.*  
  > *Além disso, implementamos o listener `on_test_start` que aguarda o período de aquecimento configurado e executa `stats.reset_all()`, garantindo o descarte automático do primeiro minuto de aquecimento e registrando apenas o estado estacionário."*

---

### [1:45 - 3:00] Bloco 3: Execução do Locust e Monitoramento de CPU
- **O que Mostrar na Tela:** Tela dividida: lado esquerdo com o terminal rodando o teste, lado direito com o `docker stats`.
- **Ação:**
  1. No terminal da esquerda, execute o modo de demonstração rápida:
     ```bash
     ./run_experiments.sh --quick
     ```
  2. No terminal da direita, mostre o monitoramento em tempo real:
     ```bash
     docker stats api-gateway customers-service vets-service
     ```
- **O que Falar:**
  > *"Agora vamos demonstrar a execução do experimento com o nosso script orquestrador automatizado `run_experiments.sh`.*  
  > *Observem no terminal da direita o monitoramento contínuo de CPU via Docker Stats:*  
  > *Vejam como o `customers-service` é imediatamente exigido sob carga, ultrapassando 200% a 350% de utilização de CPU porque precisa processar as consultas e inserções no banco.*  
  > *Enquanto isso, o `api-gateway` se mantém estável em torno de 90-110% lidando com o roteamento reativo não-bloqueante, e o `vets-service` opera com amplo alívio de processamento.*  
  > *O script captura todas as métricas em segundo plano, calcula médias pós-aquecimento e gera os CSVs em `results/raw/`."*

---

### [3:00 - 4:45] Bloco 4: Análise dos Resultados e Gráficos
- **O que Mostrar na Tela:** O `README.md` com as tabelas e os gráficos comparativos da pasta `results/charts/`.
- **Ação:** Abra os gráficos e responda diretamente às 5 perguntas obrigatórias do trabalho:
- **O que Falar:**
  > *"Com as 60 execuções consolidadas, produzimos os gráficos comparativos e respondemos às 5 questões propostas:*  
  > *1. Impacto no tempo de resposta: Conforme o Gráfico 1, o aumento de 30 para 80 usuários causou um crescimento exponencial na latência média, saltando de 16 ms para quase 1.500 ms no perfil de leitura devido à fila de requisições no `customers-service`.*  
  > *2. Vazão: Sob carga leve, o Perfil de Leitura atingiu a maior vazão com quase 138 req/s. Mas sob carga moderada de 80 usuários, a leitura de coleções grandes congestionou mais o sistema que as inserções pontuais da escrita.*  
  > *3. Degradação por operação: O Gráfico 5 mostra com muita clareza que `GET /owners` sofreu a maior degradação, subindo de 25 ms para quase 2.000 ms. Por outro lado, `GET /vets` permaneceu estável em apenas 7 ms durante todo o teste, comprovando o isolamento de recursos do microsserviço independente.*  
  > *4. Consumo de CPU: O `customers-service` foi o grande gargalo da aplicação, atingindo pico de 450% de CPU no Cenário B, enquanto o `vets-service` consumiu menos de 5%.*  
  > *5. Taxa de falhas: No Cenário C com 150 usuários, os Circuit Breakers do Spring Cloud Gateway foram acionados para evitar o travamento em cascata, resultando em taxa de falhas próxima de 100% com rejeição rápida das conexões."*

---

### [4:45 - 5:30] Bloco 5: Conclusões e Encerramento
- **O que Mostrar na Tela:** O repositório no GitHub ou terminal com a estrutura de pastas organizada.
- **O que Falar:**
  > *"Em conclusão, os experimentos demonstraram na prática os benefícios do isolamento de falhas em microsserviços, bem como a necessidade de escalabilidade horizontal automática (HPA) e cache distribuído para microsserviços que concentram grande volume de consultas, como o `customers-service`.*  
  > *Todos os arquivos, scripts de reprodução, CSVs brutos, tabelas e gráficos estão disponíveis e organizados no repositório GitHub.*  
  > *Muito obrigado pela atenção!"*

---

## 📌 Dicas Finais para Envio
1. Faça o upload do vídeo gravado no **YouTube** (como *Não Listado* ou *Público*) ou no **Google Drive** (certifique-se de que a permissão de compartilhamento esteja definida para *"Qualquer pessoa com o link pode visualizar"*).
2. Abra o arquivo `README.md`, localize a linha:
   ```markdown
   > **Link do Vídeo (YouTube / Google Drive):** `[COLOQUE O LINK DO SEU VÍDEO AQUI]`
   ```
   e substitua pelo link do vídeo gravado.
3. Faça o commit e push para o repositório GitHub:
   ```bash
   git add .
   git commit -m "Entrega TP06: Avaliação de Desempenho com Locust"
   git push origin main
   ```
4. Submeta o link do repositório no SIGAA.
