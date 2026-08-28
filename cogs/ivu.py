import base64
import logging
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger('cogs.ivu')

def _has_role(ctx, role_name: str):
	role_id = ctx.bot.config['roles'][role_name]
	return ctx.author.get_role(role_id) is not None

# able to set passwords
def is_helper(ctx):
	# assume that organizer implies helper
	if _has_role(ctx, 'helper') or _has_role(ctx, 'organizer'):
		return True

	raise commands.CommandError('You need either the Helper or Organizer role to run this command.')

# able to ban
def is_organizer(ctx):
	if _has_role(ctx, 'organizer'):
		return True

	raise commands.CommandError('You need the Organizer role to run this command.')

class Ivu(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		# this doesn't need to be hashed or anything because it's not super sensitive
		# storing it in plain text lets admins refer to it to hand out to new attendees
		with open('password.txt') as f:
			self._set_password(f.read())

	def _set_password(self, password):
		# for CTF style fun
		self.passwords = {password, base64.b64encode(password.encode()).decode()}

	@app_commands.command(name='password')
	async def password_command(self, interaction, password: str):
		grant_role = interaction.guild.get_role(self.bot.config['roles']['grant'])
		if grant_role in interaction.user.roles:
			await interaction.response.send_message(
				f'Sorry, but you already have the {grant_role} role. '
				'To discourage guessing, I will not tell you whether this password is correct.',
				ephemeral=True,
			)
			return

		if password not in self.passwords:
			await interaction.response.send_message('Wrong password!', ephemeral=True)
			return

		await interaction.user.add_roles(grant_role)

		if remove_role_id := self.bot.config['roles']['remove']:
			remove_role = interaction.guild.get_role(remove_role_id)
			await interaction.user.remove_roles(remove_role)

		await interaction.response.send_message(f'Thanks! You have been granted the {grant_role} role.', ephemeral=True)

	# we avoid using interactions commands for these because those are visible to all users

	@commands.command(name='set-password')
	@commands.check(is_helper)
	async def set_password(self, ctx, password):
		with open('password.txt', 'w') as f:
			f.write(password)
		self._set_password(password)
		await ctx.message.add_reaction(self.bot.config['success_emojis'][True])

	@commands.command()
	@commands.check(is_organizer)
	async def ban(self, ctx, user: discord.Member | discord.User | discord.Object, *, reason: str = None):
		try:
			await ctx.guild.ban(user, reason=reason)
		except discord.Forbidden as exc:
			await ctx.send(f"I don't have permission to ban {user}. Details: {exc.text}. Code: {exc.code}.")
		else:
			async with asyncio.TaskGroup() as tg:
				tg.create_task(ctx.message.add_reaction(self.bot.config['success_emojis'][True]))
				tg.create_task(ctx.send(f'Banned {user}.'))

async def setup(bot):
	await bot.add_cog(Ivu(bot))
