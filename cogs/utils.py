from datetime import datetime

import discord
from discord.ext import commands


class Utils(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    utils = discord.SlashCommandGroup('utils')

    @utils.command(description="Delete 100 messages, if not limit is provided.")
    @discord.default_permissions(manage_messages=True)
    async def purge(self, ctx, limit=100):
        await ctx.respond("Deleting...", ephemeral=True, delete_after=3)
        if ctx.channel.type == discord.ChannelType.private:
            async for msg in ctx.channel.history(limit=limit):
                if msg.author == self.bot.user:
                    await msg.delete()
        else:
            await ctx.channel.purge(limit=limit)

    @utils.command(description="Get the timestamp.")
    async def timestamp(self, ctx, year: int = None, month: int = None,
                        day: int = None, hour: int = None, minute: int = None,
                        second: int = None):
        dt = datetime.now()
        ls = [year, month, day, hour, minute, second,
              dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second]
        ls = [ls[i+6] if ls[i] is None else ls[i] for i in range(6)]
        dt = dt.replace(year=ls[0], month=ls[1], day=ls[2], hour=ls[3],
                        minute=ls[4], second=ls[5])
        await ctx.respond(int(dt.timestamp()), ephemeral=True, delete_after=45)


def setup(bot):
    bot.add_cog(Utils(bot))
