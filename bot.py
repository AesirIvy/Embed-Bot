import json

from discord.ext import commands


class Bot(commands.Bot):

    def __init__(self):
        super().__init__()
        with open('config.json') as data:
            config = json.loads(data.read())
        for ext in config['extension']:
            self.load_extension(ext)
        self.run(config['token'])

    async def on_ready(self):
        print(f"{self.user.name} is connected.")


if __name__ == '__main__':
    bot = Bot()
