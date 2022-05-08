import datetime
import re
from builtins import bool

import bonus
import gspread
from calendar import timegm
import time
import matplotlib.colors as colors


async def calculate(logging, client, options):
    start = timegm(datetime.datetime.strptime(input("Entrez la première date (dd/mm/yyyy): "), "%d/%m/%Y").utctimetuple())
    end = timegm(datetime.datetime.strptime(input("Entrez la deuxième date (dd/mm/yyyy): "), "%d/%m/%Y").utctimetuple())

    if start > end:
        print("La première date est postérieure à la deuxième")
        return

    guild = await client.fetch_guild(options['guildID'])
    channel = None
    purchases_channel = None
    vehicle_order_channel = None
    account_channel = None

    for ch in await guild.fetch_channels():
        if ch.id == int(options['channelID']):
            channel = ch

        if ch.id == int(options['purchasesChannelID']):
            purchases_channel = ch

        if ch.id == int(options['vehicleOrderChannelID']):
            vehicle_order_channel = ch

        if ch.id == int(options['accountChannelID']):
            account_channel = ch

    if channel is None:
        logging.error("Channel not found")
        exit(1)

    turnover = 0

    received_bills_total = 0
    received_bills = []

    async for message in channel.history(limit=5000):
        if start <= timegm(message.created_at.utctimetuple()) <= end:
            for embed in message.embeds:
                if embed.title != "Facture reçus":
                    break

                received_bill = {"author": "", "price": 0, "description": ""}
                for fieldsList in embed.description.split("\n"):
                    fields = fieldsList.split(": ") if fieldsList.__contains__(":") else fieldsList.split(" -> ")
                    if str(fields[0]) == "Auteur":
                        received_bill["author"] = fields[1]
                    elif str(fields[0]).replace(" ", "") == "Prix":
                        received_bill["price"] = int(fields[1])
                    elif str(fields[0]).replace(" ", "") == "Description":
                        received_bill["description"] = fields[1]

                received_bills.append(received_bill)

    total_tips = 0
    messages_bills_ids = []
    delivery_bills_total = 0
    normal_bills_total = 0
    async for message in channel.history(limit=5000):
        if start <= timegm(message.created_at.utctimetuple()) <= end:
            for embed in message.embeds:
                if embed.title != "Facture payée":
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
                    break

                messages_bills_ids.append(id)

                if received_bills.__contains__({'author': author, 'price': int(price), 'description': description}):
                    received_bills_total += int(price)
                    break

                try:
                    if "(" in description:
                        tip = re.search(r".*?\((.*?)\)", description).group(1)
                        tip = tip.replace("$", "").replace(" pb", "")
                        total_tips += int(tip)
                except:
                    pass

                if description.__contains__("[Livraison]"):
                    delivery_bills_total += int(price)
                else:
                    normal_bills_total += int(price)

                turnover += int(price)

    last_bill_id = messages_bills_ids[0]
    first_bill_id = messages_bills_ids[len(messages_bills_ids) - 1]

    others = int(input("Entrez le montant des autres achats: "))
    others_with_tax = others * 1.15
    tax_on_others = others_with_tax - others

    purchases = 0
    async for purchase in purchases_channel.history(limit=5000):

        if start <= timegm(purchase.created_at.utctimetuple()) <= end:
            for embed in purchase.embeds:
                if embed.title != "Achat":
                    break

                cost = 0
                for fieldsList in embed.description.split("\n"):
                    fields = fieldsList.split(": ")
                    if str(fields[0]).replace(" ", "") == "Coût":
                        cost = int(re.search(r'\d+', fields[1]).group())

                if cost == 0:
                    break

                purchases += cost

    vehicle_orders = 0
    async for vehicle_order in vehicle_order_channel.history(limit=5000):
        if start <= timegm(vehicle_order.created_at.utctimetuple()) <= end:
            for embed in vehicle_order.embeds:
                if embed.title != "Commande passée":
                    break

                vehicle_orders += int(re.search(r'\d+', embed.description).group())

    supplies = 0
    async for transactions in account_channel.history(limit=5000):
        if start <= timegm(transactions.created_at.utctimetuple()) <= end:
            for embed in transactions.embeds:
                if embed.title != "Dépot d'argent":
                    break

                supplies += int(re.search(r'\d+', embed.description).group())

    all_bonuses = await bonus.calculate(logging, client, options, first_bill_id, last_bill_id)
    before_tx = turnover / 1.149975

    conventional_bonus = 0
    for b in all_bonuses:
        conventional_bonus += int(all_bonuses[b])

    exceptional_bonus = int(input("Entrez le montant des primes exceptionnels : "))
    bonus_total = conventional_bonus + exceptional_bonus

    all_purchases = purchases + vehicle_orders + int(total_tips * 0.25)
    purchases_with_tax = all_purchases * 1.15
    tax_on_purchases = purchases_with_tax - all_purchases
    received_bills_without_tax = received_bills_total / 1.149975
    tax_on_received_bills = received_bills_total - received_bills_without_tax
    gross_profit = turnover - purchases_with_tax - received_bills_total - bonus_total - others_with_tax
    expenses = all_purchases + received_bills_without_tax + others + bonus_total
    expenses_with_tax = purchases_with_tax + received_bills_total + others_with_tax
    tax_on_expenses = expenses_with_tax - expenses
    perceived_taxes = before_tx * 0.15
    paid_taxes = tax_on_received_bills + tax_on_purchases + tax_on_others
    overpaid_taxes = perceived_taxes - paid_taxes
    employees_number = int(input("Entrez le nombre d'employés : "))
    management_cost_per_employee = int(input("Entrez les frais de gestion par employé : "))
    management_cost = management_cost_per_employee * employees_number
    overpaid_taxes_and_management_cost = overpaid_taxes + management_cost
    gross_profit_before_taxes = gross_profit - overpaid_taxes_and_management_cost
    tax_on_profit = gross_profit_before_taxes * 0.15
    taxes = tax_on_profit + overpaid_taxes_and_management_cost
    profit = gross_profit_before_taxes - taxes

    gc = gspread.service_account()
    sh = gc.create("CAPI - " + str(datetime.datetime.fromtimestamp(start).strftime("%d/%m/%Y")) + " à " + str(datetime.datetime.fromtimestamp(end).strftime("%d/%m/%Y")))

    print("Veuillez patienter... (ceci peut prendre quelques minutes)")

    wks = sh.get_worksheet(0)

    wks.update_acell('A2', 'Apports')
    wks.update_acell('A8', 'Dépenses')
    # Chiffre d'affaires
    wks.update_acell('B2', 'Chiffre d\'affaires')
    wks.update_acell('C2', int(turnover))
    wks.update_acell('D2', "Total des factures pourboirs inclus")

    # Apports des particuliers
    wks.update_acell('B3', 'Apports des particuliers')
    wks.update_acell('C3', int(supplies))
    wks.update_acell('D3', "Apports versés par les particuliers (indicatif)")

    # Total des pourboires
    wks.update_acell('B4', 'Total des pourboires')
    wks.update_acell('C4', int(total_tips))
    wks.update_acell('D4', "Pourboires versés à nos employés via les factures (utilisation fractionnée) ")

    # Avant les taxes
    wks.update_acell('B6', 'Avant les taxes')
    wks.update_acell('C6', int(before_tx))
    wks.update_acell('D6', "Chiffre d'affaire/1.49975")

    # Total des primes
    wks.update_acell('B8', 'Total des primes')
    wks.update_acell('C8', int(bonus_total))
    wks.update_acell('D8', "Primes versées aux employés (5$ par item vendu + 75% des pourboires) + primes exceptionnelles")

    # Achats + 25% des pourboires
    wks.update_acell('B9', 'Achats')
    wks.update_acell('C9', int(all_purchases))
    wks.update_acell('D9', "Achats réalisés par l'entreprise (matière première, véhicules, 25% des pourboires pour la nourriture des employés)")

    # Achats avec taxes
    wks.update_acell('B10', 'Achats avec taxes')
    wks.update_acell('C10', int(purchases_with_tax))
    wks.update_acell('D10', "Achats*1.15")

    # Taxe sur les achats
    wks.update_acell('B11', 'Taxe sur les achats')
    wks.update_acell('C11', int(tax_on_purchases))
    wks.update_acell('D11', "Achats avec taxes-Achats")

    # Total des factures reçues
    wks.update_acell('B12', 'Montant total des factures reçues avec taxes')
    wks.update_acell('C12', int(received_bills_total))
    wks.update_acell('D12', "Cumule des factures reçues au nom de l'entreprise (sortie de garage, réparations de véhicules de compagnie...)")

    # Factures reçues avec taxes
    wks.update_acell('B13', 'Factures reçues sans taxes')
    wks.update_acell('C13', int(received_bills_without_tax))
    wks.update_acell('D13', "Montant total des factures reçues/1.149975")

    # Taxe sur les factures
    wks.update_acell('B14', 'Taxe sur les factures')
    wks.update_acell('C14', int(tax_on_received_bills))
    wks.update_acell('D14', "Montant avec taxes-factures sans taxes")

    # Bénéfice brut
    wks.update_acell('B19', 'Bénéfice brut')
    wks.update_acell('C19', int(gross_profit))
    wks.update_acell('D19', "Chiffre d'affaire-(dépenses avec taxes+primes)")

    # Montant des autres achats
    wks.update_acell('B15', 'Montant des autres achats')
    wks.update_acell('C15', int(others))
    wks.update_acell('D15', "Montant total des achats exeptionnels de l'entreprise (évenements, publicité...)")

    # Montant des autres achats avec taxes
    wks.update_acell('B16', 'Montant des autres achats avec taxes')
    wks.update_acell('C16', int(others_with_tax))
    wks.update_acell('D16', "Montant des autres achats*1.15")

    # Taxe sur les autres achats
    wks.update_acell('B17', 'Taxe sur les autres achats')
    wks.update_acell('C17', int(tax_on_others))
    wks.update_acell('D17', "Montant des autres achats*-Montant total des autres achats")

    # Taxes perçues
    wks.update_acell('B21', 'Taxes perçues')
    wks.update_acell('C21', int(perceived_taxes))
    wks.update_acell('D21', "Chiffre d'affaire avant les taxes*0.15")

    # Taxes payées
    wks.update_acell('B22', 'Taxes payées')
    wks.update_acell('C22', int(paid_taxes))
    wks.update_acell('D22', "Cumule des taxes sur les dépenses")

    # Taxes en trop
    wks.update_acell('B23', 'Taxes en trop')
    wks.update_acell('C23', int(overpaid_taxes))
    wks.update_acell('D23', "Différence entre les taxes perçues et les taxes payées")

    time.sleep(60)

    # Nombre d'employés
    wks.update_acell('B25', 'Nombre d\'employés')
    wks.update_acell('C25', int(employees_number))
    wks.update_acell('D25', "Nombre d'employé à fin de la periode indiquée")

    # Frais de gestion par employé
    wks.update_acell('B26', 'Frais de gestion')
    wks.update_acell('C26', int(management_cost))
    wks.update_acell('D26', "Nombre d'employés*frais de géstion pour un employé (" + str(management_cost_per_employee) + "$)")

    # Taxes en trop et frais de gestion
    wks.update_acell('B28', 'Taxes en trop et frais de gestion')
    wks.update_acell('C28', int(overpaid_taxes_and_management_cost))
    wks.update_acell('D28', "Taxes perçues en trop + frais de gestion")

    # Bénéfice brut avant taxes
    wks.update_acell('B29', 'Bénéfice brut avant taxes')
    wks.update_acell('C29', int(gross_profit_before_taxes))
    wks.update_acell('D29', "Bénéfice brut-Taxes en trop et frais de gestion")

    # Taxe sur le bénéfice brut
    wks.update_acell('B30', 'Taxe sur le bénéfice brut')
    wks.update_acell('C30', int(tax_on_profit))
    wks.update_acell('D30', "Bénéfice but*0.15")

    # Impôts à remettre
    wks.update_acell('B33', 'Impôts à remettre')
    wks.update_acell('C33', int(taxes) if taxes > 0 else int(management_cost))

    # Bénéfice net
    wks.update_acell('B34', 'Bénéfice net')
    wks.update_acell('C34', int(profit))

    # Détail des factures
    wks.update_acell('F2', 'Détail des factures')
    wks.update_acell('F3', 'Livraison')
    wks.update_acell('G3', delivery_bills_total)
    wks.update_acell('F4', 'Non livrées')
    wks.update_acell('G4', normal_bills_total)

    # Détail des achats
    wks.update_acell('F8', 'Détail des achats')
    wks.update_acell('F9', 'Matières premières')
    wks.update_acell('G9', int(purchases))
    wks.update_acell('F10', 'Véhicules')
    wks.update_acell('G10', int(vehicle_orders))
    wks.update_acell('F11', '25% des pourboires')
    wks.update_acell('G11', int(total_tips * 0.25))

    # Résumé des dépenses
    wks.update_acell('F14', 'Résumé des dépenses')
    wks.update_acell('F15', 'Toutes les dépenses')
    wks.update_acell('G15', int(expenses))
    wks.update_acell('F16', 'Toutes les dépenses avec taxes')
    wks.update_acell('G16', int(expenses_with_tax))
    wks.update_acell('F17', 'Taxes sur les dépenses')
    wks.update_acell('G17', int(tax_on_expenses))

    # Détail des primes
    wks.update_acell('F19', 'Détail des primes')
    wks.update_acell('F20', 'Primes conventionelles')
    wks.update_acell('G20', int(conventional_bonus))
    wks.update_acell('F21', 'Primes exceptionnelles')
    wks.update_acell('G21', int(exceptional_bonus))

    wks.update_acell('D35', "POWERED BY C.A.P.I. & UWU'S CALC")

    wks.columns_auto_resize(0, 25)

    default_border = {"style": "SOLID_MEDIUM"}
    thin_border = {"style": "SOLID"}

    light_pink = {"red": colors.to_rgb("#d5a6bd")[0], "green": colors.to_rgb("#d5a6bd")[1], "blue": colors.to_rgb("#d5a6bd")[2]}

    wks.format("B33:C34", {
        "backgroundColor": light_pink
    })

    wks.format("C2:C31", {
        "borders": {
            "right": default_border,
        }
    })

    wks.format("A1:D1", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("A4:D4", {
        "borders": {
            "bottom": default_border,
            "right": default_border
        }
    })

    wks.format("A7:D7", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("A18:D18", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("A31:D31", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("D2:D30", {
        "borders": {
            "right": default_border,
            "bottom": thin_border
        }
    })

    wks.format("B2:C30", {
        "borders": {
            "bottom": thin_border,
        }
    })

    wks.format("D35", {
        "textFormat": {
            "fontFamily": "Verdana",
            "bold": True,
            "italic": True,
            "fontSize": 14,
            "foregroundColor": {
                "red": 102.0,
                "green": 102.0,
                "blue": 102.0,
                "alpha": 1.0
            }
        },
        "horizontalAlignment": "RIGHT"
    })

    time.sleep(60)

    green = {"red": colors.to_rgb("#b6d7a8")[0], "green": colors.to_rgb("#b6d7a8")[1], "blue": colors.to_rgb("#b6d7a8")[2]}

    wks.format("A2", {
        "backgroundColor": green
    })

    wks.format("B2:C4", {
        "backgroundColor": green
    })

    pink = {"red": colors.to_rgb("#ea9999")[0], "green": colors.to_rgb("#ea9999")[1], "blue": colors.to_rgb("#ea9999")[2]}

    wks.format("A8", {
        "backgroundColor": pink
    })

    wks.format("B8:C17", {
        "backgroundColor": pink
    })

    wks.format("A31:D31", {
        "borders": {
            "top": default_border
        }
    })

    wks.format("A4", {
        "borders": {
            "bottom": default_border,
        }
    })

    wks.format("B3:D3", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("A5:D5", {
        "borders": {
            "top": default_border,
        }
    })

    wks.format("A7:D7", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("B10:D10", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("B13:D13", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("B16:D16", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("A17:D17", {
        "borders": {
            "bottom": default_border
        }
    })

    wks.format("B22:D22", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("B25:D25", {
        "borders": {
            "bottom": None
        }
    })

    wks.format("B29:D29", {
        "borders": {
            "bottom": None,
            "top": None
        }
    })

    wks.format("B2:D2", {
        "borders": {
            "bottom": None
        }
    })

    wks.format("B21:D21", {
        "borders": {
            "bottom": None
        }
    })

    wks.format("B28:D28", {
        "borders": {
            "bottom": None
        }
    })

    wks.format("B6:D6", {
        "borders": {
            "top": thin_border,
            "bottom": thin_border
        }
    })

    wks.format("B9:D9", {
        "borders": {
            "top": None,
            "bottom": None
        }
    })

    wks.format("B12:D12", {
        "borders": {
            "top": thin_border,
            "bottom": None
        }
    })

    wks.format("B15:D15", {
        "borders": {
            "top": thin_border,
            "bottom": None
        }
    })

    wks.format("B21:D21", {
        "borders": {
            "top": thin_border,
            "bottom": None
        }
    })

    wks.format("B28:D28", {
        "borders": {
            "top": thin_border,
            "bottom": None
        }
    })

    wks.format("E2:E30", {
        "borders": {
            "left": default_border
        }
    })

    wks.format("A2:A30", {
        "borders": {
            "right": default_border,
        }
    })

    wks.format("C33", {
        "borders": {
            "left": thin_border,
            "right": default_border,
            "top": default_border,
            "bottom": thin_border
        }
    })

    wks.format("C34", {
        "borders": {
            "left": thin_border,
            "right": default_border,
            "top": thin_border,
            "bottom": default_border
        }
    })

    wks.format("B33", {
        "borders": {
            "left": default_border,
            "right": thin_border,
            "top": default_border,
            "bottom": thin_border
        }
    })

    wks.format("B34", {
        "borders": {
            "left": default_border,
            "right": thin_border,
            "top": thin_border,
            "bottom": default_border
        }
    })

    wks.format("A5", {
        "borders": {
            "top": default_border,
            "right": default_border
        }
    })

    wks.format("A8", {
        "borders": {
            "top": default_border,
            "right": default_border
        }
    })

    wks.format("A18", {
        "borders": {
            "top": default_border,
            "right": default_border
        }
    })

    wks.format("A31", {
        "borders": {
            "top": default_border
        }
    })

    wks.format("F8:F11", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": default_border,
            "right": None
        }
    })

    wks.format("G8:G11", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": None,
            "right": default_border
        }
    })

    wks.format("F8:F11", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": default_border,
            "right": None
        }
    })

    wks.format("G8:G11", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": None,
            "right": default_border
        }
    })

    wks.format("F8:G8", {
        "borders": {
            "bottom": thin_border
        }
    })

    wks.format("F14:F17", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": default_border,
            "right": None
        }
    })

    wks.format("G14:G17", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": None,
            "right": default_border
        }
    })

    wks.format("F14:G14", {
        "borders": {
            "bottom": thin_border
        }
    })

    wks.format("F19:F21", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": default_border,
            "right": None
        }
    })

    wks.format("G20:G21", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": None,
            "right": default_border
        }
    })

    wks.format("F19:F19", {
        "borders": {
            "bottom": default_border,
            "right": None,
            "left": None,
            "top": None
        }
    })

    wks.format("G3:G4", {
        "borders": {
            "top": default_border,
            "bottom": default_border,
            "left": None,
            "right": default_border
        }
    })

    wks.format("F3:F4", {
        "borders": {
            "bottom": default_border,
            "right": None,
            "left": default_border,
            "top": None
        }
    })

    sh.share("likemoi99@gmail.com", perm_type='user', role="writer", notify=False)
    sh.share("selim160706@gmail.com", perm_type='user', role="writer", notify=False)

    print("\nGénération terminée !")
    print("Voici l'url vers la feuille Google : " + sh.url)
    print("___________________________________________")






