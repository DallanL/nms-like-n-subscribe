# ns-subscribe
service to create and maintain subscriptions


## Clone the repo and prepwork

clone the repo:
```bash
git clone https://github.com/DallanL/nms-like-n-subscribe.git
cd nms-like-n-subscribe
```

edit the environmental variables:
```bash
cp env-example .env
vim .env
```
*** to exit vim, press `esc` + `:wq`


now either run it locally, or via docker:


##### local

setup virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

install requirements:
```bash
pip install -r requirements.txt
```

run the application:
```bash
python3 run.py
```

##### docker

build the docker container:
```bash
docker build -t nms-like-n-subscribe .
```

run the docker container:
```bash
docker run --env-file .env -d --name nms-like-n-subscribe -p 8001:8001 nms-like-n-subscribe
```
