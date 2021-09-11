import os
from dotenv import load_dotenv

import asyncio
import logging

import lightbulb
from hikari import Intents, Embed, events
from hikari.impl import event_manager_base

load_dotenv()

if os.name != "nt":
    import uvloop
    uvloop.install()

bot = lightbulb.Bot(
    token=os.getenv("DISCORD_BOT_TOKEN"),
    prefix="!",
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

    async def form_runner(self, member):
        try:
            msg = await member.send(
                Embed(
                    title="Preferred name and pronouns, and handles",
                    description="We want to know how would you like to be addressed and that could be by your name or by your handle. If you like, we would love to welcome you to our communities on twitter and telegram, in case you want to drop your handles!",
                    color=0xdefb48
                )
            )
            response = await self.bot.wait_for(
                events.DMMessageCreateEvent,
                180.0,
                lambda event: event.author.id == member.id
            )
            print(response.message.content)

            msg = await member.send(
                Embed(
                    title="What brought you here?",
                    description="- Proposals for TEC Funding(research, TE Education)\n\
- Contributor in the TEC\n\
- Educator\n\
- Token Engineer\n\
- Social Science/Cultural Build/Governance, etc.\n\
- Partnership\n",
                    color=0xdefb48
                )
            )
            response = await self.bot.wait_for(
                events.DMMessageCreateEvent,
                180.0,
                lambda event: event.author.id == member.id
            )
            print(response.message.content)

            await member.send(
                    Embed(
                        description="Thanks for filling this form!",
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
                    description="That form timed out, to fill the same, use the command- `!welcome` and follow the instructions.",
                    color=0xff0000
                )
            )



    async def greeting(self, member):
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
                    description="That form timed out, to fill the same, use the command- `!welcome` and follow the instructions.",
                    color=0xff0000
                )
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
