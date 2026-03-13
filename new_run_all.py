import subprocess
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("overall_run.log"),
        logging.StreamHandler()
    ]
)

def main():
    start_time = datetime.now()
    logging.info(f"Parallel scraping process started at {start_time}")

    # List of scrapers to run
    scrapers = [
        "scraper.py",             # TopBoats
        "boat24_scraper.py",      # Boat24
        "mondialbroker_scraper.py",# MondialBroker
        "yachtall_scraper.py",    # Yachtall
        "prepare_navisnet.py"     # Navisnet
    ]

    # We use the venv python interpreter
    venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable # fallback

    processes = []
    
    # Open a single output file for all processes or separate ones
    with open("output.log", "a") as out_file:
        for scraper in scrapers:
            if os.path.exists(scraper):
                logging.info(f"Launching {scraper} in parallel...")
                # Redirect BOTH stdout and stderr to the log file to avoid deadlocks
                p = subprocess.Popen([venv_python, scraper], stdout=out_file, stderr=subprocess.STDOUT, text=True)
                processes.append((scraper, p))
            else:
                logging.warning(f"Scraper {scraper} not found in current directory.")

    # Wait for all scrapers to complete
    logging.info(f"Waiting for {len(processes)} scrapers to finish...")
    for scraper_name, p in processes:
        p.wait()
        if p.returncode == 0:
            logging.info(f"Finished {scraper_name} successfully.")
        else:
            logging.error(f"Scraper {scraper_name} failed with exit code {p.returncode}.")

    # Run normalization only after all are done
    if any(f.endswith(".json") for f in os.listdir(".")):
        logging.info("All scrapers finished. Starting data normalization...")
        try:
            subprocess.run([venv_python, "normalize_data.py"], check=True)
            logging.info("Normalization completed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Normalization failed: {e}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Full parallel process completed at {end_time}. Total duration: {duration}")

if __name__ == "__main__":
    main()
