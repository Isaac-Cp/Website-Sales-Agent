# Production Startup Script
# Usage: bash setup_production.sh

echo "Setting up production environment..."

# 1. Update and install basic tools
sudo apt-get update
sudo apt-get install -y wget curl unzip gnupg2

# 2. Install Google Chrome for Linux
if ! command -v google-chrome &> /dev/null
then
    echo "Installing Google Chrome..."
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
else
    echo "Google Chrome is already installed."
fi

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create necessary directories
mkdir -p screenshots
mkdir -p debug

echo "Setup complete. You can now run the agent."
