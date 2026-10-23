# Tabela de Utilização Média de CPU por Microsserviço

| Cenário          | Perfil   | api-gateway (Média ± DP)   | customers-service (Média ± DP)   | vets-service (Média ± DP)   |
|------------------|----------|----------------------------|----------------------------------|-----------------------------|
| A (30 usuários)  | Escrita  | 11.14 ± 3.62%              | 146.72 ± 31.76%                  | 0.30 ± 0.15%                |
| B (80 usuários)  | Escrita  | 40.32 ± 1.22%              | 153.84 ± 23.19%                  | 0.22 ± 0.04%                |
| C (150 usuários) | Escrita  | 80.00 ± 5.56%              | 126.42 ± 17.04%                  | 0.46 ± 0.41%                |
| A (30 usuários)  | Leitura  | 7.92 ± 2.34%               | 170.53 ± 51.88%                  | 0.59 ± 0.35%                |
| B (80 usuários)  | Leitura  | 41.97 ± 0.72%              | 159.74 ± 23.98%                  | 0.17 ± 0.04%                |
| C (150 usuários) | Leitura  | 83.97 ± 2.79%              | 129.95 ± 14.88%                  | 0.13 ± 0.02%                |
