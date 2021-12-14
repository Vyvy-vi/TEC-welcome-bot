import os
from dotenv import load_dotenv

import asyncio

import dhooks_lite

import lightbulb
from hikari import Intents, Embed, events, errors


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
        self.questions = [
            {
                "title": "How would you like to be addressed?",
                "sub": "What name(s) and pronouns would you like us to use?",
                "type": "text"
            },
            {
                "title": "Why did you come to the TEC?",
                "options": [
                    "[Curious] - I’m curious to learn more about TEC in general",
                    "[Future Contributor] - I’d like to contribute to building or improving the TEC",
                    "[Proposals] - I’d like to submit a proposal in order to receive TEC funding",
                    "[Partnerships] - I want to build a partnership between my DAO and the TEC",
                    "[Education] - I want to learn more about Web3, DAOs, and/or Token Engineering",
                    "[Other] - [Long Answer Text Box]"
                ],
                "emojis": [
                    '🤔',
                    '🛠️',
                    '📜',
                    '🤝',
                    '📚',
                    '➕'
                ],
                "type": "choice"
            },
            {
                "title": "How familiar are you with web3?",
                "type": "text"
            },
            {
                "title": "How did you find out about the TEC?",
                "type": "text"
            },
            {
                "title": "Which timezone are you in?",
                "type": "text"
            }
        ]

    async def form_runner(self, member):
        try:
            details = []

            for ques in self.questions:
                if ques['type'] == 'text':
                    await member.send(
                        Embed(
                            title=ques['title'],
                            description=ques['sub'] if 'sub' in ques else None,
                            color=0xdefb48
                        )
                    )
                    response = await self.bot.wait_for(
                        events.DMMessageCreateEvent,
                        180.0,
                        lambda event: event.author.id == member.id
                    )
                    details.append(response.message.content)
                elif ques['type'] == 'choice':
                    msg = await member.send(
                        Embed(
                            title=ques['title'],
                            description="React with an emoji to make your choice for this question:\n\n" + '\n'.join([f"{ques['emojis'][i]} {ques['options'][i]}" for i in range(len(ques['options']))]),
                            color=0xdefb48
                        )
                    )

                    for emoji in ques['emojis']:
                        await msg.add_reaction(emoji)

                    content = ""

                    try:
                        reaction = await self.bot.wait_for(
                            events.DMReactionAddEvent,
                            180.0,
                            lambda event: (event.user_id == member.id) and (event.emoji_name in ques['emojis'])
                        )
                        content += [ques["options"][i] for i in range(len(ques['options'])) if ques['emojis'][i] == reaction.emoji_name][0]
                        if reaction.emoji_name == emoji[-1]:
                            await member.send(Embed(description="You can enter a more detailed description in a message below..."))
                            response = await self.bot.wait_for(
                                events.DMMessageCreateEvent,
                                180.0,
                                lambda event: event.author_id == member.id
                            )
                            content += f'\n{response.message.content}'

                        details.append(content)
                    except asyncio.TimeoutError:
                        for emoji in ques['emojis']:
                            await msg.remove_reaction(
                                emoji,
                                user=self.bot.get_me()
                            )

                else:
                    await member.send("Something's wrong... Oh no!")


            def get_field(i):
                title = self.questions[i].get('title')
                sub =  self.questions[i].get('sub')

                title = '' if not title else title
                sub = '' if not sub else sub
                return f"**{title + ' - ' + sub}**\n{details[i]}"

            self.log_channel_hook.execute(
                embeds=[dhooks_lite.Embed(
                    title=f"{member} joined the server!",
                    description="\n\n".join(
                        [f"{get_field(i)}" for i in range(len(details))]
                    ),
                    color=0xdefb48
                )]
            )


            await member.send(
                Embed(
                    description="Thanks for filling out this form! To continue your journey, visit the #your-guide channel...",
                    color=0x00ff00
                )
            )

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
        try:
            print(f"{event.member} entered the server...")
            """
            self.add_data(
                str(event.member.id),
                event.member.username + '#' + event.member.discriminator
            )
            """
        except Exception as e:
            await event.member.send(f"Error -\n{e}")
            print(e)
        await self.greeting(event.member)


bot.add_plugin(WelcomePlugin(bot))
bot.run()
