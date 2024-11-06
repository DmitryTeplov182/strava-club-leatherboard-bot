# Strava club - Week's Leaderboard

  
[![https://i.imgur.com/U4Yvb6kl.jpg](https://i.imgur.com/U4Yvb6kl.jpg)](https://github.com/DmitryTeplov182/strava-club-leatherboard-bot)  
  
This Python script scrapes data from the Strava club leaderboard, providing information about the leaders of the previous week. The data is sent to users via a Telegram bot, supporting both [inline](https://core.telegram.org/api/bots/inline) and classic modes. Code uses Selenium to scrape data. So you need to create Strava account for it.  


**DO NOT USE YOUR MAIN STRAVA ACCOUNT HERE. STRAVA CAN BAN YOU FOR SCRAPPING ANY TIME**

Strava is constantly struggling with data parsing. Since November 6, 2024, it's been necessary to use a [undetected_chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver/) and Chrome inside the container with the bot. Also, a VNC server has been added to the container. If you need to use it, uncomment the lines in the docker-compose file. The password is inside the Dockerfile.
## Installation
1. **Install Docker and Docker Compose:**  
Follow the official Docker documentation to install Docker and Docker Compose on your system.
* [Docker Installation Guide](https://docs.docker.com/engine/install/)
* [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)
2. **Download the necessary files:**  
Use `wget` to download the `compose.yaml` and `.env.example` files from the repository.
    ```bash
    wget https://raw.githubusercontent.com/DmitryTeplov182/strava-club-leatherboard-bot/main/compose.yaml
    wget https://raw.githubusercontent.com/DmitryTeplov182/strava-club-leatherboard-bot/main/.env.example -O .env
    ```
3. **Fill in the .env file with your data:**  
Open the `.env` file in a text editor and fill in the required information, such as your Strava login, password, Telegram bot token, and other necessary details.

4. **Start the Docker services:**  
   Run the following command to start the Docker services in detached mode.  
    ```bash
       docker compose up -d
    ```
## Disclaimer
**DO NOT USE YOUR MAIN STRAVA ACCOUNT HERE. STRAVA CAN BAN YOU FOR SCRAPING ANY TIME**  
The author assumes no responsibility for any errors or omissions in the content of this code. The information contained in this code is provided on an "as is" basis with no guarantees of completeness, accuracy, usefulness, or timeliness. The author shall not be liable for any losses, injuries, or damages from the use of this code.
## License  
This project is licensed under the Beerware license. As long as you retain this notice, you can do whatever you want with this stuff. If we meet someday, and you think this stuff is worth it, you can buy me a beer in return.
