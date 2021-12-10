# DiscordManagement

Website that allows to manage Discord members (ban/kick/manage roles)

**For more on this bot and all the rest of the Eco Community bots, check out [this post](https://echo.mirror.xyz/GlFuqSbTZOLDl0LA7eDa0Yibhqq6IHNUC48nd3WJZQw).**

### Using website you can:
* Lot's of options to filter members
* Ban members
* Kick members
* Assign roles to members
* Remove roles from members
* Automatically ban copycats
* Ability to ban/kick/assign roles/remove roles to multiple (or even all) members at the same time

## Installation
1. [Install Docker](https://docs.docker.com/engine/install/ubuntu/)
2. Copy and update settings in `.env.example`
3. Execute `docker-compose up -d`
4. Install requirements from `requirements.txt` for `>= Python 3.8`
5. Init database tables via `python backend/manage.py migrate`
6. Start bot via `python bot/run.py` or [via supervisord](http://supervisord.org/) or [systemd](https://es.wikipedia.org/wiki/Systemd)
7. Add a bot to the server with at least `268509190` scope  
Note: place bot role [at the top](https://medium.com/the-discord-path/the-perfect-hierarchy-order-6bb6b4a0cda3) if you want it to be able to manage roles below
8. Start backend via `python backend/manage.py runserver` or [via supervisord](http://supervisord.org/) or [systemd](https://es.wikipedia.org/wiki/Systemd)
