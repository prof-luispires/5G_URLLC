import csv
import json
import math
import os
import random
from datetime import datetime

# =========================================================
# CONFIGURACAO GLOBAL V3 - COM LATENCIA EXPLICITA
# =========================================================

SEED = 42
random.seed(SEED)

BASE_DIR = "v3_dense_sweep_latency"
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")

OUTPUT_CSV = os.path.join(DATASET_DIR, "urllc_fr2_mc_raw_dataset_v3_latency.csv")
CONFIG_JSON = os.path.join(BASE_DIR, "config_v3_latency.json")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

NUM_SAMPLES_PER_SCENARIO = 1500

# Sweep denso
E_K_SCENARIOS = [5, 10, 20, 40, 60, 80, 100]
BETA_VALUES = [0.005, 0.0075, 0.01, 0.015, 0.02]
BLOCKLENGTH_VALUES = [100, 200, 300, 400, 600, 800, 1000]
MISALIGNMENT_VALUES_DEG = [0, 2, 4, 6, 8, 10, 12, 15]

# Parametros fisicos
SERVICE_DISTANCE_RANGE = (60.0, 120.0)   # m
REGION_RADIUS = 250.0                    # m
INTERFERER_MIN_DISTANCE = 5.0            # m

ALPHA_LOS = 2.0
ALPHA_NLOS = 3.5

# Potencias e ruido
P_SIGNAL = 1.0
P_INTERFERER = 0.2
NOISE_POWER = 1e-9

# Ganhos de antena simplificados
G_MAIN = 10.0
G_SIDE = 0.1

# Finite blocklength
TARGET_RATE = 0.25  # bits/use
EPSILON_TARGET = 1e-5
LATENCY_TARGET_S = 1e-3  # 1 ms

# Modelo de latencia simplificado
QUEUE_MEAN_S = 5e-4          # 0.5 ms em media
RX_PROCESSING_FACTOR = 0.2   # 20% do tempo de transmissao
LIGHT_SPEED = 3e8

CSV_DELIMITER = ";"


# =========================================================
# FUNCOES AUXILIARES
# =========================================================

def q_function(x):
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def poisson_sample_knuth(lmbda):
    """Amostragem exata de Poisson pelo algoritmo de Knuth."""
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def sample_distance_in_annulus(r_min, r_max):
    """Distancia uniforme em area num anel circular."""
    u = random.random()
    return math.sqrt((r_max ** 2 - r_min ** 2) * u + r_min ** 2)


def los_probability(d, beta):
    return math.exp(-beta * d)


def sample_los_state(d, beta):
    return 1 if random.random() < los_probability(d, beta) else 0


def pathloss_linear(d, is_los):
    alpha = ALPHA_LOS if is_los else ALPHA_NLOS
    return d ** (-alpha)


def sample_small_scale_fading():
    """Fading exponencial unitario (potencia Rayleigh simplificada)."""
    u = max(random.random(), 1e-12)
    return -math.log(u)


def signal_antenna_gain(misalignment_deg):
    if misalignment_deg <= 2:
        return G_MAIN
    if misalignment_deg <= 6:
        return G_MAIN * 0.8
    if misalignment_deg <= 10:
        return G_MAIN * 0.5
    if misalignment_deg <= 12:
        return G_MAIN * 0.25
    return G_SIDE


def interferer_antenna_gain():
    return G_MAIN if random.random() < 0.2 else G_SIDE


def finite_blocklength_dispersion(sinr_linear):
    return 1.0 - (1.0 + sinr_linear) ** (-2.0)


def capacity_bits_per_use(sinr_linear):
    return math.log2(1.0 + sinr_linear)


def epsilon_finite_blocklength(sinr_linear, n, rate):
    """Aproximacao normal: eps ~= Q( sqrt(n) * (C-R) / sqrt(V) )"""
    c_val = capacity_bits_per_use(sinr_linear)
    v_val = finite_blocklength_dispersion(sinr_linear)

    if v_val <= 1e-12:
        return 1.0 if c_val < rate else 0.0

    arg = math.sqrt(n) * (c_val - rate) / math.sqrt(v_val)
    eps = q_function(arg)
    return min(max(eps, 0.0), 1.0)


