#!/usr/bin/env python3
"""
Gera graficos de alta resolucao e tabelas em Markdown para o relatorio.
Trabalho Pratico 06 - Sistemas Distribuidos
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate

# Estilo visual moderno e limpo
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "figure.titlesize": 16,
    "figure.dpi": 300,
    "savefig.dpi": 300
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")
TABLES_DIR = os.path.join(RESULTS_DIR, "tables")

os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

COLOR_LEITURA = "#2b5c8f"    # Azul solido elegante
COLOR_ESCRITA = "#d95f02"    # Laranja avermelhado elegante
PALETTE = {"leitura": COLOR_LEITURA, "escrita": COLOR_ESCRITA}
PALETTE_LABELS = {"leitura": "Perfil 1 — Leitura", "escrita": "Perfil 2 — Escrita"}


def load_data():
    raw_csv = os.path.join(RESULTS_DIR, "raw_executions.csv")
    agg_csv = os.path.join(RESULTS_DIR, "aggregated_summary.csv")
    endp_csv = os.path.join(RESULTS_DIR, "aggregated_by_endpoint.csv")

    if not os.path.exists(raw_csv):
        raise FileNotFoundError(f"Arquivo nao encontrado: {raw_csv}")

    df_raw = pd.read_csv(raw_csv)
    df_agg = pd.read_csv(agg_csv) if os.path.exists(agg_csv) else None
    df_endp = pd.read_csv(endp_csv) if os.path.exists(endp_csv) else None

    return df_raw, df_agg, df_endp


def plot_avg_response_time(df_agg):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    for prof in ["leitura", "escrita"]:
        sub = df_agg[df_agg["profile"] == prof].sort_values("users")
        label = PALETTE_LABELS[prof]
        color = PALETTE[prof]
        ax.errorbar(
            sub["users"],
            sub["avg_response_time_ms_mean"],
            yerr=sub["avg_response_time_ms_std"].fillna(0),
            marker="o",
            linewidth=2.5,
            markersize=8,
            capsize=5,
            label=label,
            color=color
        )
        for _, row in sub.iterrows():
            ax.annotate(
                f"{row['avg_response_time_ms_mean']:.1f} ms",
                (row["users"], row["avg_response_time_ms_mean"]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontweight="bold",
                fontsize=10,
                color=color
            )

    ax.set_title("Impacto da Carga no Tempo Médio de Resposta", pad=15)
    ax.set_xlabel("Usuários Concorrentes")
    ax.set_ylabel("Tempo Médio de Resposta (ms)")
    ax.set_xticks([30, 80, 150])
    ax.set_xticklabels(["30 (Leve)", "80 (Moderado)", "150 (Elevado)"])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "01_tempo_resposta_medio.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def plot_p95_response_time(df_agg):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    for prof in ["leitura", "escrita"]:
        sub = df_agg[df_agg["profile"] == prof].sort_values("users")
        label = PALETTE_LABELS[prof]
        color = PALETTE[prof]
        ax.errorbar(
            sub["users"],
            sub["p95_response_time_ms_mean"],
            yerr=sub["p95_response_time_ms_std"].fillna(0),
            marker="s",
            linewidth=2.5,
            markersize=8,
            capsize=5,
            label=label,
            color=color
        )
        for _, row in sub.iterrows():
            ax.annotate(
                f"{row['p95_response_time_ms_mean']:.1f} ms",
                (row["users"], row["p95_response_time_ms_mean"]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontweight="bold",
                fontsize=10,
                color=color
            )

    ax.set_title("Tempo de Resposta P95 (95º Percentil) vs Carga de Usuários", pad=15)
    ax.set_xlabel("Usuários Concorrentes")
    ax.set_ylabel("Tempo de Resposta P95 (ms)")
    ax.set_xticks([30, 80, 150])
    ax.set_xticklabels(["30 (Leve)", "80 (Moderado)", "150 (Elevado)"])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "02_tempo_resposta_p95.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def plot_throughput(df_agg):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    for prof in ["leitura", "escrita"]:
        sub = df_agg[df_agg["profile"] == prof].sort_values("users")
        label = PALETTE_LABELS[prof]
        color = PALETTE[prof]
        ax.errorbar(
            sub["users"],
            sub["throughput_rps_mean"],
            yerr=sub["throughput_rps_std"].fillna(0),
            marker="^",
            linewidth=2.5,
            markersize=8,
            capsize=5,
            label=label,
            color=color
        )
        for _, row in sub.iterrows():
            ax.annotate(
                f"{row['throughput_rps_mean']:.1f} req/s",
                (row["users"], row["throughput_rps_mean"]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontweight="bold",
                fontsize=10,
                color=color
            )

    ax.set_title("Vazão do Sistema (Throughput) vs Quantidade de Usuários", pad=15)
    ax.set_xlabel("Usuários Concorrentes")
    ax.set_ylabel("Vazão (requisições/s)")
    ax.set_xticks([30, 80, 150])
    ax.set_xticklabels(["30 (Leve)", "80 (Moderado)", "150 (Elevado)"])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "03_vazao_throughput.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def plot_cpu_utilization(df_agg):
    # Agrupa por Cenario e Perfil para mostrar barras de CPU dos servicos
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    scenarios = ["A (30)", "B (80)", "C (150)"]
    x = np.arange(len(scenarios))
    width = 0.25

    # Subplot 1: Perfil Leitura
    df_leit = df_agg[df_agg["profile"] == "leitura"].sort_values("users")
    if not df_leit.empty:
        gw = df_leit["cpu_api-gateway_avg_mean"].values
        cust = df_leit["cpu_customers-service_avg_mean"].values
        vets = df_leit["cpu_vets-service_avg_mean"].values

        ax1.bar(x - width, gw, width, label="api-gateway", color="#3182bd")
        ax1.bar(x, cust, width, label="customers-service", color="#31a354")
        ax1.bar(x + width, vets, width, label="vets-service", color="#fd8d3c")

        for i in range(len(scenarios)):
            ax1.text(x[i] - width, gw[i] + 0.5, f"{gw[i]:.1f}%", ha="center", fontsize=9)
            ax1.text(x[i], cust[i] + 0.5, f"{cust[i]:.1f}%", ha="center", fontsize=9)
            ax1.text(x[i] + width, vets[i] + 0.5, f"{vets[i]:.1f}%", ha="center", fontsize=9)

    ax1.set_title("Perfil 1 — Leitura: Utilização Média de CPU", pad=12)
    ax1.set_xlabel("Cenário (Usuários)")
    ax1.set_ylabel("Utilização de CPU (%)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios)
    ax1.legend(frameon=True, facecolor="white")
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Subplot 2: Perfil Escrita
    df_esc = df_agg[df_agg["profile"] == "escrita"].sort_values("users")
    if not df_esc.empty:
        gw = df_esc["cpu_api-gateway_avg_mean"].values
        cust = df_esc["cpu_customers-service_avg_mean"].values
        vets = df_esc["cpu_vets-service_avg_mean"].values

        ax2.bar(x - width, gw, width, label="api-gateway", color="#3182bd")
        ax2.bar(x, cust, width, label="customers-service", color="#31a354")
        ax2.bar(x + width, vets, width, label="vets-service", color="#fd8d3c")

        for i in range(len(scenarios)):
            ax2.text(x[i] - width, gw[i] + 0.5, f"{gw[i]:.1f}%", ha="center", fontsize=9)
            ax2.text(x[i], cust[i] + 0.5, f"{cust[i]:.1f}%", ha="center", fontsize=9)
            ax2.text(x[i] + width, vets[i] + 0.5, f"{vets[i]:.1f}%", ha="center", fontsize=9)

    ax2.set_title("Perfil 2 — Escrita: Utilização Média de CPU", pad=12)
    ax2.set_xlabel("Cenário (Usuários)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios)
    ax2.legend(frameon=True, facecolor="white")
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.suptitle("Comparativo de Consumo de CPU entre Microsserviços", y=1.02, fontsize=15, fontweight="bold")
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "04_utilizacao_cpu_servicos.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def plot_endpoint_degradation(df_endp):
    if df_endp is None or df_endp.empty:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    operations = ["GET /owners", "GET /owners/{id}", "GET /vets", "POST /owners"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    
    # Perfil Leitura
    df_l = df_endp[df_endp["profile"] == "leitura"].sort_values("users")
    for idx, op in enumerate(operations):
        col = f"{op}_avg_rt_mean"
        if col in df_l.columns:
            ax1.plot(df_l["users"], df_l[col], marker="o", linewidth=2.2, label=op, color=colors[idx])
            for _, r in df_l.iterrows():
                ax1.annotate(f"{r[col]:.1f}", (r["users"], r[col]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)

    ax1.set_title("Perfil 1 — Leitura: Degradação por Operação", pad=12)
    ax1.set_xlabel("Usuários Concorrentes")
    ax1.set_ylabel("Tempo Médio de Resposta (ms)")
    ax1.set_xticks([30, 80, 150])
    ax1.set_xticklabels(["30 (Leve)", "80 (Moderado)", "150 (Elevado)"])
    ax1.legend(frameon=True, facecolor="white")
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Perfil Escrita
    df_e = df_endp[df_endp["profile"] == "escrita"].sort_values("users")
    for idx, op in enumerate(operations):
        col = f"{op}_avg_rt_mean"
        if col in df_e.columns:
            ax2.plot(df_e["users"], df_e[col], marker="o", linewidth=2.2, label=op, color=colors[idx])
            for _, r in df_e.iterrows():
                ax2.annotate(f"{r[col]:.1f}", (r["users"], r[col]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)

    ax2.set_title("Perfil 2 — Escrita: Degradação por Operação", pad=12)
    ax2.set_xlabel("Usuários Concorrentes")
    ax2.set_xticks([30, 80, 150])
    ax2.set_xticklabels(["30 (Leve)", "80 (Moderado)", "150 (Elevado)"])
    ax2.legend(frameon=True, facecolor="white")
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.suptitle("Degradação do Tempo de Resposta por Tipo de Operação", y=1.02, fontsize=15, fontweight="bold")
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "05_degradacao_por_operacao.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def plot_failure_rates(df_agg):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    scenarios = ["A (30)", "B (80)", "C (150)"]
    x = np.arange(len(scenarios))
    width = 0.35

    df_l = df_agg[df_agg["profile"] == "leitura"].sort_values("users")
    df_e = df_agg[df_agg["profile"] == "escrita"].sort_values("users")

    fl_l = df_l["failure_rate_pct_mean"].values if not df_l.empty else [0, 0, 0]
    fl_e = df_e["failure_rate_pct_mean"].values if not df_e.empty else [0, 0, 0]

    b1 = ax.bar(x - width/2, fl_l, width, label="Perfil 1 — Leitura", color=COLOR_LEITURA)
    b2 = ax.bar(x + width/2, fl_e, width, label="Perfil 2 — Escrita", color=COLOR_ESCRITA)

    for i in range(len(scenarios)):
        ax.text(x[i] - width/2, fl_l[i] + 0.05, f"{fl_l[i]:.2f}%", ha="center", fontsize=10, fontweight="bold")
        ax.text(x[i] + width/2, fl_e[i] + 0.05, f"{fl_e[i]:.2f}%", ha="center", fontsize=10, fontweight="bold")

    ax.set_title("Taxa de Falhas (%) entre Cenários e Perfis", pad=15)
    ax.set_xlabel("Cenário (Usuários)")
    ax.set_ylabel("Taxa de Falhas (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend(frameon=True, facecolor="white")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "06_taxa_falhas.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[GRAFICO] Salvo: {out_path}")


def fmt_val_std(val, std, unit=""):
    if pd.isna(std) or std == 0:
        return f"{val:.2f}{unit}"
    return f"{val:.2f} ± {std:.2f}{unit}"


def generate_markdown_tables(df_agg, df_endp):
    # 1. Tabela Resumo Geral de Metricas Obrigatorias
    table_rows = []
    for _, r in df_agg.sort_values(["profile", "users"]).iterrows():
        prof_name = "Leitura" if r["profile"] == "leitura" else "Escrita"
        table_rows.append([
            f"Cenário {r['scenario']} ({r['scenario_name']})",
            f"Perfil {prof_name}",
            int(r["users"]),
            fmt_val_std(r['avg_response_time_ms_mean'], r['avg_response_time_ms_std']),
            fmt_val_std(r['p95_response_time_ms_mean'], r['p95_response_time_ms_std']),
            fmt_val_std(r['throughput_rps_mean'], r['throughput_rps_std']),
            f"{int(r['total_requests_mean'])}",
            f"{r['failure_rate_pct_mean']:.2f}%",
            f"{r['cpu_api-gateway_avg_mean']:.1f}%",
            f"{r['cpu_customers-service_avg_mean']:.1f}%",
            f"{r['cpu_vets-service_avg_mean']:.1f}%"
        ])

    headers = [
        "Cenário", "Perfil", "Usuários", "Média RT (ms)", "P95 RT (ms)",
        "Vazão (req/s)", "Total Reqs", "Falhas (%)", "CPU Gateway", "CPU Customers", "CPU Vets"
    ]
    md_table = tabulate(table_rows, headers=headers, tablefmt="github")
    
    tabela_path = os.path.join(TABLES_DIR, "tabela_resumo_metricas.md")
    with open(tabela_path, "w") as f:
        f.write("# Tabela Resumo: Métricas Obrigatórias\n\n")
        f.write(md_table + "\n")
    print(f"[TABELA] Salva: {tabela_path}")

    # 2. Tabela de Degradação por Operação
    if df_endp is not None and not df_endp.empty:
        op_rows = []
        for _, r in df_endp.sort_values(["profile", "users"]).iterrows():
            prof_name = "Leitura" if r["profile"] == "leitura" else "Escrita"
            op_rows.append([
                f"{r['scenario']} ({r['users']} u)",
                prof_name,
                f"{r['GET /owners_avg_rt_mean']:.1f} / {r['GET /owners_p95_rt_mean']:.1f}",
                f"{r['GET /owners/{id}_avg_rt_mean']:.1f} / {r['GET /owners/{id}_p95_rt_mean']:.1f}",
                f"{r['GET /vets_avg_rt_mean']:.1f} / {r['GET /vets_p95_rt_mean']:.1f}",
                f"{r['POST /owners_avg_rt_mean']:.1f} / {r['POST /owners_p95_rt_mean']:.1f}"
            ])
        op_headers = ["Cenário", "Perfil", "GET /owners (Avg/P95)", "GET /owners/{id} (Avg/P95)", "GET /vets (Avg/P95)", "POST /owners (Avg/P95)"]
        op_md = tabulate(op_rows, headers=op_headers, tablefmt="github")
        op_path = os.path.join(TABLES_DIR, "tabela_degradacao_operacoes.md")
        with open(op_path, "w") as f:
            f.write("# Tabela de Degradação de Latência por Operação (ms)\n\n")
            f.write(op_md + "\n")
        print(f"[TABELA] Salva: {op_path}")

    # 3. Tabela de Consumo de CPU
    cpu_rows = []
    for _, r in df_agg.sort_values(["profile", "users"]).iterrows():
        prof_name = "Leitura" if r["profile"] == "leitura" else "Escrita"
        cpu_rows.append([
            f"{r['scenario']} ({r['users']} usuários)",
            prof_name,
            fmt_val_std(r['cpu_api-gateway_avg_mean'], r['cpu_api-gateway_avg_std'], "%"),
            fmt_val_std(r['cpu_customers-service_avg_mean'], r['cpu_customers-service_avg_std'], "%"),
            fmt_val_std(r['cpu_vets-service_avg_mean'], r['cpu_vets-service_avg_std'], "%")
        ])
    cpu_headers = ["Cenário", "Perfil", "api-gateway (Média ± DP)", "customers-service (Média ± DP)", "vets-service (Média ± DP)"]
    cpu_md = tabulate(cpu_rows, headers=cpu_headers, tablefmt="github")
    cpu_path = os.path.join(TABLES_DIR, "tabela_consumo_cpu.md")
    with open(cpu_path, "w") as f:
        f.write("# Tabela de Utilização Média de CPU por Microsserviço\n\n")
        f.write(cpu_md + "\n")
    print(f"[TABELA] Salva: {cpu_path}")


def main():
    try:
        df_raw, df_agg, df_endp = load_data()
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return

    print("Gerando gráficos comparativos...")
    plot_avg_response_time(df_agg)
    plot_p95_response_time(df_agg)
    plot_throughput(df_agg)
    plot_cpu_utilization(df_agg)
    plot_endpoint_degradation(df_endp)
    plot_failure_rates(df_agg)

    print("\nGerando tabelas Markdown...")
    generate_markdown_tables(df_agg, df_endp)

    print("\n[SUCESSO] Todos os gráficos e tabelas foram gerados com sucesso!")


if __name__ == "__main__":
    main()
