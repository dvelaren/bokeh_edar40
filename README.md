# bokeh_edar40 Project

This project was developed using Flask, Bootstrap, Bokeh and Rapidminer for a research project between Vicomtech, Mondragon University, Ibermatica and Giroa Veolia.

EDAR is the acronym for "Estacion Depuradora de Aguas Residuales", which is translates into Wastewater Treatment Plant.

## Installation
1. First make sure logs directory exists within the cloned git directory, if it isn't, create it as follows:
    ```sh
    mkdir logs
    ```
2. Install python3-pip, python dev tools and python3-venv
    ```sh
    sudo apt-get update
    sudo apt-get install python3-pip
    sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
    sudo apt-get install python3-venv
    ```

3. Create virtual environment inside directory
    ```sh
    python3 -m venv venv
    ```

4. Activate virtual environment
    ```sh
    source venv/bin/activate
    ```

5. Install python required libraries (using requirements.txt file)
    ```sh
    pip install -r requirements.txt
    ```

6. Edit server_config.py SERVER_IP parameter to match host ip address

7. Install nginx to proxy inverse Flask port and Bokeh port
    ```sh
    sudo apt-get install nginx
    ```

8. Create a new nginx configuration file inside /etc/nginx/sites-available/
    ```sh
    sudo nano /etc/nginx/sites-available/edar
    ```

9. Edit nginx config file as follows:
    ```
    server {
        listen 80;
        server_name SERVER_DNS;

        location / {
            include proxy_params;
            proxy_pass http://127.0.0.1:9995;
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

10. Create a link to the previous nginx config file inside /etc/nginx/sites-enabled/
    ```sh
    sudo ln -s /etc/nginx/sites-available/edar /etc/nginx/sites-enabled
    ```

11. Test that nginx config is correct
    ```sh
    sudo nginx -t
    ```

12. Restart nginx
    ```sh
    sudo systemctl restart nginx
    ```

13. Run application with gunicorn
    ```sh
    gunicorn -b 0.0.0.0:9995 main:app
    ```















