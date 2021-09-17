import os
from dotenv import load_dotenv

import asyncio
import logging

import dhooks_lite

import lightbulb
from hikari import Intents, Embed, events, webhooks, errors
from hikari.impl import event_manager_base

load_dotenv()

if os.name != "nt":
    import uvloop
    uvloop.install()

bot = lightbulb.Bot(
    token=os.getenv("DISCORD_BOT_TOKEN"),
    prefix="^",
    intents=Intents.ALL,
    logs={
        "version": 1,
        "incremental": True,
        "loggers": {
            "hikari": {"level": "INFO"},
            "hikari.ratelimits": {"level": "TRACE_HIKARI"},
            "lightbulb": {"level": "INFO"},
        }
    }
)

@bot.command()
async def ping(ctx):
    await ctx.respond("Pong!")

class WelcomePlugin(lightbulb.Plugin):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.log_channel_hook = dhooks_lite.Webhook(os.getenv("LOG_CHANNEL_WEBHOOK_LINK"))

    async def form_runner(self, member):
        try:
            details = {}
            msg = await member.send(
                Embed(
                    title="How would you like to be addressed?",
                    description="(Could be a name, nickname, handle, etc.). We would also love to welcome you to our communities on Twitter and Telegram, if you would like to share your handles",
                    color=0xdefb48
                )
            )
            response = await self.bot.wait_for(
                events.DMMessageCreateEvent,
                180.0,
                lambda event: event.author.id == member.id
            )
            details["name"] = response.message.content

            msg = await member.send(
                Embed(
                    title="Where did you hear about the TEC? What brings you here?",
                    description="All info is welcome, and here are just some ideas:\n\
- You want to learn more and participate.\n\
- You’re interested in submitting a proposal for TEC funding (TE research and education).\n\
- You are attracted to the Cultural Build.\n\
- You are attracted to a particular Working Group.\n\
- Your DAO is interested in a partnership.\n\n\
You can be a token engineer, a social scientist, a scientist, a data scientist, in the arts or humanities or something else!\n\
Please share as much as you would like. It will help us to get to know you and steward you in the right direction as you join the TEC community!",
                    color=0xdefb48
                )
            )
            response = await self.bot.wait_for(
                events.DMMessageCreateEvent,
                180.0,
                lambda event: event.author.id == member.id
            )
            details['background'] = response.message.content

            self.log_channel_hook.execute(
                embeds=[dhooks_lite.Embed(
                    title=f"{member} joined the server!",
                    description=f"\n\
**1) How would you like to be addressed?**\n{details['name']}\n\n\
**2) Where did you hear about the TEC? What brings you here?**\n{details['background']}",
                    color=0xdefb48
                )]
            )

            await member.send(
                    Embed(
                        description="Thanks for filling out this form!",
                        color=0x00ff00
                    )
            )
            await member.send(
                Embed(
                    title="Welcome to the TEC!",
                    description=f"Hi {member.mention}, and welcome to the TEC! <:TEC:835016327542210560>\n\
❓ Please join our weekly orientation Call with your questions, suggestions or feedback on Wednesdays at 6pm CET on our [#!community-hall](https://discord.gg/Yr7jWKY2qE) voic channel on TEC Discord.\n\
🌐 Join the community call on Discord on Thursdays at 7pm CET.\n\n\
ℹ️  Here are some links to get you started:\n\
- 🗓️ **TEC Calendar** ⏰\nOur meetings are open to all. Find one in our calendar; looking forward to seeing you there!\nhttps://calendar.google.com/calendar/u/0/embed?src=5mkep1ad1j860k6g7i7fr8plq0@group.calendar.google.com&ctz=Europe/Berlin\n\
- 📽️  **TEC YouTube** 🎞️\nThe TEC is proactive to transparency, and so our Working Group sessions are all available on Youtube.\nhttps://www.youtube.com/channel/UCagCOhMqMNU29rWx259-tcg\n\
- 📜 **TEC Blog** 📋\nAnd read the latest posts on our blog.\nhttps://medium.com/token-engineering-commons/\n\n\
Please feel free to look around, and reach out on Discord to `@Suga#8514` (our onboarding coordinator) if you have any questions, or want to schedule a 1-on-1\n<:TEC:835016327542210560> Enjoy your stay! See you soon. 👋\n",
                    color=0xdefb48,
                    url="https://tecommons.org/"
                )
            )
            await member.send("https://www.youtube.com/watch?v=vf1rOMDzw38")

        except asyncio.TimeoutError:
            await member.send(
                Embed(
                    description="That form timed out, to fill the same, use the command- `^welcome` and follow the instructions.",
                    color=0xff0000
                )
            )



    async def greeting(self, member):
        try:
            msg = await member.send(
                Embed(
                    title="Welcome to the TEC!",
                    description="It would be great if you could share some more info with us by filling a small form. To start filling it react to this mesage with a 📝",
                    color=0xdefb48
                )
            )
            await msg.add_reaction('📝')

            try:
                reaction = await self.bot.wait_for(
                    events.DMReactionAddEvent,
                    180.0,
                    lambda event: event.user_id == member.id
                )
                await self.form_runner(member)
            except asyncio.TimeoutError:
                await msg.remove_reaction(
                    '📝',
                    user=self.bot.get_me()
                )
                await member.send(
                    Embed(
                        description="That form timed out, to fill the same, use the command- `^welcome` and follow the instructions.",
                        color=0xff0000
                    )
                )
        except errors.ForbiddenError:
            await self.log_channel_hook.execute(
                embeds=[Embed(
                    description=f"Error: Couldn't send DM to {member.mention}",
                    color=0xff0000
                )]
            )

    @lightbulb.dm_only()
    @lightbulb.command()
    async def welcome(self, ctx):
        await self.greeting(ctx.author)

    @lightbulb.plugins.listener(events.MemberCreateEvent)
    async def send_greetings(self, event):
        await self.greeting(event.member)


bot.add_plugin(WelcomePlugin(bot))
bot.run()
