# Standard library imports
from pathlib import Path
import shutil
import sys
import tomllib

# Third-party imports
from loguru import logger
import tomli_w

#  Base directory and Bundle directory resolution.
if getattr(sys, 'frozen', False):
    # Running as compiled PyInstaller executable (handles both --onedir and --onefile)
    BASE_DIR = Path(sys.executable).parent.resolve()
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS')).resolve()
else:
    # Running as a standard Python script
    BASE_DIR = Path(__file__).parent.resolve()
    BUNDLE_DIR = Path(__file__).parent.resolve()

def setup_global_logger() -> None:
    """Configures the global logger with both console and file handlers."""
    logger.remove() # Remove default loguru handler

    # Add Console output
    if sys.stderr is not None:
        logger.add(sys.stderr, level="INFO")

    # Add File output
    log_file_path = BASE_DIR / "debug.log"
    logger.add(log_file_path, level="DEBUG", rotation="10 MB")

# Trigger it immediately
setup_global_logger()

# Global path for the active config file
CONFIG_PATH = BASE_DIR / "config.toml"
EXAMPLE_PATH = BASE_DIR / "config.example.toml"

def load_config() -> dict:
    """ Ensure our required files are present before trying to read them"""
    if not CONFIG_PATH.exists():
        # Check for template in BASE_DIR (source code) or BUNDLE_DIR (PyInstaller)
        bundle_example_path = BUNDLE_DIR / "app_data" / "config.example.toml"

        if EXAMPLE_PATH.exists():
            template_to_use = EXAMPLE_PATH
        elif bundle_example_path.exists():
            template_to_use = bundle_example_path
        else:
            logger.critical("No config.toml or config.example.toml found. "
                            "Please create a config.toml based on the project README.")
            sys.exit(1)

        try:
            shutil.copy(template_to_use, CONFIG_PATH)
            logger.info(f"No config.toml found — copied from {template_to_use.name}.")
            logger.warning("Please review config.toml and add your API keys/settings before running.")
        except PermissionError:
            logger.error(f"Permission denied: Cannot write to {BASE_DIR}. "
                         "Please run as Administrator or move the app to a user folder.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to copy config template: {e}")
            sys.exit(1)
    mapping_path = ensure_user_file("mapping.csv")

    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.critical(f"Your config.toml is corrupted or invalidly formatted: {e}")
        sys.exit(1)

    # Validate and resolve the mapping_csv_path from the config, ensuring it exists and is an absolute path
    raw_csv_path = config.get('mapping_csv_path', '')

    if not raw_csv_path:
        # Better Suggestion: Instead of crashing, gracefully fallback to the
        # default mapping.csv we just guaranteed exists next to the exe.
        logger.warning("'mapping_csv_path' missing from config.toml. Using default.")
        config['mapping_csv_path'] = mapping_path
    else:
        # Resolve user-provided path relative to BASE_DIR
        csv_path = Path(raw_csv_path)
        if not csv_path.is_absolute():
            csv_path = BASE_DIR / csv_path

        if not csv_path.exists():
            logger.critical(f"CRITICAL: Required data file missing at {csv_path}")
            sys.exit(1)

        # Store the resolved, absolute Path object back into the config dictionary
        config['mapping_csv_path'] = csv_path

    return config

def load_prompt() -> str:
    """ Ensure prompt.txt is extracted on first run before trying to read it"""
    prompt_path = ensure_user_file("prompt.txt")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def ensure_user_file(filename: str, bundle_subfolder: str = "app_data") -> Path:
    """
    Ensures a user-editable file exists next to the executable.
    Copies the default from the PyInstaller bundle if missing.
    """
    user_path = BASE_DIR / filename

    if not user_path.exists():
        bundle_path = BUNDLE_DIR / bundle_subfolder / filename

        if bundle_path.exists():
            try:
                shutil.copy(bundle_path, user_path)
                logger.info(f"First run setup: Created default '{filename}' in {BASE_DIR}")
            except PermissionError:
                logger.error(f"Permission denied: Cannot write to {BASE_DIR}. "
                             "Please run as Administrator or move the app to a user folder.")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Failed to copy default {filename}: {e}")
                sys.exit(1)
        else:
            logger.critical(f"Build error: Default '{filename}' is missing from the compiled bundle.")
            sys.exit(1)

    return user_path

def save_setting(key, value) -> None:
    """Updates a single key in the TOML file."""
    try:
        # Read existing data so we don't overwrite everything else
        with open(CONFIG_PATH, "rb") as f:
            config_data = tomllib.load(f)

        # Update the specific key
        config_data[key] = value

        # Write back to the TOML file
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(config_data, f)

        logger.debug(f"Successfully saved '{key}' to config.")
    except PermissionError:
        logger.error(f"Permission denied: Could not save setting '{key}'. Check folder permissions.")
    except Exception as e:
        logger.error(f"Failed to save setting '{key}': {e}")

# Expose the validated dictionary and string
# Doing this here means other files can `from config import CONFIG, PROMPT` normally.
CONFIG = load_config()
PROMPT = load_prompt()