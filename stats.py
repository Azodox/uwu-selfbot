from calendar import timegm
import datetime
import check
import re
import gspread
from collections import Counter
import time

short_names_to_full_names = {
    "cg": "Café Glacé",
    "cgv": "Café Glacé Vanille",
    "cgc": "Café Glacé Caramel",
    "c": "Café",
    "cd": "Café Décaféiné",
    "ca": "Cappuccino",
    "cl": "Café Latte",
    "a": "Americano",
    "m": "Moka",
    "cc": "Chocolat Chaud",
    "ch": "Chocolatine",
    "cr": "Croissant",
    "mf": "Muffin",
    "cgn": "Café Glacé Noisette",
    "mo": "Mochi",
    "ra": "Ramen",
    "bb": "Booster Box",
    "bp": "Booster Pack",
    "tg": "Thé Glacé",
    "gfingsoif": "gfingfsoif",
    "chocochoco": "chocochoco",
    "lebonmatin": "lebonmatin",
    "mac": "mac and cheese",
    "cs": "packet de chips"
}

sold_quantity_per_product = {}


async def calculate(logging, client, options):
    start = timegm(datetime.datetime.strptime(input("Entrez la première date (dd/mm/yyyy): "), "%d/%m/%Y").utctimetuple())
    end = timegm(datetime.datetime.strptime(input("Entrez la deuxième date (dd/mm/yyyy): "), "%d/%m/%Y").utctimetuple())

    if start > end:
        print("La première date est postérieure à la deuxième")
        return

    guild = await client.fetch_guild(options['guildID'])
    channel = None

    for ch in await guild.fetch_channels():
        if ch.id == int(options['channelID']):
            channel = ch

    if channel is None:
        logging.error("erreur de login")
        exit(1)

    bills = []
    bills_done_ids = []
    async for message in channel.history(limit=int(100000)):
        if start <= timegm(message.created_at.utctimetuple()) <= end:
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

                if bills_done_ids.__contains__(id) is False:
                    print("Adding bill " + id + " to the list.")
                    bills.append({"id": id, "author": author, "price": price, "description": description})
                    bills_done_ids.append(id)

    products_stats = {}

    for bill in bills:
        id = bill['id']
        author = bill['author']
        price = int(bill['price'])
        description = bill['description']

        result = await check.check_price(price, description, True)
        if result['value'] is True:
            print("Bill " + id + " is valid.")
            products_stats = Counter(products_stats) + Counter(get_products_stats_of_one_bill(description))
        else:
            continue
    print(products_stats)
    create_spreadsheet(start, end, products_stats)


def get_products_stats_of_one_bill(s):
    products_stats = {}

    delivery = False
    discount = False
    public_service = False
    tenten = False

    brackets_options = re.findall(r'\[(.*?)\]', s)
    if brackets_options is not None:
        for option in brackets_options:
            if option == "Livraison":
                delivery = True
            elif option == "Réduction 10%":
                discount = True
            elif option == "Service Public":
                public_service = True
            elif option == "10-10":
                tenten = True

    try:
        tip = 0
        if "(" in s:
            tip = re.search(r".*?\((.*?)\)", s).group(1)
            tip = tip.replace("$", "").replace(" pb", "")

        if discount is True or delivery is True or public_service is True:
            s = s.split("]")[2 if discount is True and delivery is True else 1]

        regex = r"(.*?){}".format(r"\(" if tip != 0 else "")
        content = re.search(regex, s).group(1) if regex != "(.*?)" else s
        split = re.split(r"([0-9]+)([a-z]+)", content.lower().replace(" ", ""))

        for i in range(0, len(split)):
            item = split[i]

            if item != "" and item.isnumeric() is False:
                amount = int(split[i - 1])
                if products_stats.__contains__(item) is True:
                    products_stats[item] += amount
                else:
                    products_stats.__setitem__(item, amount)
        return products_stats
    except:
        print("Found a bill with invalid declaration, skipping...")
        return products_stats


def create_spreadsheet(start, end, products_stats):
    gc = gspread.service_account()
    sh = gc.create("CAPI Stats - " + str(datetime.datetime.fromtimestamp(start).strftime("%d/%m/%Y")) + " à " + str(datetime.datetime.fromtimestamp(end).strftime("%d/%m/%Y")))

    print("Veuillez patienter, nous calculons.")
    wks = sh.get_worksheet(0)
    for i in range(0, len(products_stats)):
        product = list(products_stats)[i]
        wks.update_acell('A' + str(i+1), short_names_to_full_names[product])
        wks.update_acell('B' + str(i+1), products_stats[product])
    sh.share("selim160706@gmail.com", perm_type='user', role="writer", notify=False)
    sh.share("likemoi99@gmail.com", perm_type='user', role="writer", notify=False)
    print("FINITO")