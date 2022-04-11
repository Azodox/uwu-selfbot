import re

short_names_to_normal_prices = {
    "cg": 50,
    "cgv": 65,
    "cgc": 65,
    "c": 40,
    "cd": 40,
    "ca": 50,
    "cl": 45,
    "a": 45,
    "m": 50,
    "cc": 55,
    "ch": 45,
    "cr": 35,
    "mf": 40,
    "gfingsoif": 135,
    "choco'choco": 100,
    "lebonmatin": 75
}

short_names_to_delivery_prices = {
    "cg": 60,
    "cgv": 75,
    "cgc": 75,
    "c": 50,
    "cd": 50,
    "ca": 60,
    "cl": 55,
    "a": 55,
    "m": 60,
    "cc": 65,
    "ch": 55,
    "cr": 45,
    "mf": 50,
    "gfingsoif": 150,
    "choco'choco": 120,
    "lebonmatin": 95
}

def check_price(displayed_price, s):
    delivery = False
    discount = False

    total = 0

    try:
        bracketsOptions = re.findall(r'\[(.*?)\]', s)
        if bracketsOptions is not None:
            for option in bracketsOptions:
                if option == "Livraison":
                    delivery = True
                elif option == "Réduction 10%":
                    discount = True
        tip = 0
        if "(" in s:
            tip = re.search(r".*?\((.*?)\)", s).group(1)
            tip = tip.replace("$", "").replace(" pb", "")

        if discount is True or delivery is True:
            s = s.split("]")[2 if discount is True and delivery is True else 1]

        regex = r"(.*?){}".format(r"\(" if tip != 0 else "")
        content = re.search(regex, s).group(1) if regex != "(.*?)" else s
        split = re.split(r"([0-9]+)([a-z]+)", content.lower().replace(" ", ""))

        for i in range(0, len(split)):
            item = split[i]

            if item != "" and item.isnumeric() is False:
                price = int(split[i - 1]) * int(
                    short_names_to_normal_prices.get(item) if delivery is False else short_names_to_delivery_prices.get(
                        item))
                total += price
    except:
        return False


    if int(displayed_price) == (int(total + int(tip)) if discount is False else int(int(total + int(tip)) * 0.9)):
        return True
    else:
        return False