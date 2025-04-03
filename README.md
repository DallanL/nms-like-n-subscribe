# ns-subscribe
service to create and maintain subscriptions
postgresql database is required as that is where subscription data is maintained

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



### create a subscription
i included a simple program in `/create-sub/` that works along with the subscription maintainer, it is a command line tool that lets you step through creating a single subscription... the subscription maintainer also has an API endpoint at  `<url>:8001/create-subscription` that accepts a json blob of:
```json
{
	"model": <model>,
        "domain": <domain>,
        "post_url": <post_url>,
        "expires": <expire date/time>,
}
```

and creates a new subscription it will maintain
