import time
import discord
import sqlite3
import graphviz

client = discord.Client()
database_name = "polybot.db"
relationship_types = ["qpp", "fwb", "partner"]

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

    if message.content.startswith(">polybot"):
        await process_command(message)


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
        if split_message[2].lower() in relationship_types:
            return_message = await add_relationship(message, split_message[2].lower())
            await message.channel.send(return_message)
        else:
            return_message = "You need to include a valid relationship type, these are currently QPP, FWB, and partner"
            await message.channel.send(return_message)

    if split_message[1] == "status":
        print("I was asked for the relationship status of " + get_name(message.author))
        return_message = await relationship_status(message)
        await message.channel.send(return_message)

    if split_message[1] == "remove":
        print("I was asked to remove a relationship by " + get_name(message.author))
        return_message = await remove_relationship(message)
        await message.channel.send(return_message)

    if split_message[1] == "display":
        print("I was asked to display the polycule of " + get_name(message.author))
        polycule_image = await display_polycule(message)
        await message.channel.send("Here is " + get_name(message.author) + "\'s polycule", file=polycule_image)


async def add_relationship(message, relationship_type):
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
            connection.close()
            return get_name(asker) + " has previously asked " + get_name(asked) + " to be their " + relationship_type
        elif existing_relationship[2] == 1:
            connection.close()
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


async def relationship_status(message):
    if len(message.mentions) == 0:
        return "You must mention someone to find out your status with them"
    asker = message.author
    asked = message.mentions[0]

    # check if the person is asking for their status with themself
    if asker == asked:
        return "You can\'t ask for your status with yourself, silly"

    # check if a confirmed relationship exists
    for relationship_type in relationship_types:
        if check_relationship(relationship_type, asker, asked, 1):
            return get_name(asked) + " is your " + relationship_type
    # check if either person has asked to be in a relationship with the other
    for relationship_type in relationship_types:
        if check_relationship(relationship_type, asker, asked, 0):
            # connect to database
            connection = sqlite3.connect(database_name)
            cur = connection.cursor()
            # see if the person who asked to be in a relationship was the one who requested the status
            cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asker.id, asked.id))
            potential_relationship = cur.fetchone()
            if potential_relationship is not None:
                connection.close()
                return "you asked " + get_name(asked) + " to be your " + relationship_type + \
                       " but they have not accepted it"
            cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asked.id, asker.id))
            potential_relationship = cur.fetchone()
            if potential_relationship is not None:
                connection.close()
                return get_name(asked) + " asked you to be their " + relationship_type + " but you have not accepted it"

    return "You are not in a relationship with " + get_name(asked)


async def check_relationship(relationship_type, asker, asked, confirmed):
    # connect to the database
    connection = sqlite3.connect(database_name)
    cur = connection.cursor()
    # check if a relationship exists
    cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type), (asker.id, asked.id))
    existing_relationship = cur.fetchone()
    if existing_relationship is not None:
        if existing_relationship[2] == confirmed:
            connection.close()
            return True
    # and do the same but with the opposite asker
    cur.execute("SELECT * FROM {} WHERE asker = ? AND asked = ?".format(relationship_type), (asked.id, asker.id))
    existing_relationship = cur.fetchone()
    if existing_relationship is not None:
        if existing_relationship[2] == confirmed:
            connection.close()
            return True
    connection.close()
    return False


async def remove_relationship(message):
    # check if this message mentions someone
    if len(message.mentions) == 0:
        return "You must mention someone to remove them from a relationship with you"
    connection = sqlite3.connect(database_name)
    cur = connection.cursor()
    asker = message.author
    asked = message.mentions[0]

    # check if the asker is asking someone else
    if asker == asked:
        return "You can\'t remove a relationship with yourself, silly"

    # check for a confirmed relationship
    for relationship_type in relationship_types:
        if check_relationship(relationship_type, asker, asked, 1):
            cur.execute("DELETE FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asker.id, asked.id))
            cur.execute("DELETE FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asked.id, asker.id))
            connection.commit()
            connection.close()
            return get_name(asked) + " is no longer your " + relationship_type
    # check if either person has asked to be in a relationship with the other
    for relationship_type in relationship_types:
        if check_relationship(relationship_type, asker, asked, 0):
            cur.execute("DELETE FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asker.id, asked.id))
            cur.execute("DELETE FROM {} WHERE asker = ? AND asked = ?".format(relationship_type),
                        (asked.id, asker.id))
            connection.commit()
            connection.close()
            return "the pending relationship between you and " + get_name(asked) + " has been removed"
    return "you do not have a relationship with " + get_name(asked)


async def display_polycule(message):
    # create an array to keep track of the relationships directly from the database
    raw_relationships = []
    # connect to the database
    connection = sqlite3.connect(database_name)
    cur = connection.cursor()

    asker = message.author
    for relationship_type in relationship_types:
        cur.execute("SELECT * FROM {} WHERE asker = ? OR asked = ?".format(relationship_type), (asker.id, asker.id))
        relationships_to_add = cur.fetchall()
        for relationship in relationships_to_add:
            raw_relationships.append({"relationship": relationship, "type": relationship_type})

    # create an array of easier to use relationships
    relationships = []
    for raw_relationship in raw_relationships:
        # check if this relationship has been confirmed
        if raw_relationship.get("relationship")[2] == 1:
            relationship_asker = await get_user_from_id(raw_relationship.get("relationship")[0])
            relationship_asked = await get_user_from_id(raw_relationship.get("relationship")[1])
            relationship = {"asker": relationship_asker,
                            "asked": relationship_asked,
                            "type": raw_relationship.get("type")}
            relationships.append(relationship)

    # create an array for the people in the polycule
    people = []
    for relationship in relationships:
        if relationship.get("asker") not in people:
            people.append(relationship.get("asker"))
        if relationship.get("asked") not in people:
            people.append(relationship.get("asked"))

    # add each person as a node
    polycule = graphviz.Graph(comment=get_name(asker) + "\'s Polycule", format="png", directory="graphviz_output",
                              renderer="cairo")
    for person in people:
        polycule.node(str(person.id), str(person.id))

    # add each relationship as an edge
    for relationship in relationships:
        polycule.edge(str(relationship.get("asker").id), str(relationship.get("asked").id))

    # use the time that the rendering starts as the filename because this is effectively unique
    rendered_at = str(time.time_ns())
    polycule.filename = rendered_at
    polycule.render(cleanup=True)
    return discord.File("graphviz_output/" + rendered_at + ".cairo.png")


async def get_user_from_id(user_id):
    # get the user if it is cached
    user = client.get_user(user_id)

    # get it from discord if it's not
    if user is None:
        user = await client.fetch_user(user_id)

    return user


def get_name(user):
    if user.nick is not None:
        return user.nick
    else:
        return user.name


# load the token from a file so that it isn't uploaded to GitHub
token = open("token.txt", "r").readline()
client.run(token)
