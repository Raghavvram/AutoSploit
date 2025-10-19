#!/usr/bin/env python3
"""
AutoSploit Settings Module
Modernized for Python 3.12
"""

import os
import re
import sys
import time
import socket
import random
import platform
import getpass
import tempfile
import shutil
import threading
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Dict, List, Optional, Tuple, Union

import psutil

# Import local modules
try:
    import lib.output as lib_output
    import lib.banner as lib_banner
    import lib.jsonize as lib_jsonize
except ImportError:
    # Handle relative imports
    from . import output as lib_output
    from . import banner as lib_banner
    from . import jsonize as lib_jsonize


class AutoSploitCompleter:
    """Auto completer for the terminal interface."""

    def __init__(self, opts: List[str]):
        self.opts = sorted(opts)
        self.possibles: List[str] = []

    def complete_text(self, text: str, state: int) -> Optional[str]:
        """Complete text based on available options."""
        if state == 0:
            if text:
                self.possibles = [m for m in self.opts if m.startswith(text)]
            else:
                self.possibles = self.opts[:]
        try:
            return self.possibles[state]
        except IndexError:
            return None


TERMINAL_HELP_MESSAGE = """
COMMAND:                SUMMARY:
---------               --------
view/show               Show the already gathered hosts
mem[ory]/history        Display the command history
exploit/run/attack      Run the exploits on the already gathered hosts
search/api/gather       Search the API's for hosts
exit/quit               Exit the terminal session
single                  Load a single host into the file, or multiple hosts separated by a comma (1,2,3,..)
personal/custom         Load a custom host file
tokens/reset            Reset API tokens if needed
external                View loaded external commands
ver[sion]               View the current version of the program
clean/clear             Clean the hosts.txt file of duplicate IP addresses
help/?                  Display this help
"""

# Current directory
CUR_DIR = str(Path.cwd())

# Home directory
HOME = str(Path.home() / ".autosploit_home")

# Backup the current hosts file
HOST_FILE_BACKUP = str(Path(HOME) / "backups")

# AutoSploit command history file path
HISTORY_FILE_PATH = str(Path(HOME) / ".history")

# Save the scans XML output for future use
NMAP_XML_OUTPUT_BACKUP = str(Path(HOME) / "nmap_scans" / "xml")

# Dump the generated dict data into JSON and save it into a file
NMAP_JSON_OUTPUT_BACKUP = str(Path(HOME) / "nmap_scans" / "json")

# Regex to discover errors or warnings
NMAP_ERROR_REGEX_WARNING = re.compile(r"^warning: .*", re.IGNORECASE)

# Possible options in nmap
NMAP_OPTIONS_PATH = str(Path(CUR_DIR) / "etc" / "text_files" / "nmap_opts.lst")

# Possible paths for nmap
NMAP_POSSIBLE_PATHS = (
    'nmap', '/usr/bin/nmap', '/usr/local/bin/nmap', '/sw/bin/nmap', '/opt/local/bin/nmap'
)

# Link to the checksums
try:
    with open(str(Path(CUR_DIR) / "etc" / "text_files" / "checksum_link.txt"), 'r') as f:
        CHECKSUM_LINK = f.read().strip()
except FileNotFoundError:
    CHECKSUM_LINK = ""

# Path to the file containing all the discovered hosts
HOST_FILE = str(Path(CUR_DIR) / "hosts.txt")
Path(HOST_FILE).touch(exist_ok=True)

# Path to the folder containing all the JSON exploit modules
EXPLOIT_FILES_PATH = str(Path(CUR_DIR) / "etc" / "json")

# Path to the usage and legal file
USAGE_AND_LEGAL_PATH = str(Path(CUR_DIR) / "etc" / "text_files" / "general")

# One bash script to rule them all takes an argument via the operating system
START_SERVICES_PATH = str(Path(CUR_DIR) / "etc" / "scripts" / "start_services.sh")

