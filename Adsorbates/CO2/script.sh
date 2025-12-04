#!/bin/bash
#SBATCH --job-name=CO2_calc
#SBATCH --partition=west
#SBATCH --cpus-per-task=2



conda deactivate
conda activate pynta_fairchem
python /projects/westgroup/lekia.p/NEB/Adsorbates/CO2/script.py