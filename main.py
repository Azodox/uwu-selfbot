import bonus
import json
import discord
import logging
import taxes
import car

print("Loading...")

with open('config.json') as config_file:
    options = json.load(config_file)

    if options['token'] == "" or options['channelID'] == "" or options['guildID'] == "":
        logging.error("Invalid config.json")
        exit(1)


async def main():
    mode = input("Voulez-vous calculer les taxes ou les primes ou les résultats de la voiture ? (taxes/primes/voiture) ")
    if mode == "taxes":
        await taxes.calculate(logging, client, options)

    if mode == "primes":
        await bonus.calculate(logging, client, options)

    if mode == "voiture":
        await car.calculate()


class Client(discord.Client):
    async def on_ready(self):
        print('Logged in as', self.user)
        await main()


client = Client()
client.run(options['token'])