# Path where we will keep the rc scripts
RC_SCRIPTS_PATH = str(Path(HOME) / "autosploit_out")

# Path to the file that will contain our query
QUERY_FILE_PATH = tempfile.NamedTemporaryFile(delete=False).name

# Default HTTP User-Agent
try:
    DEFAULT_USER_AGENT = f"AutoSploit/{lib_banner.VERSION} (Language=Python/{sys.version.split(' ')[0]}; Platform={platform.platform().split('-')[0]})"
except (AttributeError, ImportError, NameError):
    DEFAULT_USER_AGENT = f"AutoSploit/4.0 (Language=Python/{sys.version.split(' ')[0]}; Platform={platform.platform().split('-')[0]})"

# The prompt for the platforms
PLATFORM_PROMPT = f"\n{getpass.getuser()}@\033[36mPLATFORM\033[0m$ "

# The prompt that will be used most of the time
AUTOSPLOIT_PROMPT = f"\033[31m{getpass.getuser()}\033[0m@\033[36mautosploit\033[0m# "

# All the paths to the API tokens
API_KEYS = {
    "censys": (
        str(Path(CUR_DIR) / "etc" / "tokens" / "censys.key"),
        str(Path(CUR_DIR) / "etc" / "tokens" / "censys.id")
    ),
    "shodan": (str(Path(CUR_DIR) / "etc" / "tokens" / "shodan.key"),)
}

# All the URLs that we will use while doing the searching
API_URLS = {
    "shodan": "https://api.shodan.io/shodan/host/search?key={token}&query={query}",
    "censys": "https://censys.io/api/v1/search/ipv4",
    "zoomeye": (
        "https://api.zoomeye.org/user/login",
        "https://api.zoomeye.org/web/search"
    )
}

# Has MSF been launched?
MSF_LAUNCHED = False

# Token path for issue requests
TOKEN_PATH = str(Path(CUR_DIR) / "etc" / "text_files" / "auth.key")

# Location of error files
ERROR_FILES_LOCATION = str(Path(HOME) / ".autosploit_errors")

# Terminal options
AUTOSPLOIT_TERM_OPTS = {
    1: "usage and legal", 2: "gather hosts", 3: "custom hosts",
    4: "add single host", 5: "view gathered hosts", 6: "exploit gathered hosts",
    99: "quit"
}

# Global variable for the search animation
stop_animation = False


def load_external_commands() -> List[str]:
    """Create a list of external commands from provided directories."""
    paths = ["/bin", "/usr/bin"]
    loaded_externals = []
    for path_dir in paths:
        try:
            for cmd in os.listdir(path_dir):
                cmd_path = Path(path_dir) / cmd
                if cmd_path.is_file() and os.access(cmd_path, os.X_OK):
                    loaded_externals.append(cmd)
        except (OSError, PermissionError):
            continue
    return loaded_externals


def backup_host_file(current: str, path: str) -> str:
    """Backup the current hosts file."""
    import datetime

    Path(path).mkdir(parents=True, exist_ok=True)
    new_filename = str(Path(path) / f"hosts_{lib_jsonize.random_file_name(length=22)}_{datetime.date.today()}.txt")
    shutil.copy2(current, new_filename)
    return new_filename


def auto_completer(keywords: List[str]) -> None:
    """Initialize the auto complete utility."""
    try:
        import readline
        completer = AutoSploitCompleter(keywords)
        readline.set_completer(completer.complete_text)
        readline.parse_and_bind('tab: complete')
    except ImportError:
        # readline not available on this platform
        pass


def validate_ip_addr(provided: str, home_ok: bool = False) -> bool:
    """Validate an IP address to see if it is real or not."""
    if not home_ok:
        not_acceptable = ("0.0.0.0", "127.0.0.1", "255.255.255.255")
    else:
        not_acceptable = ("255.255.255.255",)

    if provided not in not_acceptable:
        try:
            socket.inet_aton(provided)
            return True
        except OSError:
            return False
    return False


