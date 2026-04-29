[README_v4_latency_calibrated.md](https://github.com/user-attachments/files/27197912/README_v4_latency_calibrated.md)


Latency model computed:

    T_tx = (n * R) / C(SINR)

This expression gives a number of channel uses, not seconds. In v3 it was interpreted directly as seconds, which generated unrealistic latency values.

In v4 this is corrected by using:

    T_tx = n / B_eff

where:
- n is the finite blocklength in channel uses;
- B_eff is the effective number of channel uses per second.

Default:
    B_eff = 100e6 channel uses/s

Thus:
    n = 1000 -> T_tx = 10 microseconds

The final latency is:
    T_latency = T_tx + T_queue + T_prop + T_rx + T_sched

## Run order

1. Generate the dataset:
    python mc_dataset_generator_v4_latency_calibrated.py

2. Aggregate the results:
    python aggregate_results_v4_latency_calibrated.py

3. Generate figures and Excel:
    python plot_results_v4_latency_calibrated.py

## Expected outputs

Folder:
    v4_dense_sweep_latency_calibrated/

Files:
    datasets/urllc_fr2_mc_raw_dataset_v4_latency_calibrated.csv
    results/aggregated_results_v4_latency_calibrated.csv
    results/results_summary_v4_latency_calibrated.xlsx
    figures/*.png

## Main corrected parameter

In config_v4_latency_calibrated.json:

    "effective_channel_uses_per_second": 100000000.0

For sensitivity tests:
- 20e6 gives larger latency;
- 100e6 is reasonable for wideband FR2;
- 400e6 gives lower transmission time.
