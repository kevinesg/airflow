# Apache Airflow

## Introduction
This git repository contains the files needed for the Airflow instance (including DAGs, airflow config file, etc.). The Airflow Webserver can be accessed publicly at [airflow.kevinesg.com](airflow.kevinesg.com) with the following log-in credentials:
````
username: viewer
password: airflow
````
This user only has read access to everything.

## Table of Contents
1. [Release Notes](#release-notes)
2. [Pre-installation Notes](#pre-installation-notes)
3. [Installation](#installation)
4. [Deploy Airflow Webserver to a Domain](#deploy-airflow-webserver-to-a-domain)
5. [Folder Structure](#folder-structure)

##
## Release Notes
* created initial setup of git repo and Airflow instance
* deployed Airflow webserver to [airflow.kevinesg.com](airflow.kevinesg.com)

##
## Pre-installation Notes
* I strongly recommend that you use Linux-- either bare-metal, via a (headless) virtual machine, or via WSL2 (if you're using Windows). Personally, I use a GCP VM for production, and a local headless VM for the development environment, and this Github repository, so there is a CI/CD workflow.
* Another thing I strongly recommend is use a virtual environment of your choice. In my case, I prefer to use [Miniconda](https://docs.anaconda.com/miniconda/).
* The instructions below are the steps for bare-metal installation. Feel free to install Airflow instead either via Docker/Docker Compose, or Kubernetes, or via a managed service (via a Cloud Provider).
* You are also not limited to Airflow for orchestration. Popular alternatives are [Dagster](https://dagster.io/), [Prefect](https://www.prefect.io/), and [Mage.ai](https://www.mage.ai/).
* This installation process works for Airflow 2.10. Some steps may not be applicable for future versions.
* Another assumption is that you're using Ubuntu or any Linux distribution that uses `apt` package manager.

##
## Installation
1. Open your Linux terminal and `cd` to the directory where you want to install Airflow. In my case, I created `github/` under the home directory, such that `pwd` command shows `/home/kevinesg/github`. Then I `git clone` this git repository, which then creates `/home/kevinesg/github/airflow`. I `cd` into it. 
    * Enter `sudo apt update && sudo apt upgrade` if you are using a freshly-created Linux distro to make sure everything is updated (you might have to restart).
    * Don't forget to activate your virtual environment.
2. Go to [Apache Airflow Github](https://github.com/apache/airflow) and navigate to the installation part of the documentation.
3. In this project, the installation command I used is `pip install 'apache-airflow[postgres]==2.10.0' --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.0/constraints-3.8.txt"`.
4. I enter the command `export AIRFLOW_HOME=/home/kevinesg/github/airflow`. Basically you create a variable `AIRFLOW_HOME` and set its value to your `airflow` directory.
    * Optional step: Edit `~/.bashrc` (can be done via `nano ~/.bashrc`, you might have to install nano if you don't have it yet, via `sudo apt install nano`), then navigate to the bottom of the file using your down arrowkey. Type `export AIRFLOW_HOME=/home/kevinesg/github/airflow` here too. This makes it so that every time you reboot your Linux distro, it is automatically set. If you don't do this, you have to set the variable every time.
    * Every time you edit `~/.bashrc`, you have to type `source ~/.bashrc` so that the update/s will take effect.
5. Enter `sudo apt install postgresql` to install postgres.
6. Enter `sudo -u postgres psql` to enter postgres (psql) using `postgres` user. By now your terminal should look a bit different since you should have been able to enter postgres. You can verify by typing `\du` to list users.
    * Feel free to check the [Airflow Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html) about how to set up a database. Navigate to the subsection "Setting up a PostgreSQL Database".
    * In my case, the needed commands are as follows:
    ````
    CREATE DATABASE airflow_db;
    CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
    GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
    -- PostgreSQL 15 requires additional privileges:
    GRANT ALL ON SCHEMA public TO airflow_user;
    ````
    * Feel free to change `airflow_db`, `airflow_user`, and of course, your password `airflow_pass`.
    * You can verify if the database is created by typing `\l`, and the user by the previously-mentioned command `\du`.
7. Exit postgres by typing `\q`. You should now be back at your Airflow directory.
8. Enter `airflow db migrate`. This should initialize the Airflow setup.
    * If you got an error message saying something like "permission denied for schema public", try the following fix:
        * Enter postgres again via `sudo -u postgres psql`.
        * type `ALTER DATABASE airflow_db OWNER TO airflow_user;`.
        * Exit postgres using `\q`.
        * Try `airflow db migrate` again.
    * If all goes well, you should see new files in your Airflow directory. Enter `ls` to list the files. You should see `airflow.cfg` which is the config file.
9. Create airflow user by using the following command:
    ````
    airflow users create \
    -e <email> \
    -f <first name> \
    -l <last name> \
    -p <password> \
    -r <role (Admin)> \
    -u <username>
    ````
    * You can check if creating user is successful via `airflow users list`.
10. Edit `airflow.cfg` using `nano airflow.cfg`, or since this is a big file and might be tedious to navigate using a terminal text editor, I recommend using an IDE like VS Code. If you're using a VM, you should still be able to access it using VS Code via ssh.
    * The following edits are based on my personal preference and may not be applicable to future Airflow versions. Feel free to read the Airflow documentation about these variables.
        ```
        [core]
        hide_sensitive_var_conn_fields = False
        executor = LocalExecutor
        load_examples = False

        [database]
        sql_alchemy_conn = postgresql+psycopg2://<airflow_user>:<airflow_pass>@localhost/<airflow_db> # change the variables (and remove < > symbols)

        [scheduler]
        min_file_process_interval = 300
        #parsing_cleanup_interval = 60
        #stale_dag_threshold = 50
        #dag_dir_list_interval = 300
        ```
11. Initialize Airflow Webserver and Scheduler using `screen` (or any alternative).
    * You might need to install screen first via `sudo apt install screen`.
    * Create and enter a screen for webserver using the command `screen -S airflow-webserver`.
        * Activate virtual environment again (this is now inside the screen you created).
        * Enter `airflow webserver`. Wait a bit and check the logs if there are any errors.
            * You should see a confirmation message asking to use the database you created. Type "y" then enter to confirm.
            * You can exit a screen using `CTRL + A` then `D`. If you're using a Linux distribution (bare metal), you might need to use `CTRL + SHIFT + A` then `D`
            * If you get an error like "psycopg2.errors.InsufficientPrivilege: permission denied for schema public", go back to the first subsection of step 8.
                * Exit the screen first.
                * After doing the fix on step 8, enter the screen again. To enter an existing screen, first enter `screen -ls` to see the info of the existing screens. The first value should be the id. In my case, it is "23076.airflow-webserver". I can enter this screen using `screen -R 23076.airflow-webserver`.
                * Inside the screen, enter `airflow webserver` again.
                * Don't forget to exit the screen.
                * You might need to create an Airflow user again (step 9).
    * Create and enter another screen, this time for scheduler, using the command `screen -S airflow-scheduler`.
        * Activate virtual environment again.
        * Enter `airflow scheduler`
        * Wait several seconds to check if there will be error messages.
        * Don't forget to exit the screen.
    * If you need to kill a screen, enter `screen -X -S <screen id> kill`.
    * Optional but recommended: If you anticipate or observe that your VM will be rebooted (either intentional or unintentional), add initialization of Airflow webserver and scheduler in `~/.bashrc`. This is because every time your VM reboots, you have to start webserver and scheduler again. This is one disadvantage of this Airflow installation method.
        * `nano ~/.bashrc` then navigate to the bottom of the file.
        * Add the following:
            ````
            # Start Airflow scheduler
            screen -S airflow-scheduler -d -m bash -c '/home/kevinesg/miniconda3/envs/airflow/bin/airflow scheduler'

            # Start Airflow webserver
            screen -S airflow-webserver -d -m bash -c '/home/kevinesg/miniconda3/envs/airflow/bin/airflow webserver'
            ````
            * Take note that the command above assumes you use a conda environment named "airflow", and miniconda3 is in the home directory. Feel free to edit the directory as needed.
12. Access Airflow webserver.
    * If you're using a VM, and you already have an ssh connection set up, enter `ssh -f -N -L 8080:localhost:8080 <username>@<ip address> -i ~/.ssh/<private ssh key>`.
    * You should now be able to access Airflow via your browser, on `http://localhost:8080/` (or on another port if the defaults in `airflow.cfg` changed).
13. Try to create Airflow DAGs on `~/github/airflow/dags` (create `/dags` if it) and check if it will appear the UI after a bit (or after clicking the manual parsing button for Airflow 2.10 onwards). In my case, the DAGs inside `/dags` folder are reflected in the Airflow webserver UI as seen below:

![Airflow webserver UI](https://i.imgur.com/8GAv6dl.png)

##
## Deploy Airflow Webserver to a Domain
### GCP VM
Note: Since I use a GCP VM for my git repos, the following steps are catered to this use case and may not be applicable to you.
1. Reserve a static IP.
    * Go to GCP Console -> VPC Network -> IP Address. Here's where I assign a static external IP so that the IP doesn't change when the VM restarts.
    * You might need to scroll to the right to find the three dots. Click it to change the IP to static, then assign a name.
2. Open HTTP/HTTPS Ports in GCP Firewall.
    * Go to VPC Network -> Firewall.
    * Create a firewall rule.
        * Name: give a name like "allow-http".
        * Network: Select the network where your VM instance is located (usually default).
        * Priority: You can leave this at the default value of 1000.
        * Direction of traffic: Choose "Ingress" to allow incoming traffic.
        * Action on match: Choose "Allow" to allow the traffic.
        * Targets: Select "All instances in the network" or specify your VM instance if you want to restrict the rule to only that instance.
        * Source filter: Choose "IP ranges".
        * To allow all external traffic, enter 0.0.0.0/0 (note: this allows traffic from anywhere, which is suitable for web access but could be a security risk if not managed).
        * Protocols and ports: Check the box for "tcp" and enter `80` to allow HTTP traffic.
    * Double-check everything then click `Create` once done.
    * You should see the newly-created firewall rule.
    * Repeat the same steps for `Name: "allow-https"` and `tcp: 443` instead of `80` for HTTPS.

### Nginx
1. Install Nginx via `sudo apt install nginx`
2. Configure nginx as reverse proxy.
    * `sudo nano /etc/nginx/sites-available/default`
    * Modify the configuration to proxy requests to your Airflow instance running on `localhost:8080` (or on another port depending on your preference, based on `airflow.cfg`). Here’s an example configuration you can add after the default `server` block:
        ````
        server {
            listen 80;
            server_name airflow.kevinesg.com;

            location / {
                proxy_pass http://127.0.0.1:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }

            listen 443 ssl; # managed by Certbot
            ssl_certificate /etc/letsencrypt/live/airflow.kevinesg.com/fullchain.pem; # managed by Certbot
            ssl_certificate_key /etc/letsencrypt/live/airflow.kevinesg.com/privkey.pem; # managed by Certbot
            include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
            ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

        }
        ````
    * Save and exit.
    * Test the nginx configuration for syntax errors via `sudo nginx -t`. If test is successful, restart nginx via `sudo systemctl restart nginx`. Here's the message I got which confirms everything it set up correctly:
    ````
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ````
3. Create ssl certificate.
    * `sudo apt install certbot python3-certbot-nginx`
    * `sudo certbot --nginx -d airflow.kevinesg.com`

### Cloudflare
1. If you don't have one yet, buy your preferred domain name from any provider. In my case I chose [Squarespace](https://www.squarespace.com/). If you decide to do the same, sign up and enter your payment information.
2. Go to [Cloudflare](https://www.cloudflare.com/products/registrar/) and enter your domain name. In my case I chose the free plan tier. Follow the rest of instructions to complete initial setup.
3. Update/Setup DNS configuration.
    * Go to DNS settings.
    * Create the following records (you will have to create these one at a time):
        ````
        Type: A
        Name: @ # root (in my case, kevinesg.com)
        Content: <external IP address of your machine that runs airflow>
        Proxy status: Proxied
        TTL: Auto


        Type: A
        Name: www # similar to root
        Content: <external IP address of your machine that runs airflow>
        Proxy status: Proxied
        TTL: Auto


        Type: A
        Name: airflow
        Content: <external IP address of your machine that runs airflow>
        Proxy status: Proxied
        TTL: Auto
        ````
4. Feel free to read Cloudflare docs and guides as not every case is covered in these steps.
5. Optional: if you can't load your websites after everything is set up, try to change SSL/TLS encryption to `Full` or `Full (strict)` in SSL/TLS -> Overview.


##
## Folder Structure
````
.
├── LICENSE
├── README.md
├── airflow-webserver.pid   # generated when `airflow webserver` runs; do not delete
├── airflow.cfg             # main Airflow config file for settings like DB, executor, etc.
├── airflow.db              # default SQLite DB, replaceable with Postgres/MySQL
├── dags                    # contains all Airflow DAGs (active and inactive)
│   ├── archived            # inactive DAGs moved here
│   ├── .airflowignore      # works like .gitignore; to ignore archived/*
├── logs                    # task logs, also accessible via the UI
├── variables.json          # variables entered via Airflow webserver UI
└── webserver_config.py     # generated when `airflow webserver` runs; stores webserver settings

````

Some files and folders might be missing because they are included in `.gitignore` for privacy purposes.
##
For more information, feel free to check [Apache Airflow Installation Documentation](https://airflow.apache.org/docs/apache-airflow/stable/start.html) or their [Github](https://github.com/apache/airflow). Let me know if you have any questions! You can contact me at kevinlloydesguerra@gmail.com.