"""
CLI entry point for efemel.
"""

import argparse

from .main import hello_world


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Efemel CLI application")
    parser.add_argument(
        "--version",
        action="version",
        version=f"efemel {__import__('efemel').__version__}",
    )
    parser.add_argument(
        "--hello", action="store_true", help="Print hello world message"
    )

    args = parser.parse_args()

    if args.hello:
        print(hello_world())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
