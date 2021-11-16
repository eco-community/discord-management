# DiscordManagement

Website that allows to manage Discord members (ban/kick/manage roles)


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
