# 🚦 Traffic Light

Traffic Light is a webserver that takes in data from VMs Traffic Mode and formats it nicely. It acts as a debugger for the game, so developers can more easily follow the game traffic and understand how things work.

It can either send to Discord or print to console. Output pictured below. Usually, Discord is better to view the data, while console output works better to understand what's going on.

![img.png](readme_assets/discord.png)

![img.png](readme_assets/log.png)

## Setup

- It's made to be used on your local computer with a local phone
- Clone repo, install requirements, copy `config.example.py` to `config.py`, fill out config
- Open VM on your phone. Set Scanmode to `2`. Set POST destination to your endpoint from config.py (default: http://{computer IP}:3335)
- Run `trafficlight.py` and watch either your console or Discord
