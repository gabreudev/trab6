#!/usr/bin/env python3
"""
Orquestrador de Experimentos de Desempenho com Locust
Trabalho Prático 06 - Sistemas Distribuídos
Spring PetClinic Microservices
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# Definicoes dos perfis e cenarios
SCENARIOS = {
    "A": {"name": "Leve", "users": 30, "spawn_rate": 5, "duration": 360, "warmup": 60},
    "B": {"name": "Moderado", "users": 80, "spawn_rate": 10, "duration": 360, "warmup": 60},
    "C": {"name": "Elevado", "users": 150, "spawn_rate": 15, "duration": 360, "warmup": 60},
}

PROFILES = {
    "leitura": {
        "user_class": "PerfilLeituraUser",
        "description": "Perfil 1 — Leitura (45% GET /owners, 35% GET /owners/{id}, 15% GET /vets, 5% POST /owners)"
    },
    "escrita": {
        "user_class": "PerfilEscritaUser",
        "description": "Perfil 2 — Escrita (20% GET /owners, 20% GET /owners/{id}, 20% GET /vets, 40% POST /owners)"
    }
}

MONITORED_CONTAINERS = ["api-gateway", "customers-service", "vets-service"]


class CpuMonitor(threading.Thread):
    """Monitora a utilizacao de CPU dos containers Docker durante o experimento."""
    def __init__(self, containers, interval=2.0):
        super().__init__()
        self.containers = containers
        self.interval = interval
        self.running = True
        self.records = []
        self.start_time = None
        self.warmup_seconds = 0

    def run(self):
        self.start_time = time.time()
        while self.running:
            now = time.time()
            elapsed = now - self.start_time
            phase = "warmup" if elapsed < self.warmup_seconds else "measurement"
            
            try:
                cmd = [
                    "docker", "stats", "--no-stream",
                    "--format", "{{.Name}},{{.CPUPerc}},{{.MemPerc}}"
                ] + self.containers
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                for line in res.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        cpu_str = parts[1].strip().replace("%", "")
                        mem_str = parts[2].strip().replace("%", "") if len(parts) >= 3 else "0.0"
                        try:
                            cpu_val = float(cpu_str)
                            mem_val = float(mem_str)
                        except ValueError:
                            cpu_val = 0.0
                            mem_val = 0.0
                        self.records.append({
                            "timestamp": now,
                            "elapsed_s": round(elapsed, 2),
                            "phase": phase,
                            "container": name,
                            "cpu_pct": cpu_val,
                            "mem_pct": mem_val
                        })
            except Exception as e:
                # Docker pode demorar para responder ou container reiniciar
                pass
            
            time.sleep(self.interval)

    def stop(self):
        self.running = False


def run_single_execution(scenario_id, profile_key, rep_num, duration, warmup, host, base_dir, users_override=None):
    sc_info = SCENARIOS[scenario_id]
    prof_info = PROFILES[profile_key]
    users = users_override if users_override is not None else sc_info["users"]
    spawn_rate = sc_info["spawn_rate"]

    raw_dir = os.path.join(base_dir, "results", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    file_prefix = f"sc_{scenario_id}_prof_{profile_key}_rep_{rep_num:02d}"
    csv_out_prefix = os.path.join(raw_dir, file_prefix)

    print("\n" + "=" * 70)
    print(f"Executando: Cenario {scenario_id} ({sc_info['name']}) | Perfil: {profile_key.upper()} | Repeticao: {rep_num}")
    print(f"Usuarios: {users} | Spawn: {spawn_rate}/s | Duracao: {duration}s | Aquecimento: {warmup}s")
    print("=" * 70)

    # 1. Inicia monitor de CPU
    monitor = CpuMonitor(MONITORED_CONTAINERS, interval=2.0)
    monitor.warmup_seconds = warmup
    monitor.start()

    # 2. Executa Locust em modo headless
    locust_cmd = [
        os.path.join(base_dir, "venv", "bin", "locust"),
        "-f", os.path.join(base_dir, "locustfile.py"),
        prof_info["user_class"],
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", f"{duration}s",
        "--host", host,
        "--csv", csv_out_prefix,
        "--only-summary"
    ]
    
    env = os.environ.copy()
    env["WARMUP_SECONDS"] = str(warmup)

    start_exec = time.time()
    try:
        proc = subprocess.run(locust_cmd, env=env, capture_output=True, text=True)
    finally:
        monitor.stop()
        monitor.join()

    exec_elapsed = time.time() - start_exec
    print(f"Finalizado em {exec_elapsed:.1f}s (codigo de saida: {proc.returncode})")

    # 3. Salva metricas de CPU
    cpu_df = pd.DataFrame(monitor.records)
    if not cpu_df.empty:
        cpu_csv = f"{csv_out_prefix}_cpu_samples.csv"
        cpu_df.to_csv(cpu_csv, index=False)

    # 4. Processa stats do Locust
    stats_file = f"{csv_out_prefix}_stats.csv"
    if not os.path.exists(stats_file):
        print(f"ERRO: Arquivo {stats_file} nao foi gerado pelo Locust!")
        return None

    stats_df = pd.read_csv(stats_file)
    
    # Linha agregada
    agg_row = stats_df[stats_df["Name"] == "Aggregated"]
    if agg_row.empty:
        agg_row = stats_df[stats_df["Name"].isna()]
    
    if agg_row.empty:
        print("ERRO: Nao encontrou linha Aggregated no CSV.")
        return None

    agg = agg_row.iloc[0]
    total_reqs = int(agg.get("Request Count", 0))
    total_fails = int(agg.get("Failure Count", 0))
    avg_rt = float(agg.get("Average Response Time", 0.0))
    p95_rt = float(agg.get("95%", 0.0))
    throughput = float(agg.get("Requests/s", 0.0))
    fail_rate = (total_fails / total_reqs * 100.0) if total_reqs > 0 else 0.0

    # Medias de CPU no periodo de medicao pura (pos-aquecimento)
    cpu_meas = cpu_df[cpu_df["phase"] == "measurement"] if not cpu_df.empty else pd.DataFrame()
    
    cpu_stats = {}
    for c in MONITORED_CONTAINERS:
        if not cpu_meas.empty and c in cpu_meas["container"].values:
            c_samples = cpu_meas[cpu_meas["container"] == c]["cpu_pct"]
            cpu_stats[f"cpu_{c}_avg"] = round(c_samples.mean(), 2)
            cpu_stats[f"cpu_{c}_max"] = round(c_samples.max(), 2)
        else:
            cpu_stats[f"cpu_{c}_avg"] = 0.0
            cpu_stats[f"cpu_{c}_max"] = 0.0

    # Metricas por operacao
    op_metrics = {}
    for op in ["GET /owners", "GET /owners/{id}", "GET /vets", "POST /owners"]:
        op_row = stats_df[stats_df["Name"] == op]
        if not op_row.empty:
            r = op_row.iloc[0]
            op_metrics[f"{op}_reqs"] = int(r.get("Request Count", 0))
            op_metrics[f"{op}_fails"] = int(r.get("Failure Count", 0))
            op_metrics[f"{op}_avg_rt"] = float(r.get("Average Response Time", 0.0))
            op_metrics[f"{op}_p95_rt"] = float(r.get("95%", 0.0))
            op_metrics[f"{op}_rps"] = float(r.get("Requests/s", 0.0))
        else:
            op_metrics[f"{op}_reqs"] = 0
            op_metrics[f"{op}_fails"] = 0
            op_metrics[f"{op}_avg_rt"] = 0.0
            op_metrics[f"{op}_p95_rt"] = 0.0
            op_metrics[f"{op}_rps"] = 0.0

    result = {
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario_id,
        "scenario_name": sc_info["name"],
        "profile": profile_key,
        "repetition": rep_num,
        "users": users,
        "duration_s": duration,
        "warmup_s": warmup,
        "total_requests": total_reqs,
        "total_failures": total_fails,
        "failure_rate_pct": round(fail_rate, 4),
        "avg_response_time_ms": round(avg_rt, 2),
        "p95_response_time_ms": round(p95_rt, 2),
        "throughput_rps": round(throughput, 2),
        **cpu_stats,
        **op_metrics
    }

    print(f"-> Resultado: {throughput:.1f} req/s | Avg RT: {avg_rt:.1f} ms | P95: {p95_rt:.1f} ms | Falhas: {fail_rate:.2f}%")
    print(f"-> CPU: Gateway={cpu_stats.get('cpu_api-gateway_avg', 0)}% | Customers={cpu_stats.get('cpu_customers-service_avg', 0)}% | Vets={cpu_stats.get('cpu_vets-service_avg', 0)}%")

    return result


def aggregate_results(raw_executions_csv, results_dir):
    df = pd.read_csv(raw_executions_csv)
    
    # Agrupamento por Cenario e Perfil
    grouped = df.groupby(["scenario", "scenario_name", "profile", "users"])

    agg_summary = grouped.agg({
        "avg_response_time_ms": ["mean", "std"],
        "p95_response_time_ms": ["mean", "std"],
        "throughput_rps": ["mean", "std"],
        "total_requests": ["mean", "std"],
        "failure_rate_pct": ["mean", "std"],
        "cpu_api-gateway_avg": ["mean", "std"],
        "cpu_customers-service_avg": ["mean", "std"],
        "cpu_vets-service_avg": ["mean", "std"],
    }).reset_index()

    # Flatten column multi-index
    agg_summary.columns = [
        f"{c[0]}_{c[1]}" if c[1] else c[0] for c in agg_summary.columns
    ]

    out_file = os.path.join(results_dir, "aggregated_summary.csv")
    agg_summary.to_csv(out_file, index=False)
    print(f"\n[OK] Resumo agregado salvo em: {out_file}")

    # Agregacao por operacao
    op_cols = {}
    for op in ["GET /owners", "GET /owners/{id}", "GET /vets", "POST /owners"]:
        op_cols[f"{op}_avg_rt"] = ["mean", "std"]
        op_cols[f"{op}_p95_rt"] = ["mean", "std"]
        op_cols[f"{op}_rps"] = ["mean", "std"]
        op_cols[f"{op}_reqs"] = ["mean"]

    op_summary = grouped.agg(op_cols).reset_index()
    op_summary.columns = [
        f"{c[0]}_{c[1]}" if c[1] else c[0] for c in op_summary.columns
    ]
    op_out_file = os.path.join(results_dir, "aggregated_by_endpoint.csv")
    op_summary.to_csv(op_out_file, index=False)
    print(f"[OK] Resumo por endpoint salvo em: {op_out_file}")

    return agg_summary, op_summary


def check_services_health(host):
    """Verifica se o API Gateway e os servicos estao saudaveis antes de iniciar a execucao."""
    for attempt in range(12):
        try:
            r = requests.get(f"{host}/api/vet/vets", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        print(f"[!] Aguardando microsservicos responderem em {host} (tentativa {attempt+1}/12)...")
        time.sleep(5)
    return False


def main():
    parser = argparse.ArgumentParser(description="Executor de Testes de Carga com Locust")
    parser.add_argument("--scenarios", nargs="+", default=["A", "B", "C"], choices=["A", "B", "C"], help="Cenarios a executar")
    parser.add_argument("--profiles", nargs="+", default=["leitura", "escrita"], choices=["leitura", "escrita"], help="Perfis a executar")
    parser.add_argument("--repetitions", type=int, default=10, help="Numero de repeticoes (padrao: 10)")
    parser.add_argument("--duration", type=int, default=None, help="Duracao em segundos (padrao: 360s)")
    parser.add_argument("--warmup", type=int, default=None, help="Tempo de aquecimento em segundos (padrao: 60s)")
    parser.add_argument("--host", default="http://localhost:8080", help="Host da aplicacao (API Gateway)")
    parser.add_argument("--quick", action="store_true", help="Modo rapido de teste de calibracao (30s teste, 10s warmup, 1 repeticao)")
    parser.add_argument("--clean", action="store_true", help="Limpa resultados anteriores antes de iniciar")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    raw_csv = os.path.join(results_dir, "raw_executions.csv")
    raw_dir = os.path.join(results_dir, "raw")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    if args.quick:
        print("[MODO QUICK ATIVADO] Executando calibracao rapida: 30s teste, 10s warmup, 1 repeticao")
        duration = 30
        warmup = 10
        repetitions = 1
    else:
        duration = args.duration if args.duration else 360
        warmup = args.warmup if args.warmup else 60
        repetitions = args.repetitions

    # Limpeza se solicitada
    if args.clean and os.path.exists(raw_csv):
        print("[LIMPEZA] Removendo execucoes anteriores para iniciar bateria limpa...")
        os.remove(raw_csv)
        for f in os.listdir(raw_dir):
            try:
                os.remove(os.path.join(raw_dir, f))
            except Exception:
                pass

    # Carrega execucoes existentes se o arquivo ja existir
    existing_records = []
    if os.path.exists(raw_csv):
        try:
            existing_records = pd.read_csv(raw_csv).to_dict("records")
        except Exception:
            existing_records = []

    all_records = list(existing_records)

    total_runs = len(args.scenarios) * len(args.profiles) * repetitions
    current_run = len(all_records)
    runs_to_do = total_runs - current_run

    print("=" * 70)
    print(f"Bateria de Experimentos Oficial: Total de {total_runs} execuções.")
    print(f"Já concluídas: {current_run} | Restantes: {runs_to_do}")
    print(f"Perfis: {args.profiles} | Cenários: {args.scenarios} | Repetições: {repetitions}")
    print(f"Duração por teste: {duration}s ({duration/60:.1f} min) | Aquecimento: {warmup}s ({warmup/60:.1f} min)")
    est_total_min = (runs_to_do * (duration + 10)) // 60
    print(f"Tempo total estimado restante: ~{est_total_min} minutos (~{est_total_min/60:.1f} horas)")
    print("=" * 70)

    for sc_id in args.scenarios:
        for prof_key in args.profiles:
            for rep in range(1, repetitions + 1):
                # Verifica se este cenario/perfil/rep ja foi executado
                already_done = any(
                    r.get("scenario") == sc_id and
                    r.get("profile") == prof_key and
                    int(r.get("repetition", -1)) == rep and
                    int(r.get("duration_s", 0)) == duration
                    for r in all_records
                )
                if already_done:
                    print(f"[SKIP] Cenario {sc_id} | Perfil {prof_key} | Rep {rep} ja executado anteriormente.")
                    continue

                current_run += 1
                rem_runs = total_runs - current_run
                eta_min = (rem_runs * (duration + 10)) // 60
                print(f"\n>>> Progresso geral: {current_run}/{total_runs} ({(current_run/total_runs)*100:.1f}%) | ETA restante: ~{eta_min} min")

                # Verifica saude dos servicos
                if not check_services_health(args.host):
                    print("[ALERTA] Servicos nao estao respondendo! Tentando prosseguir...")

                res = run_single_execution(
                    scenario_id=sc_id,
                    profile_key=prof_key,
                    rep_num=rep,
                    duration=duration,
                    warmup=warmup,
                    host=args.host,
                    base_dir=base_dir
                )
                if res:
                    all_records.append(res)
                    # Salva imediatamente para evitar perda de dados
                    pd.DataFrame(all_records).to_csv(raw_csv, index=False)

                # Intervalo de resfriamento entre execucoes
                if current_run < total_runs:
                    print("Pausa de 10s para estabilizacao dos microsservicos e garbage collection...")
                    time.sleep(10)

    print("\n" + "=" * 70)
    print("Todas as execucoes foram concluidas com sucesso!")
    print("=" * 70)

    # Agrega resultados
    aggregate_results(raw_csv, results_dir)

    # Gera graficos e tabelas
    plots_script = os.path.join(base_dir, "generate_plots.py")
    if os.path.exists(plots_script):
        print("\nGerando tabelas e graficos comparativos...")
        subprocess.run([os.path.join(base_dir, "venv", "bin", "python3"), plots_script], check=True)


if __name__ == "__main__":
    main()
