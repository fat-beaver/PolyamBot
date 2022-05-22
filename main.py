import discord

client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    # check that this message wasn't sent by the bot
    if message.author == client.user:
        return

    if message.content.startswith("/polybot"):
        await process_command(message)


def get_name(user):
    if user.nick is not None:
        return user.nick
    else:
        return user.name


# process a command, assuming it starts with /polybot
async def process_command(message):
    split_message = message.content.split(" ")
    # say hello back if someone says hello to the bot
    if split_message[1] == "hello":
        author = message.author
        return_message = "Hello " + get_name(author) + "!"
        await message.channel.send(return_message)
        return

    # say hello to someone else when asked
    if split_message[1] == "greet":
        return_message = "You need to ping a user to greet"
        if len(message.mentions) != 0:
            return_message = "Hello " + get_name(message.mentions[0]) + "!"

        await message.channel.send(return_message)
        return
    # respond if someone thanks polybot
    if split_message[1] == "thanks":
        author = message.author
        return_message = "You're welcome " + get_name(author) + " <3"
        await message.channel.send(return_message)
        return


# load the token from a file so that it does not get uploaded to GitHub
token = open("token.txt", "r").readline()
client.run(token)
