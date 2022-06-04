import check
from art import *


async def calculate(logging, client, options, first_bill_id=None, last_bill_id=None):
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
        end = input("Entrez l'id de la première facture : ") if first_bill_id is None else first_bill_id
        start = input("Entrez l'id de la dernière facture : ") if last_bill_id is None else last_bill_id

        bills = []
        bills_done_ids = []
        automatically_add = False
        async for message in channel.history(
                limit=int(input("Combien de messages de facture avez-vous besoin de récupérer ? ")) if first_bill_id is None and last_bill_id is None else 5000):
            for embed in message.embeds:
                if embed.title != "Facture payée":
                    print("Found a non-paid bill, skipping...")
                    break

                id = ""
                author = ""
                price = ""
                description = ""
                for fieldsList in embed.description.split("\n"):
                    fields = fieldsList.split(": ") if fieldsList.__contains__(":") else fieldsList.split(" -> ")
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
                    bills_done_ids.append(id)
                    automatically_add = True

                if automatically_add is True and bills_done_ids.__contains__(id) is False:
                    print("Adding bill " + id + " to the list.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})
                    bills_done_ids.append(id)

                if id == end:
                    print("Found the last bill.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})
                    bills_done_ids.append(id)
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
    return bonus

