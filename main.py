import discord
import sqlite3

client = discord.Client()
database_name = "polybot.db"

intents = discord.Intents.default()
intents.members = True


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    # check that this message wasn't sent by the bot
    if message.author == client.user:
        return

    if message.content.startswith("polybot"):
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
    if split_message[1].lower() == "hello":
        print("I was greeted by " + get_name(message.author))
        return_message = "Hello " + get_name(message.author) + "!"
        await message.channel.send(return_message)
        return

    # say hello to someone else when asked
    if split_message[1].lower() == "greet":
        print("I was asked to greet someone by " + get_name(message.author))
        return_message = "You need to ping a user to greet"
        if len(message.mentions) != 0:
            return_message = "Hello " + get_name(message.mentions[0]) + "!"

        await message.channel.send(return_message)
        return

    # respond if someone thanks polybot
    if split_message[1].lower() == "thanks":
        print("I was thanked by " + get_name(message.author))
        return_message = "You're welcome " + get_name(message.author) + " <3"
        await message.channel.send(return_message)
        return

    # add a potential relationship or confirm one
    if split_message[1] == "add":
        print("I was asked to add a relationship by " + get_name(message.author))
        if split_message[2].lower() == "qpp" \
                or split_message[2].lower() == "fwb" \
                or split_message[2].lower() == "partner":
            return_message = add_relationship(message, split_message[2].lower())
            await message.channel.send(return_message)
        else:
            return_message = "You need to include a valid relationship type, these are currently QPP, FWB, and partner"
            await message.channel.send(return_message)


def add_relationship(message, relationship_type):
    # check if this message mentions someone
    if len(message.mentions) == 0:
        return "You must mention someone to ask them to be in a relationship with you"
    connection = sqlite3.connect(database_name)
    cur = connection.cursor()
    asker = message.author
    asked = message.mentions[0]

    # check if the asker is asking someone else
    if asker == asked:
        return "You can\'t ask to be in a relationship with yourself, silly"

    # check if the asker has already asked for this relationship type
    cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type), (asker.id, asked.id))
    existing_relationship = cur.fetchone()
    if existing_relationship is not None:
        if existing_relationship[2] == 0:
            return get_name(asker) + " has previously asked " + get_name(asked) + " to be their " + relationship_type
        elif existing_relationship[2] == 1:
            return get_name(asked) + " is already " + get_name(asker) + "\'s " + relationship_type

    # figure out if this is creating a new relationship or confirming one
    cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type), (asked.id, asker.id))
    if cur.fetchone() is not None:
        cur.execute("UPDATE {} SET confirmed = 1 WHERE asker = ? AND asked = ?".format(relationship_type),
                    (asked.id, asker.id))
        connection.commit()
        connection.close()
        return get_name(asker) + " has confirmed their relationship with " + get_name(asked)
    else:
        cur.execute("INSERT INTO {} VALUES (?, ?, ?)".format(relationship_type), (asker.id, asked.id, 0))
        connection.commit()
        connection.close()
        return get_name(asker) + " has asked " + get_name(asked) + " to be their " + relationship_type


# load the token from a file so that it isn't uploaded to GitHub
token = open("token.txt", "r").readline()
client.run(token)
