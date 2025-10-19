FROM phocean/msf

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

COPY "entrypoint.sh" .

RUN apt-get update && \
 	apt-get install -y \
					git \
					python3 \
					python3-dev \
					python3-pip \
					python3-venv \
					apache2 \
					curl \
					wget

# Upgrade pip to latest version
RUN python3 -m pip install --upgrade pip

RUN chmod +x entrypoint.sh && \
	git clone https://github.com/NullArray/AutoSploit.git && \
	python3 -m pip install -r AutoSploit/requirements.txt

# Create necessary directories
RUN mkdir -p /root/.autosploit_home/backups \
    /root/.autosploit_home/nmap_scans/xml \
    /root/.autosploit_home/nmap_scans/json \
    /root/.autosploit_home/autosploit_out \
    /root/.autosploit_home/.autosploit_errors \
    AutoSploit/etc/tokens
	
EXPOSE 4444
CMD [ "./entrypoint.sh" ]
