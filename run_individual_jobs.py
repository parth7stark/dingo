import subprocess
import os
import time
from concurrent.futures import ThreadPoolExecutor

# Define paths -- take these values from ini file
INIFILE_PATH = "/lus/eagle/projects/RAPINS/parth/Dingo/dingo/my_multiproc_inifile_.ini" 
n_parallel = 4
OUTDIR = "outdir_multiproc_GW200219_094415"  # Change if your outdir is different
OUTPUT_FILE_LABEL = "GW200219_094415"
SUBMIT_SCRIPT = os.path.join(OUTDIR, "submit", f"bash_{OUTPUT_FILE_LABEL}.sh")

# Function to run a shell command with timing and exit code check
def run_command(cmd, description=""):
    """ Run a shell command, print logs in real-time, track execution time, and check exit code. """
    print(f"\n🚀 Starting: {description}...\n{'-' * 80}")
    start_time = time.time()

    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Print logs line by line as they are generated
    for line in iter(process.stdout.readline, ''):
        print(line, end="", flush=True)

    for line in iter(process.stderr.readline, ''):
        print(f"\033[91m{line}\033[0m", end="", flush=True)  # Print stderr in red

    process.wait()
    exit_code = process.returncode
    elapsed_time = time.time() - start_time

    print(f"\n✅ Finished: {description} in {elapsed_time:.2f} seconds.{'-' * 80}")

    if exit_code != 0:
        print(f"\n❌ ERROR in {description}! Exit code: {exit_code}\n{'-' * 80}")
        exit(exit_code)  # Stop execution if a command fails

    return elapsed_time

# Step 1: Run dingo_pipe to generate submission scripts
run_command(f"dingo_pipe {INIFILE_PATH}", "Initializing dingo_pipe")

# Step 2: Run data generation and sampling sequentially
run_command(f"bash {SUBMIT_SCRIPT} generation", "Data Generation")
run_command(f"bash {SUBMIT_SCRIPT} analysis", "Sampling")

# Step 3: Run all importance sampling jobs in parallel
print("\n Running importance sampling in parallel...\n")
importance_jobs = [f"bash {SUBMIT_SCRIPT} par{i}" for i in range(n_parallel)]  # Adjust range based on actual job count

def run_importance_job(job_cmd):
    return run_command(job_cmd, description=f"Importance Sampling ({job_cmd.split()[-1]})")

with ThreadPoolExecutor(max_workers=len(importance_jobs)) as executor:
    futures = {executor.submit(run_importance_job, job): job for job in importance_jobs}

    for future in futures:
        try:
            future.result()  # Wait for all jobs to complete
        except SystemExit as e:
            print(f"\n Stopping execution due to failure in {futures[future]}!")
            exit(e.code)

# Step 4: Merge results
run_command(f"bash {SUBMIT_SCRIPT} merge", "Merging Results")

# Step 5: Run final results command
run_command(f"bash {SUBMIT_SCRIPT} results", "Generating Final Results")

print("\n All dingo_pipe jobs completed successfully!\n")
