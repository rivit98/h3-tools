import asyncio
from argparse import ArgumentParser

from executor.executor import executor_main

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()

    asyncio.run(executor_main(args.port))
