import re

short_names_to_normal_prices = {
    "cg": 70,
    "cgv": 85,
    "cgc": 85,
    "c": 60,
    "cd": 60,
    "ca": 70,
    "cl": 65,
    "a": 65,
    "m": 70,
    "cc": 75,
    "ch": 65,
    "cr": 55,
    "mf": 60,
    "gfingsoif": 160,
    "chocochoco": 140,
    "lebonmatin": 115,
    "mac": 100
}

short_names_to_delivery_prices = {
    "cg": 80,
    "cgv": 95,
    "cgc": 95,
    "c": 70,
    "cd": 70,
    "ca": 80,
    "cl": 75,
    "a": 75,
    "m": 80,
    "cc": 85,
    "ch": 75,
    "cr": 65,
    "mf": 70,
    "gfingsoif": 180,
    "chocochoco": 160,
    "lebonmatin": 135,
    "mac": 110
}


async def check_price(displayed_price: int, s: str):
    delivery = False
    discount = False

    total = 0
    prime = 0

    brackets_options = re.findall(r'\[(.*?)\]', s)
    if brackets_options is not None:
        for option in brackets_options:
            if option == "Livraison":
                delivery = True
            elif option == "Réduction 10%":
                discount = True

    try:
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
                amount = int(split[i - 1])
                total_price = amount * int(short_names_to_normal_prices.get(item) if delivery is False else int(short_names_to_delivery_prices.get(item)))
                total += total_price
                prime += 5 * amount

        if int(displayed_price) == (int(total + int(tip)) if discount is False else int(int(total * 0.9) + int(tip))):
            if tip != 0:
                prime += int(int(tip) * 0.75)
            return {"value": True, "prime": prime}
        else:
            return {"value": False, "prime": 0}
    except:
        print("Found a bill with invalid declaration, skipping...")
        return {"value": False, "prime": 0}
