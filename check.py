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
    tip = 0
    if "(" in s:
        tip = re.search(r".*?\((.*?)\)", s).group(1)
        tip = tip.replace("$", "").replace(" pb", "")

    if discount is True or delivery is True:
        s = s.split("]")[2 if discount is True and delivery is True else 1]

    print("Discount: " + str(discount))
    print("Delivery: " + str(delivery))
    print("Tip: " + str(tip))
    regex = r"(.*?){}".format(r"\(" if tip != 0 else "")
    content = re.search(regex, s).group(1) if regex != "(.*?)" else s
    split = re.split(r"([0-9]+)([a-z]+)", content.lower().replace(" ", ""))

    try:
        for i in range(0, len(split)):
            item = split[i]

            if item != "" and item.isnumeric() is False:
                amount = int(split[i - 1])
                total_price = amount * int(short_names_to_normal_prices.get(item) if delivery is False else int(short_names_to_delivery_prices.get(item)))
                total += total_price
                prime += 5 * amount
    except Exception as e:
        print("Found a bill with invalid declaration, skipping...")
        return {"value": False, "prime": 0}

    if int(displayed_price) == (int(total + int(tip)) if discount is False else int(int(total * 0.9) + int(tip))):
        if tip != 0:
            prime += int(int(tip) * 0.75)
        return {"value": True, "prime": prime}
    else:
        return {"value": False, "prime": 0}