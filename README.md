# EDAR 4.0 Dashboard

This project was developed using Flask, Bootstrap, Bokeh and Rapidminer for a research project between Vicomtech, Mondragon University, Ibermatica and Giroa Veolia.

EDAR is the acronym for "Estacion Depuradora de Aguas Residuales", which means Wastewater Treatment Plant.

## Requirements
- Ubuntu 16.04
- Rapidminer Server 9.5.0 (With Postgresql 9.5.24)
- Python 3.7.4 with Virtual Environment

## Installation

1. Create a new admin user in Ubuntu called edar.
2. Clone the current directory.

Follow the next steps.

### Rapidminer Server Install
1. Install Rapidminer Server 9.5.0 following [this guide](./docs/rapidminer_install.md).
2. Restore server's operation database and rapidminer server home directory:
    - In order to guarantee that both the operations database and the home directory are in sync, RapidMiner Server needs to be shut down before initiating the backup process:
        ```sh
        service rapidminerserver stop
        ```
    - Copy `docs/20210215_Backup Edar Rapidminer.zip` to Desktop and unzip it.
    - Open pgAdmin III, connect to database and right-click rapidminer_server Database. Select `Backup...` and under Filename browse to the file called `20210215_DB_backup_rapidminer.backup`. Click `Restore`.
    - Once finished, go to rapidminer directory and copy the file `20210215_backup_rapidminer.tar.gz`. THen extract its contents with the following command (replace files if required):
        ```sh
        cd /home/rapidminer/rapidminer-server
        tar xvzf 20210215_backup_rapidminer.tar.gz
        ```
### EDAR Dashboard Install
1. Change to `edar` user first
   ```sh
   su edar
   ```

2. Go to cloned directory with a terminal
   ```sh
   cd PATHTOREPO
   ```

3. First make sure logs directory exists within the cloned git directory, if it isn't, create it as follows:
    ```sh
    mkdir logs
    ```

4. Install python3-pip, python dev tools and python3-venv
    ```sh
    sudo apt-get update
    sudo apt-get install python3-pip
    sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
    sudo apt-get install python3-venv
    ```

5. Create virtual environment inside directory
    ```sh
    python3 -m venv venv
    ```

6. Activate virtual environment
    ```sh
    source venv/bin/activate
    ```

7. Install python required libraries (using requirements.txt file)
    ```sh
    pip install -r requirements.txt
    ```

8. Edit `utils/server_config.py` SERVER_IP parameter to match host ip address. Also set up default username and password.

9. Open `parser_edar40/common/constants.py` and edit `IN_DATA_FILE_NAME`, `IN_METEO_LIVE_FILE` with the locations of ID CARTUJA and METEO live xlsx files.


10. Install nginx to proxy inverse Flask port and Bokeh port
    ```sh
    sudo apt-get install nginx
    ```

11. Create a new nginx configuration file inside /etc/nginx/sites-available/
    ```sh
    sudo nano /etc/nginx/sites-available/edar
    ```

12. Edit nginx config file as follows (replace LOCALIP:PORT with machine LAN IP and the port assigned by systems, and SERVER_DNS with provided DNS):
    ```
    server {
        listen 80;
        listen LOCALIP:PORT;
        server_name SERVER_DNS;

        location / {
            include proxy_params;
            proxy_pass http://unix:/home/edar/bokeh_edar40/bokeh_edar40.sock;
        }

        location /bokeh/ {
            proxy_pass http://127.0.0.1:9090;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_http_version 1.1;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host:$server_port;
            proxy_buffering off;
        }
    }
    ```

13. Create a link to the previous nginx config file inside /etc/nginx/sites-enabled/
    ```sh
    sudo ln -s /etc/nginx/sites-available/edar /etc/nginx/sites-enabled
    ```

14. Test that nginx config is correct
    ```sh
    sudo nginx -t
    ```

15. Restart nginx
    ```sh
    sudo systemctl restart nginx
    ```

16. Create a UNIX service to autostart EDAR dashboard
    ```sh
    sudo nano /etc/systemd/system/edar.service
    ```

    Add the following lines. Edit workers and threads depending on available resources and according to [this](https://docs.gunicorn.org/en/stable/design.html#how-many-workers)
    ```
    [Unit]
    Description=Gunicorn instance to serve bokeh_edar40
    After=network.target

    [Service]
    User=edar
    Group=www-data
    WorkingDirectory=/home/edar/bokeh_edar40
    Environment="PATH=/home/edar/bokeh_edar40/venv/bin"
    ExecStart=/home/edar/bokeh_edar40/venv/bin/gunicorn --workers 3 --threads 3 --bind unix:bokeh_edar40.sock -m 007 main:a$

    [Install]
    WantedBy=multi-user.target
    ```

17. Start unix service and enable it (boot at system start)
    ```sh
    sudo systemctl start edar
    sudo systemctl enable edar
    ```

18. Verify status
    ```sh
    sudo systemctl status edar
    ```

19. Open a web navigator and navigate to https://SERVER_DNS. Login using default credentials (User: rapidminer, password: Rapidminer). Credentials may be changed through `utils/server_config.py` file.














