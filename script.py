import os
import multiprocessing as mp
from functools import partial
from model.neb import (
    init_molecule, opt_molecule, opt_slab,
    site_screening, validate_screening_files, clean_incomplete_files,
    recover_screening_files, load_screening_results, best_site_results,
    select_neb_endpoints_translation, select_neb_endpoints_rotation,
    prepare_neb_calculation
)

# ===============================================================
# Worker: run a single adsorbate (safe to run in parallel)
# ===============================================================
def run_adsorbate_pipeline(ads_name, base_dir="Adsorbates"):
    """
    Runs full screening + NEB (translation + rotation) for ONE adsorbate.
    Safe for multiprocessing.
    """
    try:
        ads_dir = os.path.join(base_dir, ads_name)
        screening_dir = os.path.join(ads_dir, "Screening_Data")
        neb_trans_dir = os.path.join(ads_dir, "NEB_Translation")
        neb_rot_dir = os.path.join(ads_dir, "NEB_Rotation")

        # Create directories
        os.makedirs(screening_dir, exist_ok=True)
        os.makedirs(neb_trans_dir, exist_ok=True)
        os.makedirs(neb_rot_dir, exist_ok=True)

        print(f"\n=== Starting adsorbate: {ads_name} ===")

        # --- Optimize slab + adsorbate ---
        slab = opt_slab()
        ads = opt_molecule(init_molecule(ads_name))

        # --- Site screening ---
        screening_results = site_screening(
            slab, ads,
            center_xy='site',
            use_all_sites=True,
            workdir=screening_dir
        )

        # --- Validate and recover ---
        validate_screening_files(screening_dir)
        clean_incomplete_files(screening_dir, dry_run=False)
        recover_screening_files(screening_dir)

        # --- Load final screening results ---
        screening_results = load_screening_results(
            os.path.join(screening_dir, "screening_results.pkl")
        )

        # --- Best site ---
        df_sorted, best_site = best_site_results(screening_results)

        # --- TRANSLATION NEB ---
        ep1_t, ep2_t = select_neb_endpoints_translation(best_site, screening_results)
        images_t, result_t = prepare_neb_calculation(
            ep1_t, ep2_t,
            n_images=10,
            barrier_type='translation',
            workdir=neb_trans_dir
        )

        # --- ROTATION NEB ---
        ep1_r, ep2_r = select_neb_endpoints_rotation(
            best_site, screening_results,
            rotation_angle_diff=120
        )
        images_r, result_r = prepare_neb_calculation(
            ep1_r, ep2_r,
            n_images=10,
            barrier_type='rotation',
            workdir=neb_rot_dir
        )

        return ads_name, {"translation": result_t, "rotation": result_r}

    except Exception as e:
        print(f" Error in adsorbate {ads_name}: {e}")
        return ads_name, None


# ===============================================================
# Run a LIST of adsorbates in PARALLEL
# ===============================================================
def run_adsorbate_list_parallel(adsorbate_list, base_dir="Adsorbates", n_cores=None):
    """
    Runs all adsorbates in parallel using multiprocessing.
    n_cores: number of parallel processes (default = all available CPUs)
    """
    os.makedirs(base_dir, exist_ok=True)

    if n_cores is None:
        n_cores = mp.cpu_count()

    print(f"\n>>> Running {len(adsorbate_list)} adsorbates on {n_cores} cores <<<")

    worker = partial(run_adsorbate_pipeline, base_dir=base_dir)

    with mp.Pool(processes=n_cores) as pool:
        results_list = pool.map(worker, adsorbate_list)

    # Convert list of tuples → dictionary
    results = {ads: res for ads, res in results_list}

    return results


# ===============================================================
# Example Usage
# ===============================================================
if __name__ == "__main__":
    adsorbates = ["CH2", "CH3", "OH", "NH2", "CO", "CO2", "NH3"]
    results = run_adsorbate_list_parallel(adsorbates, base_dir="Adsorbates", n_cores=len(adsorbates))
    print(results)
