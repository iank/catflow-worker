import asyncio
import argparse
from .main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", default="#", help="Topic key to bind")
    args = parser.parse_args()

    asyncio.run(main(args.topics))