def compute_interference(k_active, beta):
    total_interference = 0.0
    for _ in range(k_active):
        d_i = sample_distance_in_annulus(INTERFERER_MIN_DISTANCE, REGION_RADIUS)
        is_los_i = sample_los_state(d_i, beta)
        pl_i = pathloss_linear(d_i, is_los_i)
        g_i = interferer_antenna_gain()
        h_i = sample_small_scale_fading()
        total_interference += P_INTERFERER * g_i * pl_i * h_i
    return total_interference


def compute_latency_s(sinr_linear, n, distance_m):
    """Modelo simplificado de latencia fim-a-fim para URLLC."""
    c_val = capacity_bits_per_use(max(sinr_linear, 1e-12))
    packet_size_bits = n * TARGET_RATE

    # tempo de transmissao baseado na taxa util aproximada
    tx_time = packet_size_bits / max(c_val, 1e-9)

    # propagacao
    prop_time = distance_m / LIGHT_SPEED

    # fila com modelo exponencial simples
    queue_time = random.expovariate(1.0 / QUEUE_MEAN_S)

    # processamento no recetor proporcional ao tempo de transmissao
    rx_time = tx_time * RX_PROCESSING_FACTOR

    total_latency = tx_time + prop_time + queue_time + rx_time
    return tx_time, queue_time, prop_time, rx_time, total_latency


def save_config():
    config = {
        "experiment_name": "URLLC FR2 Monte Carlo Dataset v3 Dense Sweep with Explicit Latency",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        "base_dir": BASE_DIR,
        "dataset_dir": DATASET_DIR,
        "results_dir": RESULTS_DIR,
        "figures_dir": FIGURES_DIR,
        "output_csv": OUTPUT_CSV,
        "csv_delimiter": CSV_DELIMITER,
        "num_samples_per_scenario": NUM_SAMPLES_PER_SCENARIO,
        "E_K_scenarios": E_K_SCENARIOS,
        "beta_values": BETA_VALUES,
        "blocklength_values": BLOCKLENGTH_VALUES,
        "misalignment_values_deg": MISALIGNMENT_VALUES_DEG,
        "service_distance_range_m": SERVICE_DISTANCE_RANGE,
        "region_radius_m": REGION_RADIUS,
        "interferer_min_distance_m": INTERFERER_MIN_DISTANCE,
        "alpha_los": ALPHA_LOS,
        "alpha_nlos": ALPHA_NLOS,
        "P_signal": P_SIGNAL,
        "P_interferer": P_INTERFERER,
        "noise_power": NOISE_POWER,
        "G_main": G_MAIN,
        "G_side": G_SIDE,
        "target_rate_bits_per_use": TARGET_RATE,
        "epsilon_target": EPSILON_TARGET,
        "latency_target_s": LATENCY_TARGET_S,
        "queue_mean_s": QUEUE_MEAN_S,
        "rx_processing_factor": RX_PROCESSING_FACTOR
    }
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# =========================================================
# GERACAO DO DATASET
# =========================================================

