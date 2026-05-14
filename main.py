# Standard library imports
import argparse
import sys

# Third-party imports
from loguru import logger

# Local imports
from app.controller import AppController

def parse_args() -> argparse.Namespace:
    """Set up and parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="TOBot - The Belgian Stock-Exchange Tax Toolbox",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Note: More advanced settings (like custom mapping CSV file location or OpenAI endpoint URL) can be controlled via the 'config.toml' file."
    )
    parser.add_argument(
        "-f", "--folder",
        type=str,
        help="Path to the folder containing PDFs to process. If omitted, the GUI will launch."
    )
    parser.add_argument(
        "-a", "--api",
        type=str.lower,
        choices=["mistral", "openai"],
        default="mistral",
        help="API to use ('mistral' for Mistral Cloud, 'openai' for Custom Endpoint)."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="mistral-medium-latest",
        help="AI model to use for extraction, use a correct (non-default) value for custom endpoints."
    )
    parser.add_argument(
        "-e", "--extract-only",
        action="store_true",
        help="Only extract transactions from PDFs; do not perform extra calculation."
    )
    parser.add_argument(
        "-c", "--calc-only",
        action="store_true",
        help="Only perform transaction processing, based on available extracted JSON files."
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point of the application."""
    args = parse_args()

    # Translate the shorter CLI argument to the expected long string
    api_mapping = {
        "mistral": "Mistral Cloud",
        "openai": "Custom Endpoint"
    }
    long_api_name = api_mapping[args.api]

    try:
        # Pass the parsed arguments directly to the controller
        controller = AppController(
            folder_path=args.folder,
            api_choice=long_api_name,
            model_choice=args.model,
            calc_only=args.calc_only,
            extract_only=args.extract_only
        )
        controller.run()

    except KeyboardInterrupt:
        logger.debug("\nApplication closed by user.")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()