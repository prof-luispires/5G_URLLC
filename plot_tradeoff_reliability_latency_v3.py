import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt

# =========================================================
# CONFIGURACAO - TRADE-OFF RELIABILITY VS LATENCIA
# =========================================================

BASE_DIR = "v3_dense_sweep_latency"
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")

INPUT_CSV = os.path.join(RESULTS_DIR, "aggregated_results_v3_latency.csv")
OUTPUT_PNG = os.path.join(FIGURES_DIR, "fig_tradeoff_reliability_latency_v3.png")

CSV_DELIMITER = ";"

# Pode ajustar estes filtros para escolher um subconjunto mais limpo
BETA_FIXED = 0.01
MISALIGNMENT_FIXED_DEG = 6

os.makedirs(FIGURES_DIR, exist_ok=True)


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_rows(filename):
    rows = []
    with open(filename, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
        for row in reader:
            rows.append({
                "scenario_id": row["scenario_id"],
                "E_K_target": safe_int(row["E_K_target"]),
                "beta_blockage": safe_float(row["beta_blockage"]),
                "blocklength_n": safe_int(row["blocklength_n"]),
                "beam_misalignment_deg": safe_int(row["beam_misalignment_deg"]),
                "mean_latency_s": safe_float(row["mean_latency_s"]),
                "urllc_success_1ms_1e5": safe_float(row["urllc_success_1ms_1e5"]),
                "reliability_only_1e5": safe_float(row["reliability_only_1e5"]),
            })
    return rows


def filter_rows(rows, beta_fixed, mis_fixed):
    selected = []
    for row in rows:
        if row["beta_blockage"] is None or row["beam_misalignment_deg"] is None:
            continue
        if abs(row["beta_blockage"] - beta_fixed) < 1e-12 and row["beam_misalignment_deg"] == mis_fixed:
            selected.append(row)
    return selected


def group_by_interference(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["E_K_target"]].append(row)
    return grouped


def build_plot(rows):
    plt.figure(figsize=(9.2, 6.0))

    grouped = group_by_interference(rows)
    markers = ["o", "s", "D", "^", "v", "P", "X", "*"]

    for idx, ek in enumerate(sorted(grouped.keys())):
        group = sorted(grouped[ek], key=lambda r: r["blocklength_n"])
        x = [1000.0 * r["mean_latency_s"] for r in group]   # ms
        y = [r["urllc_success_1ms_1e5"] for r in group]
        labels = [r["blocklength_n"] for r in group]

        plt.plot(
            x,
            y,
            marker=markers[idx % len(markers)],
            label=f"E[K]={ek}"
        )

        for xi, yi, n in zip(x, y, labels):
            plt.annotate(
                f"n={n}",
                (xi, yi),
                textcoords="offset points",
                xytext=(5, 4),
                fontsize=8
            )

    plt.axvline(1.0, linestyle="--", linewidth=1.2, label="Latency target = 1 ms")
    plt.xlabel("Mean latency (ms)")
    plt.ylabel("Empirical URLLC success probability")
    plt.title(
        f"Reliability-Latency Trade-off (beta={BETA_FIXED}, misalignment={MISALIGNMENT_FIXED_DEG}°)"
    )
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    print("==============================================")
    print(" Trade-off Plot: Reliability vs Latency (v3)")
    print("==============================================")
    print(f"Input CSV : {INPUT_CSV}")
    print(f"Output PNG: {OUTPUT_PNG}")
    print(f"Filters   : beta={BETA_FIXED}, misalignment={MISALIGNMENT_FIXED_DEG} deg")
    print("==============================================")

    rows = load_rows(INPUT_CSV)
    rows = filter_rows(rows, BETA_FIXED, MISALIGNMENT_FIXED_DEG)

    if not rows:
        raise FileNotFoundError(
            "Nao foram encontrados cenarios com os filtros escolhidos. "
            "Confirme se ja executou aggregate_results_v3_latency.py "
            "e ajuste BETA_FIXED / MISALIGNMENT_FIXED_DEG se necessario."
        )

    build_plot(rows)

    print("==============================================")
    print("Figura gerada com sucesso.")
    print(f"Ficheiro: {OUTPUT_PNG}")
    print("==============================================")


if __name__ == "__main__":
    main()