def generate_dataset():
    fieldnames = [
        "scenario_id",
        "E_K_target",
        "beta_blockage",
        "blocklength_n",
        "beam_misalignment_deg",
        "service_distance_m",
        "region_radius_m",
        "K_active",
        "signal_is_los",
        "signal_pathloss_linear",
        "signal_gain_linear",
        "signal_fading",
        "interference_linear",
        "noise_linear",
        "sinr_linear",
        "sinr_db",
        "dispersion_V",
        "capacity_C",
        "epsilon_fbl",
        "tx_time_s",
        "queue_time_s",
        "prop_time_s",
        "rx_time_s",
        "latency_s",
        "success_reliability_only_1e5",
        "success_urlcc_1ms_1e5"
    ]

    total_scenarios = (
        len(E_K_SCENARIOS)
        * len(BETA_VALUES)
        * len(BLOCKLENGTH_VALUES)
        * len(MISALIGNMENT_VALUES_DEG)
    )
    total_rows_expected = total_scenarios * NUM_SAMPLES_PER_SCENARIO

    print("==============================================")
    print(" Monte Carlo Dataset Generator v3 - Dense Sweep + Latency")
    print("==============================================")
    print(f"Pasta base: {BASE_DIR}")
    print(f"Ficheiro de saida: {OUTPUT_CSV}")
    print(f"Total de cenarios: {total_scenarios}")
    print(f"Amostras por cenario: {NUM_SAMPLES_PER_SCENARIO}")
    print(f"Total esperado de linhas: {total_rows_expected}")
    print("==============================================")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()

        scenario_counter = 0
        for e_k in E_K_SCENARIOS:
            for beta in BETA_VALUES:
                for n in BLOCKLENGTH_VALUES:
                    for mis_deg in MISALIGNMENT_VALUES_DEG:
                        scenario_counter += 1
                        scenario_id = f"V3_E{e_k}_B{beta}_N{n}_M{mis_deg}"
                        print(f"[{scenario_counter:03d}/{total_scenarios}] A gerar cenario {scenario_id}")

                        for _ in range(NUM_SAMPLES_PER_SCENARIO):
                            d0 = random.uniform(*SERVICE_DISTANCE_RANGE)
                            k_active = poisson_sample_knuth(e_k)

                            sig_los = sample_los_state(d0, beta)
                            sig_pl = pathloss_linear(d0, sig_los)
                            sig_gain = signal_antenna_gain(mis_deg)
                            sig_fading = sample_small_scale_fading()
                            signal_power = P_SIGNAL * sig_gain * sig_pl * sig_fading

                            interference = compute_interference(k_active, beta)
                            denom = interference + NOISE_POWER
                            sinr = signal_power / denom if denom > 0 else 0.0
                            sinr_db = 10.0 * math.log10(sinr) if sinr > 0 else -999.0

                            v_val = finite_blocklength_dispersion(sinr)
                            c_val = capacity_bits_per_use(sinr)
                            eps = epsilon_finite_blocklength(sinr, n, TARGET_RATE)

                            tx_time, queue_time, prop_time, rx_time, latency = compute_latency_s(sinr, n, d0)

                            success_rel = 1 if eps <= EPSILON_TARGET else 0
                            success_urllc = 1 if (eps <= EPSILON_TARGET and latency <= LATENCY_TARGET_S) else 0

                            writer.writerow({
                                "scenario_id": scenario_id,
                                "E_K_target": e_k,
                                "beta_blockage": beta,
                                "blocklength_n": n,
                                "beam_misalignment_deg": mis_deg,
                                "service_distance_m": round(d0, 4),
                                "region_radius_m": REGION_RADIUS,
                                "K_active": k_active,
                                "signal_is_los": sig_los,
                                "signal_pathloss_linear": f"{sig_pl:.10e}",
                                "signal_gain_linear": f"{sig_gain:.10e}",
                                "signal_fading": f"{sig_fading:.10e}",
                                "interference_linear": f"{interference:.10e}",
                                "noise_linear": f"{NOISE_POWER:.10e}",
                                "sinr_linear": f"{sinr:.10e}",
                                "sinr_db": f"{sinr_db:.6f}",
                                "dispersion_V": f"{v_val:.10e}",
                                "capacity_C": f"{c_val:.10e}",
                                "epsilon_fbl": f"{eps:.10e}",
                                "tx_time_s": f"{tx_time:.10e}",
                                "queue_time_s": f"{queue_time:.10e}",
                                "prop_time_s": f"{prop_time:.10e}",
                                "rx_time_s": f"{rx_time:.10e}",
                                "latency_s": f"{latency:.10e}",
                                "success_reliability_only_1e5": success_rel,
                                "success_urlcc_1ms_1e5": success_urllc
                            })

    save_config()
    print("==============================================")
    print("Dataset v3 gerado com sucesso.")
    print(f"CSV: {OUTPUT_CSV}")
    print(f"Config: {CONFIG_JSON}")
    print("==============================================")


if __name__ == "__main__":
    generate_dataset()
