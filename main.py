import discum
import check
import json

with open('config.json') as config_file:
    options = json.load(config_file)

primes = {}
bot = discum.Client(token=options['token'])
end = input("Entrez l'id de la première facture : ")
start = input("Entrez l'id de la dernière facture : ")
billings = []

automaticallyAdd = False
for message in bot.getMessages(options['channelID'], 100).json():
    embeds = message['embeds']

    for embed in embeds:
        if embed['title'] != "Facture payée":
            break

        id = ""
        author = ""
        price = ""
        description = ""
        for fieldsList in embed['description'].split("\n"):
            fields = fieldsList.split(": ")
            if fields[0] == "Facture ID":
                id = fields[1]
            elif fields[0] == "Auteur":
                author = fields[1]
            elif fields[0] == "Prix":
                price = fields[1]
            elif fields[0] == "Description":
                description = fields[1]

        if id == "" or author == "" or price == "" or description == "":
            break

        if id == start:
            billings.append({"id": id, "author": author, "price": price, "description": description})
            automaticallyAdd = True

        if automaticallyAdd is True:
            billings.append({"id": id, "author": author, "price": price, "description": description})

        if id == end:
            billings.append({"id": id, "author": author, "price": price, "description": description})
            automaticallyAdd = False


for billing in billings:
    id = billing['id']
    author = billing['author']
    price = int(billing['price'])
    description = billing['description']

    result = check.check_price(price, description)
    if result['value'] is True:
        if primes.get(author) is None:
            primes.__setitem__(author, result['prime'])
        else:
            primes[author] += result['prime']

print(primes)