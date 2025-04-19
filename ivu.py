#!/usr/bin/env python

import discord
import bot_bin.bot
import qtoml as toml

class IvuBot(bot_bin.bot.Bot):
	startup_extensions = [
		'bot_bin.systemd',
		'jishaku',
		'cogs.ivu',
		'cogs.meta',
	]
	def __init__(self, *args, **kwargs):
		intents = discord.Intents.default()

		with open('config.toml') as f:
			config = toml.load(f)

		# only enable member join event if we really need it
		if config['entry_channel']:
			intents.members = True

		super().__init__(*args, intents=intents, config=config, **kwargs)

if __name__ == '__main__':
	IvuBot().run()
