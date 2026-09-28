@echo off
setlocal

echo =========================================
echo 1. Running Real-Time Data Test
echo =========================================
python scripts\test_realtime_data.py

echo =========================================
echo 2. Running Real-Time CSV Pipeline
echo =========================================
python scripts\run_realtime_csv.py --model data\realtime\supply_chain.csv --events data\realtime\events.csv --output results\realtime

echo =========================================
echo 3. Validating Real-Time Results
echo =========================================
python scripts\validate_realtime_results.py --input results\realtime\realtime_results.csv

echo =========================================
echo 4. Plotting Real-Time Results
echo =========================================
python scripts\plot_realtime_results.py --input results\realtime\realtime_results.csv --output results\plots

echo =========================================
echo 5. Running Real Instances (afiro, blend)
echo =========================================
:: Note: --source is automatically detected by run_real_instance.py
python scripts\run_real_instance.py --instance afiro
python scripts\run_real_instance.py --instance blend

echo =========================================
echo 6. Running Final Pytest Suite
echo =========================================
pytest -q

echo =========================================
echo All commands executed successfully!
echo =========================================
