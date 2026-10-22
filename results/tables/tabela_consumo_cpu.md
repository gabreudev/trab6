# Tabela de Utilização Média de CPU por Microsserviço

| Cenário          | Perfil   | api-gateway (Média ± DP)   | customers-service (Média ± DP)   | vets-service (Média ± DP)   |
|------------------|----------|----------------------------|----------------------------------|-----------------------------|
| A (30 usuários)  | Escrita  | 88.56%                     | 365.21%                          | 33.58%                      |
| B (80 usuários)  | Escrita  | 35.70%                     | 430.77%                          | 4.91%                       |
| C (150 usuários) | Escrita  | 108.00%                    | 0.12%                            | 0.14%                       |
| A (30 usuários)  | Leitura  | 111.26%                    | 197.39%                          | 48.30%                      |
| B (80 usuários)  | Leitura  | 29.25%                     | 450.84%                          | 3.53%                       |
| C (150 usuários) | Leitura  | 91.00%                     | 193.55%                          | 1.34%                       |
