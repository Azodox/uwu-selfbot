import bonus
import json
import discord
import logging
import taxes
import car
import stats

print("Loading...")

with open('config.json') as config_file:
    options = json.load(config_file)

    if options['token'] == "" or options['channelID'] == "" or options['guildID'] == "":
        logging.error("Invalid config.json")
        exit(1)


async def main():
    mode = input("Voulez-vous calculer les taxes, les primes, les résultats de la voiture ou les statistiques de la compagnie? (taxes/primes/voiture/stats) ")
    if mode == "taxes":
        await taxes.calculate(logging, client, options)

    if mode == "primes":
        await bonus.calculate(logging, client, options)

    if mode == "voiture":
        await car.calculate()

    if mode == "stats":
        await stats.calculate(logging, client, options)


class Client(discord.Client):
    async def on_ready(self):
        print('Logged in as', self.user)
        await main()


client = Client()
client.run(options['token'])