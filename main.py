import check
import json
import discord
import logging
from art import *

with open('config.json') as config_file:
    options = json.load(config_file)

    if options['token'] == "" or options['channelID'] == "" or options['guildID'] == "":
        logging.error("Invalid config.json")
        exit(1)


async def main():
    bonus = {}

    guild = await client.fetch_guild(options['guildID'])
    channel = None

    for ch in await guild.fetch_channels():
        if ch.id == int(options['channelID']):
            channel = ch

    if channel is None:
        logging.error("Channel not found")
        exit(1)

    print(text2art("HI BOSS", font="big"))

    non_valid_bills = []
    if input("Voulez-vous vérifier une facture en particulier ? (o/n) ") == "o":
        messageID = input("Entrez l'id du message contenant la facture : ")
        message = await channel.fetch_message(messageID)

        for embed in message.embeds:
            if embed.title != "Facture payée":
                print("This message is not a bill")
                break

            id = ""
            author = ""
            price = ""
            description = ""
            for fieldsList in embed.description.split("\n"):
                fields = fieldsList.split(": ") if not None else fieldsList.split(" -> ")
                if str(fields[0]) == "Facture ID":
                    id = fields[1]
                elif str(fields[0].replace(" ", "")) == "Auteur":
                    author = fields[1]
                elif str(fields[0].replace(" ", "")) == "Prix":
                    price = fields[1]
                elif str(fields[0].replace(" ", "")) == "Description":
                    description = fields[1]

            if id == "" or author == "" or price == "" or description == "":
                print("The bill is not well formatted, skipping...")
                break

            print("Bill found : " + id)
            result = await check.check_price(int(price), description)

            if result['value'] is True:
                print("Bill " + id + " is valid.")
                if bonus.get(author) is None:
                    bonus.__setitem__(author, result['prime'])
                else:
                    bonus[author] += result['prime']
            else:
                print("Bill " + id + " is not valid.")
                non_valid_bills.append(id)
    else:
        end = input("Entrez l'id de la première facture : ")
        start = input("Entrez l'id de la dernière facture : ")

        bills = []
        automatically_add = False
        async for message in channel.history(limit=int(input("Combien de messages de facture avez-vous besoin de récupérer ? "))):
            for embed in message.embeds:
                if embed.title != "Facture payée":
                    print("Found a non-paid bill, skipping...")
                    break

                id = ""
                author = ""
                price = ""
                description = ""
                for fieldsList in embed.description.split("\n"):
                    fields = fieldsList.split(": ") if not None else fieldsList.split(" -> ")
                    if str(fields[0]) == "Facture ID":
                        id = fields[1]
                    elif str(fields[0].replace(" ", "")) == "Auteur":
                        author = fields[1]
                    elif str(fields[0].replace(" ", "")) == "Prix":
                        price = fields[1]
                    elif str(fields[0].replace(" ", "")) == "Description":
                        description = fields[1]

                if id == "" or author == "" or price == "" or description == "":
                    print("Found a bill with missing fields, skipping...")
                    break

                if id == start:
                    print("Found the first bill.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})
                    automatically_add = True

                if automatically_add is True:
                    print("Adding bill " + id + " to the list.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})

                if id == end:
                    print("Found the last bill.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})
                    automatically_add = False

        for bill in bills:
            id = bill['id']
            author = bill['author']
            price = int(bill['price'])
            description = bill['description']

            result = await check.check_price(price, description)
            if result['value'] is True:
                print("Bill " + id + " is valid.")
                if bonus.get(author) is None:
                    bonus.__setitem__(author, result['prime'])
                else:
                    bonus[author] += result['prime']
            else:
                print("Bill " + id + " is not valid.")
                non_valid_bills.append(id)

    print("----------------------------------------------------")
    print("Factures non valides : " + str(non_valid_bills))
    print("Nombre de factures non valides : " + str(len(non_valid_bills)))
    print("Primes : " + str(bonus))
    print("----------------------------------------------------")


class Client(discord.Client):
    async def on_ready(self):
        print('Logged in as', self.user)
        await main()


client = Client()
client.run(options['token'])