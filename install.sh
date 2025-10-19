#!/bin/bash

# AutoSploit Install Script - Python 3.12 Compatible
# Author: NullArray
# License: GPL v3.0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "  ____  __ __  ______   ___   _____ ____  _       ___  ____  ______ ";
echo " /    ||  |  ||      | /   \ / ___/|    \| |     /   \|    ||      |";
echo "|  o  ||  |  ||      ||     (   \_ |  o  ) |    |     ||  | |      |";
echo "|     ||  |  ||_|  |_||  O  |\__  ||   _/| |___ |  O  ||  | |_|  |_|";
echo "|  _  ||  :  |  |  |  |     |/  \ ||  |  |     ||     ||  |   |  |  ";
echo "|  |  ||     |  |  |  |     |\    ||  |  |     ||     ||  |   |  |  ";
echo "|__|__| \__,_|  |__|   \___/  \___||__|  |_____| \___/|____|  |__|  ";
echo "                                                                    ";
echo -e "${GREEN}[+] AutoSploit Installation Script (Python 3.12 Compatible)${NC}"
echo -e "${GREEN}[+] Author: NullArray${NC}"
echo -e "${GREEN}[+] License: GPL v3.0${NC}"
echo ""

function installDebian () {
    echo -e "${GREEN}[+] Installing dependencies for Debian/Ubuntu...${NC}"
    sudo apt-get update;
    sudo apt-get -y install git python3 python3-pip python3-venv postgresql apache2 nmap;
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}[+] Python version: $PYTHON_VERSION${NC}"
    
    # Install Python packages
    echo -e "${GREEN}[+] Installing Python packages...${NC}"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    # Create necessary directories
    createDirectories;
    installMSF;
}

function installFedora () {
    echo -e "${GREEN}[+] Installing dependencies for Fedora...${NC}"
    sudo dnf -y install git python3 python3-pip postgresql apache2 nmap;
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}[+] Python version: $PYTHON_VERSION${NC}"
    
    # Install Python packages
    echo -e "${GREEN}[+] Installing Python packages...${NC}"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    # Create necessary directories
    createDirectories;
    installMSF;
}

function installOSX () {
    echo -e "${GREEN}[+] Installing dependencies for macOS...${NC}"
    xcode-select --install;
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)";
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile;
    eval "$(/opt/homebrew/bin/brew shellenv)";
    brew install python3 nmap postgresql;
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}[+] Python version: $PYTHON_VERSION${NC}"
    
    # Install Python packages
    echo -e "${GREEN}[+] Installing Python packages...${NC}"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    # Setup PostgreSQL
    brew services start postgresql;
    createuser msf -P -h localhost;
    createdb -O msf msf -h localhost;
    
    # Create necessary directories
    createDirectories;
    installOsxMSF;
}

function installOsxMSF () {
  mkdir /usr/local/share;
  cd /usr/local/share/;
  git clone https://github.com/rapid7/metasploit-framework.git;
  cd metasploit-framework;
  for MSF in $(ls msf*); do ln -s /usr/local/share/metasploit-framework/$MSF /usr/local/bin/$MSF;done;
  sudo chmod go+w /etc/profile;
  sudo echo export MSF_DATABASE_CONFIG=/usr/local/share/metasploit-framework/config/database.yml >> /etc/profile;
  bundle install;
  echo "[!!] A DEFAULT CONFIG OF THE FILE 'database.yml' WILL BE USED";
  rm /usr/local/share/metasploit-framework/config/database.yml;
  cat > /usr/local/share/metasploit-framework/config/database.yml << '_EOF'
production:
  adapter: postgresql
  database: msf
  username: msf
  password:
  host: 127.0.0.1
  port: 5432
  pool: 75
  timeout: 5
_EOF
  source /etc/profile;
  source ~/.bash_profile;
}

function installMSF () {
    if [[ ! "$(which msfconsole)" = */* ]]; then
        curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && \
            chmod 755 msfinstall && \
            ./msfinstall;
        rm msfinstall;
    fi
}

function createDirectories () {
    echo -e "${GREEN}[+] Creating necessary directories...${NC}"
    mkdir -p ~/.autosploit_home/backups
    mkdir -p ~/.autosploit_home/nmap_scans/xml
    mkdir -p ~/.autosploit_home/nmap_scans/json
    mkdir -p ~/.autosploit_home/autosploit_out
    mkdir -p ~/.autosploit_home/.autosploit_errors
    mkdir -p etc/tokens
    
    # Set permissions
    chmod +x autosploit.py
    chmod +x quicksploit.sh
    chmod +x runsploit.sh
    chmod +x drysploit.sh
    
    # Create sample configuration files
    echo -e "${GREEN}[+] Creating sample configuration files...${NC}"
    if [ ! -f "etc/tokens/shodan.key" ]; then
        echo "# Add your Shodan API key here" > etc/tokens/shodan.key
        echo -e "${YELLOW}[!] Please add your Shodan API key to etc/tokens/shodan.key${NC}"
    fi
    
    if [ ! -f "etc/tokens/censys.key" ]; then
        echo "# Add your Censys API key here" > etc/tokens/censys.key
        echo -e "${YELLOW}[!] Please add your Censys API key to etc/tokens/censys.key${NC}"
    fi
    
    if [ ! -f "etc/tokens/censys.id" ]; then
        echo "# Add your Censys API ID here" > etc/tokens/censys.id
        echo -e "${YELLOW}[!] Please add your Censys API ID to etc/tokens/censys.id${NC}"
    fi
}

function install () {
    case "$(uname -a)" in
        *Debian*|*Ubuntu*)
            installDebian;
            ;;
        *Fedora*)
            installFedora;
            ;;
        *Darwin*)
            installOSX;
            ;;
        *)
            echo -e "${RED}[!] Unable to detect an operating system that is compatible with AutoSploit...${NC}";
            exit 1;
            ;;
    esac
    
    echo "";
    echo -e "${GREEN}[+] Installation completed successfully!${NC}"
    echo -e "${GREEN}[+] You can now run AutoSploit with: python3 autosploit.py${NC}"
    echo -e "${YELLOW}[!] Remember to configure your API keys in etc/tokens/ directory${NC}"
    echo -e "${BLUE}[i] For help, run: python3 autosploit.py --help${NC}"
}

install;
