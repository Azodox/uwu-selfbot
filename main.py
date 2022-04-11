import discum
import check

primes = {}
bot = discum.Client(token=input("Entrez votre token Discord : "))

for message in bot.getMessages("962296635642220597", 100).json():
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

        if check.check_price(price, description) is True:
            if primes.get(author) is None:
                primes.__setitem__(author, int(price))
            else:
                primes[author] += int(price)

print(primes)