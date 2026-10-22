# Tabela Resumo: Métricas Obrigatórias

| Cenário              | Perfil         |   Usuários |   Média RT (ms) |   P95 RT (ms) |   Vazão (req/s) |   Total Reqs | Falhas (%)   | CPU Gateway   | CPU Customers   | CPU Vets   |
|----------------------|----------------|------------|-----------------|---------------|-----------------|--------------|--------------|---------------|-----------------|------------|
| Cenário A (Leve)     | Perfil Escrita |         30 |           50.76 |           250 |          120.08 |         2276 | 0.00%        | 88.6%         | 365.2%          | 33.6%      |
| Cenário B (Moderado) | Perfil Escrita |         80 |          910.62 |          1900 |           71.34 |         1356 | 0.00%        | 35.7%         | 430.8%          | 4.9%       |
| Cenário C (Elevado)  | Perfil Escrita |        150 |            8.12 |            18 |          716.96 |        13659 | 100.00%      | 108.0%        | 0.1%            | 0.1%       |
| Cenário A (Leve)     | Perfil Leitura |         30 |           16.15 |            35 |          137.99 |         2626 | 0.00%        | 111.3%        | 197.4%          | 48.3%      |
| Cenário B (Moderado) | Perfil Leitura |         80 |         1475.82 |          2200 |           48.59 |          925 | 0.00%        | 29.2%         | 450.8%          | 3.5%       |
| Cenário C (Elevado)  | Perfil Leitura |        150 |          449.33 |            23 |          266.44 |         5070 | 98.68%       | 91.0%         | 193.6%          | 1.3%       |
