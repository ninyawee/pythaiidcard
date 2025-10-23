"""System dependency checking for Thai ID Card reader."""

import logging
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SystemDependency:
    """Represents a system dependency."""

    def __init__(self, name: str, package_name: str, check_file: Optional[str] = None):
        """Initialize a system dependency.

        Args:
            name: Human-readable name of the dependency
            package_name: Apt package name
            check_file: Optional file path to verify installation
        """
        self.name = name
        self.package_name = package_name
        self.check_file = check_file

    def is_installed(self) -> bool:
        """Check if this dependency is installed.

        Returns:
            True if dependency is satisfied, False otherwise
        """
        try:
            import apt_pkg

            apt_pkg.init()
            cache = apt_pkg.Cache()

            if self.package_name not in cache:
                return False

            pkg = cache[self.package_name]
            is_installed = pkg.current_state == apt_pkg.CURSTATE_INSTALLED

            # Additional file check if specified
            if is_installed and self.check_file:
                return Path(self.check_file).exists()

            return is_installed

        except ImportError:
            # apt_pkg not available, fall back to file check
            if self.check_file:
                return Path(self.check_file).exists()
            # Can't verify without apt_pkg
            logger.warning(f"Cannot verify {self.name} - apt_pkg not available")
            return True  # Assume installed if we can't check
        except Exception as e:
            logger.debug(f"Error checking {self.name}: {e}")
            return False


# Required system dependencies
REQUIRED_DEPENDENCIES = [
    SystemDependency(
        name="PC/SC Smart Card Daemon",
        package_name="pcscd",
        check_file=None
    ),
    SystemDependency(
        name="PC/SC Lite development library",
        package_name="libpcsclite-dev",
        check_file="/usr/include/PCSC/winscard.h"
    ),
    SystemDependency(
        name="Python development headers",
        package_name="python3-dev",
        check_file=None  # Don't check file - pyscard installation verifies this
    ),
    SystemDependency(
        name="SWIG (for Python bindings)",
        package_name="swig",
        check_file=None
    ),
]


def check_system_dependencies(skip_check: bool = False) -> Dict[str, List[SystemDependency]]:
    """Check if all required system dependencies are installed.

    Args:
        skip_check: If True, skip the check and return empty results

    Returns:
        Dict with 'missing' and 'installed' lists of dependencies
    """
    if skip_check:
        return {"missing": [], "installed": REQUIRED_DEPENDENCIES}

    missing = []
    installed = []

    for dep in REQUIRED_DEPENDENCIES:
        if dep.is_installed():
            installed.append(dep)
            logger.debug(f"✓ {dep.name} is installed")
        else:
            missing.append(dep)
            logger.debug(f"✗ {dep.name} is missing")

    return {"missing": missing, "installed": installed}


def get_install_command(missing_deps: List[SystemDependency]) -> Optional[str]:
    """Generate installation command for missing dependencies.

    Args:
        missing_deps: List of missing dependencies

    Returns:
        Installation command string or None if not applicable
    """
    if not missing_deps:
        return None

    system = platform.system().lower()

    if system == "linux" and shutil.which("apt-get"):
        packages = " ".join(dep.package_name for dep in missing_deps)
        return f"sudo apt-get update && sudo apt-get install -y {packages}"

    return None


def format_missing_dependencies_message(missing_deps: List[SystemDependency]) -> str:
    """Format a helpful error message for missing dependencies.

    Args:
        missing_deps: List of missing dependencies

    Returns:
        Formatted error message
    """
    if not missing_deps:
        return ""

    lines = [
        "Missing required system dependencies:",
        ""
    ]

    for dep in missing_deps:
        lines.append(f"  ✗ {dep.name} ({dep.package_name})")

    lines.append("")

    install_cmd = get_install_command(missing_deps)
    if install_cmd:
        lines.append("To install missing dependencies, run:")
        lines.append("")
        lines.append(f"  {install_cmd}")
    else:
        lines.append("Please install the missing dependencies using your system's package manager.")
        lines.append("")
        packages = ", ".join(dep.package_name for dep in missing_deps)
        lines.append(f"Required packages: {packages}")

    lines.append("")
    lines.append("For more information, see the README Prerequisites section.")

    return "\n".join(lines)


def check_and_raise_if_missing(skip_check: bool = False) -> None:
    """Check system dependencies and raise exception if any are missing.

    Args:
        skip_check: If True, skip the check entirely

    Raises:
        SystemDependencyError: If required dependencies are missing
    """
    if skip_check:
        return

    # Only check on Linux systems
    system = platform.system().lower()
    if system != "linux":
        logger.debug("Skipping system dependency check (not a Linux system)")
        return

    # First, check if pyscard can be imported - this is the ultimate test
    try:
        import smartcard.System
        logger.debug("✓ pyscard is working (dependencies satisfied)")
        return  # If pyscard works, all dependencies are satisfied
    except ImportError as e:
        logger.debug(f"pyscard import failed: {e}")
        # Continue with system check
    except Exception as e:
        logger.debug(f"pyscard check failed: {e}")
        # Continue with system check

    result = check_system_dependencies(skip_check=False)
    missing = result["missing"]

    if missing:
        from .exceptions import SystemDependencyError
        message = format_missing_dependencies_message(missing)
        raise SystemDependencyError(message, missing)

    logger.debug("All system dependencies are installed")
