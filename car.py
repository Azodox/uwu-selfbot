import gspread
import time
import random


async def calculate():
    gc = gspread.service_account()
    sheet = gc.open_by_url(input("Entrez l'url de la feuille google sheet: "))
    worksheet = sheet.get_worksheet(0)

    a_cells_range = int(input("Entrez le nombre de participants (nombre de cellules): "))

    participants = []
    for i in range(1, a_cells_range):
        if i == int(a_cells_range / 2):
            print("Attente d'une minute...")
            time.sleep(60)

        participant = worksheet.acell('A' + str(i)).value
        if participant != "Nom de l'inscrit":
            amount = worksheet.acell('B' + str(i)).value
            participants.append({"name": participant, "tickets": amount})

    entries = []
    for participant in participants:
        for i in range(int(participant["tickets"])):
            entries.append(participant["name"])

    entries.sort()
    print("===============================================================")
    print("Entrées :")
    print(entries)
    print("===============================================================")
    print("Gagnant : " + str(random.choice(entries)))
