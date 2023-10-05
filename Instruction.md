## To start bot on a Google Cloud machine

# Installing Git
sudo apt-get update
sudo apt-get install git

# Clone the code
git clone https://github.com/doanhaivu/chatgpt_telegram_bot

# Add Docker's official GPG key: (https://docs.docker.com/engine/install/debian/#install-using-the-repository)

sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Just to test docker is running properly
sudo docker run hello-world

# Setting env vars

echo -e "\nTELEGRAM_BOT_TOKEN=your telegram token" | tee -a config/config.env
echo -e "\nOPENAI_API_KEY=your openai api key" | tee -a config/config.env

# Start the bot
sudo docker compose --env-file config/config.env up --build -e
OR sudo docker compose --env-file config/config.env up --build