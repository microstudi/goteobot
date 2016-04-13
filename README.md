# Goteo Bot

This is a simple (and experimental) [Telegram Bot](https://core.telegram.org/bots) bot which interacts with the [Goteo API](https://api.goteo.org) .

Curently it provides updates of every invest made into a project.

## Live instances

There's and experimental copy running sometimes as [GoteoBot](https://telegram.me/goteobot). 

## Valid commands

Currently, only one command is accepted:

```
/subscribe <project-id>
```

There's no de-subscribing command yet, but don't worry the Bot is reset frequently

## Installation

You'll need to create a Telegram Bot and fetch the Access Token

To generate an Access Token you have to talk to [BotFather](https://telegram.me/botfather) and follow a few simple steps (described here).

Also, get a valid User/Key for the Goteo API in the [Goteo profile page](https://goteo.org/dashboard/activity/apikey)

Copy the *example* config file and change the values accordingly:

```bash
cp config.example.py config.py
nano config.py
```

Install dependencies:

```bash
./deployer
```

Run the Bot:

```bash
./goteobot
```

## License

This software is licensed using the **GNU GENERAL PUBLIC LICENSE Version 3**