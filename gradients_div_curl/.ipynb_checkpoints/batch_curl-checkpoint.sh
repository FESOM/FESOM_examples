#!/bin/bash
#SBATCH --partition=batch
#SBATCH --account=your_account
#SBATCH --nodes=1
#SBATCH --time=06:00:00
#SBATCH --job-name=curl
#SBATCH --array=2015-2020 # job array index for each year

#SBATCH --mail-type=end      
#SBATCH --mail-type=fail
#SBATCH --mail-user=your_email@awi.de


# Begin of section with executable commands

module --force purge
source ~/.bashrc
conda activate your_environment

cd /path_to_script/
depth=$1
srun python calc_curl.py ${SLURM_ARRAY_TASK_ID} ${depth}
