#!/usr/bin/env python3
"""
AutoSploit Main Module
Modernized for Python 3.12
"""

import os
import sys
import ctypes
import psutil
import platform
import traceback

from lib.cmdline.cmd import AutoSploitParser
from lib.term.terminal import AutoSploitTerminal
from lib.output import (
    info,
    prompt,
    misc_info
)
from lib.settings import (
    logo,
    load_api_keys,
    check_services,
    cmdline,
    close,
    EXPLOIT_FILES_PATH,
    START_SERVICES_PATH,
    save_error_to_file
)
from lib.jsonize import (
    load_exploits,
    load_exploit_file
)


def main():
    """Main entry point for AutoSploit."""
    try:
        # Check for admin privileges
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            # Cross-platform admin check for Windows
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except AttributeError:
                # Fallback for other platforms
                is_admin = True  # Assume admin for non-Windows platforms

        # Allow help, version, and dry run to be shown without admin privileges
        if not is_admin and len(sys.argv) > 1 and any(arg in sys.argv for arg in ['--help', '-h', 'help', '--version', '-v', 'version', '--dry-run', '-d']):
            pass  # Allow help, version, and dry run to be shown
        elif not is_admin:
            close("must have admin privileges to run")

        opts = AutoSploitParser().optparser()

        logo()
        info("welcome to autosploit, give us a little bit while we configure")
        misc_info("checking your running platform")
        platform_running = platform.system()
        misc_info("checking for disabled services")

        # Check for required services (postgres, apache2)
        service_names = ("postgres", "apache2")
        try:
            for service in service_names:
                while not check_services(service):
                    if "darwin" in platform_running.lower():
                        info(
                            "seems you're on macOS, skipping service checks "
                            "(make sure that Apache2 and PostgreSQL are running)"
                        )
                        break
                    choice = prompt(
                        f"it appears that service {service.title()} is not enabled, "
                        "would you like us to enable it for you[y/N]"
                    )
                    if choice.lower().startswith("y"):
                        try:
                            if "linux" in platform_running.lower():
                                cmdline(f"{START_SERVICES_PATH} linux")
                            else:
                                close("your platform is not supported by AutoSploit at this time", status=2)

                            info("services started successfully")
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        process_start_command = f"`sudo service {service} start`"
                        if "darwin" in platform_running.lower():
                            process_start_command = f"`brew services start {service}`"
                        close(
                            f"service {service.title()} is required to be started for autosploit to run successfully "
                            f"(you can do it manually by using the command {process_start_command}), exiting"
                        )
        except Exception:
            pass

        # Handle command line arguments or start interactive mode
        if len(sys.argv) > 1:
            info("attempting to load API keys")
            loaded_tokens = load_api_keys()
            AutoSploitParser().parse_provided(opts)

            if not opts.exploitFile:
                misc_info("checking if there are multiple exploit files")
                loaded_exploits = load_exploits(EXPLOIT_FILES_PATH)
            else:
                loaded_exploits = load_exploit_file(opts.exploitFile)
                misc_info(f"Loaded {len(loaded_exploits)} exploits from {opts.exploitFile}.")

            AutoSploitParser().single_run_args(opts, loaded_tokens, loaded_exploits)
        else:
            misc_info("checking if there are multiple exploit files")
            loaded_exploits = load_exploits(EXPLOIT_FILES_PATH)
            info("attempting to load API keys")
            loaded_tokens = load_api_keys()
            terminal = AutoSploitTerminal(loaded_tokens, loaded_exploits)
            terminal.terminal_main_display(loaded_tokens)

    except Exception as e:
        global stop_animation
        stop_animation = True

        print(
            f"\033[31m[!] AutoSploit has hit an unhandled exception: '{e}', "
            "in order for the developers to troubleshoot and repair the "
            "issue AutoSploit will need to gather your OS information, "
            "current arguments, the error message, and a traceback. "
            "None of this information can be used to identify you in any way\033[0m"
        )
        error_traceback = ''.join(traceback.format_tb(sys.exc_info()[2]))
        try:
            error_class = e.__class__.__name__
        except IndexError:
            error_class = str(e.__class__).split("'")[1] if "'" in str(e.__class__) else "UnknownError"
        error_file = save_error_to_file(str(error_traceback), str(e), error_class)
        print(error_traceback)
        # request_issue_creation(error_file, hide_sensitive(), str(e))
