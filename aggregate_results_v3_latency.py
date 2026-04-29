import csv
import math
import os
from collections import defaultdict

# =========================================================
# CONFIGURACAO V3 - COM LATENCIA EXPLICITA
# =========================================================

BASE_DIR = "v3_dense_sweep_latency"
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

INPUT_CSV = os.path.join(DATASET_DIR, "urllc_fr2_mc_raw_dataset_v3_latency.csv")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "aggregated_results_v3_latency.csv")

CSV_DELIMITER = ";"

os.makedirs(RESULTS_DIR, exist_ok=True)


# =========================================================
# FUNCOES AUXILIARES
# =========================================================

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return float("nan")


def safe_int(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def mean(values):
    valid = [v for v in values if not math.isnan(v)]
    if not valid:
        return float("nan")
    return sum(valid) / len(valid)


def percentile(values, p):
    valid = sorted(v for v in values if not math.isnan(v))
    n = len(valid)
    if n == 0:
        return float("nan")
    if n == 1:
        return valid[0]

    rank = (p / 100.0) * (n - 1)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return valid[low]
    weight = rank - low
    return valid[low] * (1.0 - weight) + valid[high] * weight


# =========================================================
# AGREGACAO
# =========================================================

def aggregate_results_v3():
    grouped = defaultdict(list)

    print("==============================================")
    print(" Aggregate Results v3 - Dense Sweep + Latency")
    print("==============================================")
    print(f"Input : {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")
    print("==============================================")

    with open(INPUT_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
        for row in reader:
            grouped[row["scenario_id"]].append(row)

    print(f"Total de cenarios encontrados: {len(grouped)}")

    fieldnames = [
        "scenario_id",
        "E_K_target",
        "beta_blockage",
        "blocklength_n",
        "beam_misalignment_deg",
        "num_samples",
        "mean_service_distance_m",
        "mean_K_active",
        "mean_sinr_db",
        "p5_sinr_db",
        "p10_sinr_db",
        "p50_sinr_db",
        "p90_sinr_db",
        "p95_sinr_db",
        "mean_epsilon_fbl",
        "p50_epsilon_fbl",
        "p90_epsilon_fbl",
        "p95_epsilon_fbl",
        "mean_latency_s",
        "p50_latency_s",
        "p90_latency_s",
        "p95_latency_s",
        "reliability_only_1e5",
        "failure_rate_only_1e5",
        "urllc_success_1ms_1e5",
        "urllc_failure_1ms_1e5"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()

        scenario_counter = 0
        total_scenarios = len(grouped)

        for scenario_id in sorted(grouped.keys()):
            scenario_counter += 1
            rows = grouped[scenario_id]
            first = rows[0]

            e_k_target = safe_int(first["E_K_target"])
            beta_blockage = safe_float(first["beta_blockage"])
            blocklength_n = safe_int(first["blocklength_n"])
            beam_misalignment_deg = safe_int(first["beam_misalignment_deg"])

            service_distances = [safe_float(r["service_distance_m"]) for r in rows]
            k_active_values = [safe_int(r["K_active"]) for r in rows]
            sinr_db_values = [safe_float(r["sinr_db"]) for r in rows]
            epsilon_values = [safe_float(r["epsilon_fbl"]) for r in rows]
            latency_values = [safe_float(r["latency_s"]) for r in rows]
            success_rel_values = [safe_int(r["success_reliability_only_1e5"]) for r in rows]
            success_urllc_values = [safe_int(r["success_urlcc_1ms_1e5"]) for r in rows]

            num_samples = len(rows)
            reliability_only = mean(success_rel_values)
            failure_only = 1.0 - reliability_only
            success_urllc = mean(success_urllc_values)
            failure_urllc = 1.0 - success_urllc

            writer.writerow({
                "scenario_id": scenario_id,
                "E_K_target": e_k_target,
                "beta_blockage": f"{beta_blockage:.6f}",
                "blocklength_n": blocklength_n,
                "beam_misalignment_deg": beam_misalignment_deg,
                "num_samples": num_samples,
                "mean_service_distance_m": f"{mean(service_distances):.6f}",
                "mean_K_active": f"{mean(k_active_values):.6f}",
                "mean_sinr_db": f"{mean(sinr_db_values):.6f}",
                "p5_sinr_db": f"{percentile(sinr_db_values, 5):.6f}",
                "p10_sinr_db": f"{percentile(sinr_db_values, 10):.6f}",
                "p50_sinr_db": f"{percentile(sinr_db_values, 50):.6f}",
                "p90_sinr_db": f"{percentile(sinr_db_values, 90):.6f}",
                "p95_sinr_db": f"{percentile(sinr_db_values, 95):.6f}",
                "mean_epsilon_fbl": f"{mean(epsilon_values):.10e}",
                "p50_epsilon_fbl": f"{percentile(epsilon_values, 50):.10e}",
                "p90_epsilon_fbl": f"{percentile(epsilon_values, 90):.10e}",
                "p95_epsilon_fbl": f"{percentile(epsilon_values, 95):.10e}",
                "mean_latency_s": f"{mean(latency_values):.10e}",
                "p50_latency_s": f"{percentile(latency_values, 50):.10e}",
                "p90_latency_s": f"{percentile(latency_values, 90):.10e}",
                "p95_latency_s": f"{percentile(latency_values, 95):.10e}",
                "reliability_only_1e5": f"{reliability_only:.10f}",
                "failure_rate_only_1e5": f"{failure_only:.10f}",
                "urllc_success_1ms_1e5": f"{success_urllc:.10f}",
                "urllc_failure_1ms_1e5": f"{failure_urllc:.10f}"
            })

            if scenario_counter % 100 == 0 or scenario_counter == total_scenarios:
                print(f"Agregados {scenario_counter}/{total_scenarios} cenarios...")

    print("==============================================")
    print("Agregacao v3 concluida com sucesso.")
    print(f"Ficheiro gerado: {OUTPUT_CSV}")
    print("==============================================")


if __name__ == "__main__":
    aggregate_results_v3()