def check_services(service_name: str) -> bool:
    """Check to see if certain services are started."""
    try:
        all_processes = set()
        for pid in psutil.pids():
            try:
                running_proc = psutil.Process(pid)
                all_processes.add(" ".join(running_proc.cmdline()).strip())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for proc in all_processes:
            if service_name in proc:
                return True
        return False
    except psutil.ZombieProcess as e:
        # Zombie processes appear to happen on macOS for some reason
        # so we'll just kill them off
        try:
            pid = str(e).split("=")[-1].split(")")[0]
            os.kill(int(pid), 0)
        except (ValueError, OSError):
            pass
        return True


def write_to_file(data_to_write: Union[str, list, set, tuple], filename: str, mode: Optional[str] = None) -> str:
    """Write data to a specified file, if it exists, ask to overwrite."""
    global stop_animation

    if Path(filename).exists():
        if not mode:
            stop_animation = True
            is_append = lib_output.prompt("would you like to (a)ppend or (o)verwrite the file")
            if is_append.lower() == "o":
                mode = "w"
            elif is_append.lower() == "a":
                mode = "a+"
            else:
                lib_output.error(f"invalid input provided ('{is_append}'), appending to file")
                lib_output.error("Search results NOT SAVED!")

        if mode == "w":
            lib_output.warning(f"Overwriting to {filename}")
        if mode == "a":
            lib_output.info(f"Appending to {filename}")
    else:
        # File does not exist, mode does not matter
        mode = "w"

    with open(filename, mode, encoding='utf-8') as log:
        if isinstance(data_to_write, (tuple, set, list)):
            for item in data_to_write:
                log.write(f"{str(item).strip()}{os.linesep}")
        else:
            log.write(str(data_to_write))

    lib_output.info(f"successfully wrote info to '{filename}'")
    return filename


def load_api_keys(unattended: bool = False, path: Optional[str] = None) -> Dict[str, Tuple[str, ...]]:
    """Load the API keys from their .key files."""
    if path is None:
        path = str(Path(CUR_DIR) / "etc" / "tokens")

    # Make the directory if it does not exist
    Path(path).mkdir(parents=True, exist_ok=True)

    for key in API_KEYS.keys():
        if not Path(API_KEYS[key][0]).is_file():
            access_token = lib_output.prompt(f"enter your {key.title()} API token", lowercase=False)
            if key.lower() == "censys":
                identity = lib_output.prompt(f"enter your {key.title()} ID", lowercase=False)
                with open(API_KEYS[key][1], "a+", encoding='utf-8') as log:
                    log.write(identity)
            with open(API_KEYS[key][0], "a+", encoding='utf-8') as log:
                log.write(access_token.strip())
        else:
            lib_output.info(f"{key.title()} API token loaded from {API_KEYS[key][0]}")

    api_tokens = {
        "censys": (
            Path(API_KEYS["censys"][0]).read_text(encoding='utf-8').rstrip(),
            Path(API_KEYS["censys"][1]).read_text(encoding='utf-8').rstrip()
        ),
        "shodan": (Path(API_KEYS["shodan"][0]).read_text(encoding='utf-8').rstrip(),)
    }
    return api_tokens


def cmdline(command: str, is_msf: bool = True) -> List[str]:
    """Send the commands through subprocess."""
    lib_output.info(f"Executing command '{command.strip()}'")
    split_cmd = [x.strip() for x in command.split(" ") if x]

    sys.stdout.flush()
    stdout_buff = []

    try:
        proc = Popen(split_cmd, stdout=PIPE, bufsize=1, text=True)
        for stdout_line in iter(proc.stdout.readline, ''):
            stdout_buff.append(stdout_line.rstrip())
            if is_msf:
                print(f"(msf)>> {stdout_line.rstrip()}")
            else:
                print(stdout_line.rstrip())
    except OSError as e:
        stdout_buff.append(f"ERROR: {e}")

    return stdout_buff


