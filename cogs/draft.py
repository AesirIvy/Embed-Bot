import json
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands, pages
from discord.ui import InputText as InTxt

from data import Data


class Draft(commands.Cog):

    def __init__(self):
        self.data = Data()

    draft = discord.SlashCommandGroup('draft')

    @draft.command(description="Create a draft.")
    async def create(self, ctx):
        await ctx.send_modal(DraftModal(ctx.author.id))

    @draft.command(
        description="Delete the draft that correspond to the given code."
        )
    async def delete(self, ctx, code):
        self.data.delete_file(ctx.author.id, code)
        await ctx.respond(f"draft *{code}* deleted", ephemeral=True,
                          delete_after=5)

    @draft.command(description="Return a list of all your draft.")
    async def history(self, ctx):
        ts = self.data.history(ctx.author.id)
        folios = []
        if not ts:
            await ctx.respond("no saved draft", ephemeral=True, delete_after=5)
            return
        for i in ts:
            with open(f"data/{ctx.author.id}/{i[0]}.json") as data:
                dct = json.loads(data.read())
                folios.append(
                    pages.Page(
                        content=f"<t:{i[0]}:F>\n"
                        + f"draft code: `{hex(i[0]-1672527600)[2:]}`",
                        embeds=[discord.Embed.from_dict(dct)]
                        )
                    )
        paginator = pages.Paginator(pages=folios)
        await paginator.respond(ctx.interaction)
        await paginator.wait()
        await paginator.update(show_disabled=False, show_indicator=False)

    @draft.command(
        description="Modify the draft that correspond to the given code."
        )
    async def modify(self, ctx, code):
        code = int(code, 16)
        if Path(f'data/{ctx.author.id}/{code}.json').exists():
            with open(f'data/{ctx.author.id}/{code}.json') as data:
                embed = discord.Embed.from_dict(json.loads(data.read()))
                await ctx.send_modal(DraftModal(ctx.author.id, embed))
        else:
            await ctx.respond("You don't have draft with this code.")

    @draft.command(
        description="Send the last draft, if not draft code is provided."
        )
    @discord.option('channel', discord.TextChannel)
    async def send(self, ctx, channel, code=None):
        perm = channel.permissions_for(ctx.author)
        if not perm.send_messages:
            await ctx.respond("You don't have permission to send message in "
                              + f"<#{channel.id}>.", ephemeral=True,
                              delete_after=5)
            return
        ts = self.data.history(ctx.author.id)
        if ts:
            if not code:
                with open(f'data/{ctx.author.id}/{ts[0][0]}.json') as data:
                    dct = json.loads(data.read())
            elif int(code, 16) in [i[0] for i in ts]:
                with open(f'data/{ctx.author.id}/{int(code, 16)}.json') as data:
                    dct = json.loads(data.read())
            await channel.send(embed=discord.Embed.from_dict(dct))
            await ctx.respond("Draft sended!", ephemeral=True, delete_after=5)
            return
        await ctx.respond("no saved draft", ephemeral=True, delete_after=5)


class DraftModal(discord.ui.Modal):

    def __init__(self, identity, embed=discord.Embed(colour=0), orginal=True):
        super().__init__(title='Draft')
        if embed.colour.value == 0:
            self.add_item(InTxt(label='Colour', placeholder="Hex color codes",
                                max_length=6, required=False))
        else:
            self.add_item(InTxt(label='Colour', max_length=6, required=False,
                                value=hex(embed.colour.value)[2:]))
        self.add_item(InTxt(label='Title', max_length=256,
                            required=False, value=embed.title))
        self.add_item(InTxt(style=discord.InputTextStyle.long,
                            label='Description', max_length=2048,
                            required=False, value=embed.description))
        self.identity = identity
        self.embed = embed
        self.orginal = orginal

    async def callback(self, interaction):
        try:
            self.embed.colour = int(self.children[0].value, 16)
        except ValueError:
            self.embed.colour = 0
        self.embed.title = self.children[1].value
        self.embed.description = self.children[2].value
        res = interaction.response
        if self.orginal:
            await res.send_message(
                f"will be disabled <t:{int(datetime.now().timestamp())+900}:R>",
                embed=self.embed, view=DraftView(self.identity, self.embed)
                )
        else:
            await res.edit_message(
                content="will be disabled "
                + f"<t:{int(datetime.now().timestamp())+900}:R>",
                embed=self.embed, view=DraftView(self.identity, self.embed)
                )


class DraftView(discord.ui.View):

    def __init__(self, identity, embed):
        super().__init__(timeout=900)
        self.data = Data()
        self.identity = identity
        self.embed = embed

    async def on_timeout(self):
        self.clear_items()
        await self.message.edit('', view=self)

    @discord.ui.button(label='Modify', style=discord.ButtonStyle.blurple)
    async def modify_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftModal(self.identity, self.embed, False))

    @discord.ui.button(label='Save', style=discord.ButtonStyle.green)
    async def save_callback(self, button, interaction):
        self.clear_items()
        self.data.insert_file(self.identity, int(datetime.now().timestamp()),
                              self.embed.to_dict())
        if type(self.embed.footer) == str:
            self.embed.set_footer(text=f"{self.embed.footer} | saved")
        else:
            self.embed.set_footer(text="saved")
        res = interaction.response
        await res.edit_message(content='', embed=self.embed, view=self)

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.red)
    async def delete_callback(self, button, interaction):
        await self.message.delete()

    @discord.ui.button(label='Add', style=discord.ButtonStyle.grey)
    async def add_callback(self, button, interaction):
        res = interaction.response
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            view=DraftAddView(self.identity, self.embed)
            )


