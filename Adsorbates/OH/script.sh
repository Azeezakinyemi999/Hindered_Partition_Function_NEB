#!/bin/bash
#SBATCH --job-name=OH_calc
#SBATCH --partition=west
#SBATCH --cpus-per-task=2

conda deactivate
conda activate pynta_fairchem
python /projects/westgroup/lekia.p/NEB/Adsorbates/OH/script.py