def check_for_msf() -> Optional[str]:
    """Check the ENV PATH for msfconsole."""
    import shutil
    return os.getenv("msfconsole") or shutil.which("msfconsole")


def logo() -> None:
    """Display a random banner from the banner.py file."""
    print(lib_banner.banner_main())


def animation(text: str) -> None:
    """Display an animation while working, single threaded."""
    global stop_animation
    i = 0
    while not stop_animation:
        temp_text = list(text)
        if i >= len(temp_text):
            i = 0
        temp_text[i] = temp_text[i].upper()
        temp_text = ''.join(temp_text)
        sys.stdout.write(f"\033[96m\033[1m{temp_text}...\r\033[0m")
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)


def start_animation(text: str) -> None:
    """Start the animation until stop_animation is False."""
    global stop_animation

    if not stop_animation:
        t = threading.Thread(target=animation, args=(text,), daemon=True)
        t.start()
    else:
        lib_output.misc_info(text)


def close(warning: str, status: int = 1) -> None:
    """Exit if there's an issue."""
    lib_output.error(warning)
    sys.exit(status)


def grab_random_agent() -> str:
    """Get a random HTTP User-Agent."""
    user_agent_path = Path(CUR_DIR) / "etc" / "text_files" / "agents.txt"
    try:
        with open(user_agent_path, 'r', encoding='utf-8') as agents:
            return random.choice(agents.readlines()).strip()
    except FileNotFoundError:
        return DEFAULT_USER_AGENT


def configure_requests(proxy: Optional[str] = None, agent: Optional[str] = None, rand_agent: bool = False) -> Tuple[Optional[Dict[str, str]], Dict[str, str]]:
    """Configure the proxy and User-Agent for the requests."""
    if proxy is not None:
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        lib_output.misc_info(f"setting proxy to: '{proxy}'")
    else:
        proxy_dict = None

    if agent is not None:
        header_dict = {
            "User-Agent": agent
        }
        lib_output.misc_info(f"setting HTTP User-Agent to: '{agent}'")
    elif rand_agent:
        header_dict = {
            "User-Agent": grab_random_agent()
        }
        lib_output.misc_info(f"setting HTTP User-Agent to: '{header_dict['User-Agent']}'")
    else:
        header_dict = {
            "User-Agent": DEFAULT_USER_AGENT
        }

    return proxy_dict, header_dict


def save_error_to_file(error_info: str, error_message: str, error_class: str) -> str:
    """Save an error traceback to log file for further use."""
    import string

    Path(ERROR_FILES_LOCATION).mkdir(parents=True, exist_ok=True)
    acceptable = string.ascii_letters
    filename = ''.join(random.choice(acceptable) for _ in range(12)) + "_AS_error.txt"
    file_path = str(Path(ERROR_FILES_LOCATION) / filename)

    with open(file_path, "a+", encoding='utf-8') as log:
        log.write(f"Traceback (most recent call):\n {error_info.strip()}\n{error_class}: {error_message}")

    return file_path


def download_modules(link: str) -> str:
    """Download new module links."""
    import re
    import requests
    import tempfile

    lib_output.info(f'downloading: {link}')
    retval = ""
    req = requests.get(link)
    content = req.text
    split_data = content.split(" ")
    searcher = re.compile(r"exploit/\w+/\w+")
    storage_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')

    for item in split_data:
        if searcher.search(item) is not None:
            retval += item + "\n"

    storage_file.write(retval)
    storage_file.close()
    return storage_file.name


def find_similar(command: str, internal: List[str], external: List[str]) -> List[str]:
    """Find commands similar to the one provided."""
    retval = []
    if not command:
        return retval

    first_char = command[0]
    for inter in internal:
        if inter.startswith(first_char):
            retval.append(inter)
    for exter in external:
        if exter.startswith(first_char):
            retval.append(exter)
    return retval
