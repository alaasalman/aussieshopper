# The AussieShopper Project
## Intro
Some people consume the fantastic deals at OzBargain via the RSS feed. I wrote a telegram bot that notifies me of the latest bargains according to my interests. For example, I’m in the market for new earphones so I add that as an interest and my slave…err I mean bot notifies me when he/she notices a deal on earphones.

I wrote it because I needed it and as part of a bigger hobby project that I will announce when it matures a bit more. Add aussieshopperbot on telegram if you’d like to play around.

Your added interests are matched with the titles and description of the deals that ozbargain gets. Currently, it only matches words or terms so not particularly smart but something I am hoping I can change soon.

## Overview
The server part of this application consists of a django backend and a minimal(for now) web interface and frontend.

The backend is a typical django application so shouldn't be too surprising if you've used django before. The frontend, however, combines django's templates and [Vue](https://vuejs.org/) for some interactivity and a richer interface where necessary.

Roughly the way it works is as follows. The django backend listens to Telegram messages sent in by the user and acts on them. The backend does that by providing an endpoint that Telegram pings when a message is sent to the bot. It then delivers that message to a celery worker which unpacks the message and acts on it.

For example, the initial interaction is a user sending a START message to the bot which Telegram delivers to the django backend. The backend then assigns a worker to unpack this message and figure out that it is a START message. The backend then creates a user account for this new user and saves the Telegram chat ID so that responses can be sent to this specific user. 
 
The django project is made up of a *web* and an *api* application. As the name implies, the *web* application/directory is the django application the contains the user facing components and the *api* is for the Telegram interaction and backend API functionality.

I started this project in 2017 and it has undergone a few iterations so the above may change so always consult the code if you're unsure. The public release was in 2020 and reflects the needs of myself and the handful of users that I have. A public and free instance for anybody to use is accessible at [aussieshopper.codedemigod.com](https://aussieshopper.codedemigod.com).  

### The backend
To run it, follow these basic steps:
* Copy *local_settings.py.sample* to *local_settings.py* to define your own local settings. The most important part of this file are the secret values.
* Create a virtual environment for the project. You can also use pipenv and the enclosed Pipfile to create it.
* Install the requirements needed via `pip install -r config/requirements.txt` or if using pipenv `pipenv install`
* Run django's migrations via `./manage.py migrate`
* Run django's server via `./manage.py runserver`

### The frontend
The frontend mostly lives within the *web/frontend* directory. And it consists of some Vue components that get bundled up and served via the django templates.
 
This is a newest part of the application as originally the whole application was just the django backend and the Telegram interaction. With time, I started considering a web frontend to complement what the bot offers.
 
I use and recommend [yarn](https://yarnpkg.com/) for package management and the bundler used is [webpack](https://webpack.js.org/). [Babel](https://babeljs.io/) is the transpiler but the thing to note is although this is my preferred stack, anything that can run Vue can be used here. The Javascript world has been moving very quickly the past few years so blink and this stack might just be the "wrong" stack by the time you read this.
   
* To generate the frontend, go to the `web/frontend` directory and run the `yarn` command to install the frontend requirements.
* `yarn build-dev` will run webpack in watch mode while you develop.
* A `yarn build` is also defined for production releases. 


## Using the bot
Basically, you have 3 visible commands `/start`, `/latest` and `/listinterest` and two commands to add an interest via `/addinterest` and remove an via `/removeinterest`.

* `/latest` will show you the "latest" deals since you last checked or from the beginning of the day so as not to spam you with a lot of messages. 
* `/listinterest` lists your currently registered interests.
* `/addinterest <interest>` allows you to add a word as an interest for example `/addinterest earphones`.
* `/removeinterest <interest>` does the opposite. <interest> can also be a term such as "belkin plug"
