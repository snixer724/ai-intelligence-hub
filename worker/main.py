# main.py
import logging
import sys
from worker import run_worker

# 1. Initialize the global logging configuration ONCE at launch
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("main")

def main() -> None:
    logger.info("System boot sequence initiated.")
    
    # Optional: Add system health checks here (e.g., test DB connection, verify Redis is up)
    
    logger.info("Handing off execution flow to background worker queue...")
    
    # 2. Kick off the blocking while-True loop inside worker.py
    run_worker()

if __name__ == '__main__':
    main()