class DraftAddView(discord.ui.View):

    def __init__(self, identity, embed):
        super().__init__(timeout=900)
        self.identity = identity
        self.embed = embed

    @discord.ui.button(label="Add Field", style=discord.ButtonStyle.grey)
    async def add_field_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftAddFieldModal(self.identity, self.embed))

    @discord.ui.button(label="Edit Field", style=discord.ButtonStyle.grey)
    async def edit_field_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftEditFieldModal(self.identity, self.embed))

    @discord.ui.button(label="Remove Field", style=discord.ButtonStyle.grey)
    async def remove_field_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftRemoveFieldModal(self.identity, self.embed))

    @discord.ui.button(label='Footer', style=discord.ButtonStyle.grey)
    async def footer_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftFooterModal(self.identity, self.embed))

    @discord.ui.button(label='Timestamp', style=discord.ButtonStyle.grey)
    async def timestamp_callback(self, button, interaction):
        res = interaction.response
        await res.send_modal(DraftTimestampModal(self.identity, self.embed))

    @discord.ui.button(label='Back', style=discord.ButtonStyle.grey)
    async def back_callback(self, button, interaction):
        res = interaction.response
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            view=DraftView(self.identity, self.embed)
            )


class DraftAddFieldModal(discord.ui.Modal):

    def __init__(self, identity, embed):
        super().__init__(title='Draft')
        self.identity = identity
        self.embed = embed
        self.add_item(InTxt(label="Field Title", max_length=256,
                            required=False))
        self.add_item(InTxt(style=discord.InputTextStyle.long,
                            label="Field Description", max_length=1024,
                            required=False))

    async def callback(self, interaction):
        self.embed.add_field(name=self.children[0].value,
                             value=self.children[1].value, inline=False)
        res = interaction.response
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            embed=self.embed, view=DraftAddView(self.identity, self.embed)
            )


class DraftEditFieldModal(discord.ui.Modal):

    def __init__(self, identity, embed):
        super().__init__(title='Draft')
        self.identity = identity
        self.embed = embed
        self.add_item(InTxt(label="Field Position",
                            placeholder="Between 1 and 25",
                            max_length=2, required=True))
        self.add_item(InTxt(label="Field Title", max_length=256,
                            required=False))
        self.add_item(InTxt(style=discord.InputTextStyle.long,
                            label="Field Description", max_length=1024,
                            required=False))

    async def callback(self, interaction):
        res = interaction.response
        try:
            self.embed.set_field_at(int(self.children[0].value),
                                    name=self.children[1].value,
                                    value=self.children[2].value, inline=False)
        except (IndexError, ValueError):
            await res.send_message("invalid field position", ephemeral=True,
                                   delete_after=5)
            return
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            embed=self.embed, view=DraftAddView(self.identity, self.embed)
            )


class DraftRemoveFieldModal(discord.ui.Modal):

    def __init__(self, identity, embed):
        super().__init__(title='Draft')
        self.identity = identity
        self.embed = embed
        self.add_item(InTxt(label="Field Position",
                            placeholder="Between 1 and 25", max_length=2))

    async def callback(self, interaction):
        res = interaction.response
        try:
            pos = int(self.children[0].value) + 1
        except ValueError:
            await res.send_message("invalid field position", ephemeral=True,
                                   delete_after=5)
            return
        self.embed.remove_field(pos)
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            embed=self.embed, view=DraftAddView(self.identity, self.embed)
            )


class DraftFooterModal(discord.ui.Modal):

    def __init__(self, identity, embed):
        super().__init__(title='Draft')
        self.identity = identity
        self.embed = embed
        self.add_item(InTxt(label="Footer Text", max_length=2048,
                            required=False, value=embed.footer))

    async def callback(self, interaction):
        self.embed.set_footer(text=self.children[0].value)
        res = interaction.response
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            embed=self.embed, view=DraftAddView(self.identity, self.embed)
            )


class DraftTimestampModal(discord.ui.Modal):

    def __init__(self, identity, embed):
        super().__init__(title='Draft')
        self.identity = identity
        self.embed = embed
        self.add_item(InTxt(label="Timestamp"))

    async def callback(self, interaction):
        ts = int(self.children[0].value)
        self.embed.timestamp = datetime.fromtimestamp(ts)
        res = interaction.response
        await res.edit_message(
            content="will be disabled "
            + f"<t:{int(datetime.now().timestamp())+900}:R>",
            embed=self.embed, view=DraftAddView(self.identity, self.embed)
            )


def setup(bot):
    bot.add_cog(Draft())
