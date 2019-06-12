import requests
import json
import configparser
import logging
import os
import gspread
import datetime
from time import sleep
from pprint import pformat
from fuzzywuzzy import fuzz
from math import log as LOG
from oauth2client.service_account import ServiceAccountCredentials


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", 'w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

class Sheets:
	sheet = None

	def __init__(self):
		try:
			log.info('Connecting to Google Sheets...')
			scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			creds = ServiceAccountCredentials.from_json_keyfile_name('secret.json', scope)
			client = gspread.authorize(creds)
			self.sheet = client.open('Pinn Line').sheet1
			log.info('Successfuly connected to Google Sheet')
		except:
			log.error('GSheets connect error: ', exc_info=True)

	def getvalues(self):
		if self.sheet:
			allvalues = self.sheet.get_all_values()
			if len(allvalues) > 1:
				eventslist = []
				for event in alexline:
					eventslist.append(event['event'])

				for index, item in enumerate(allvalues[1:]):
					if item[0] and len(item[0]) > 3 and item[1] and len(item[1]) > 3 and \
						item[2] and len(item[2]) > 0 and item[3] and len(item[3]) > 0:

						if f'{item[0]} - {item[1]}' not in eventslist:
							alexline.append({
								'event': f'{item[0]} - {item[1]}',
								'p1': item[0],
								'p2': item[1],
								'p1_odds': item[2],
								'p2_odds': item[3],
								'isfound': False,
								'odds': {'value': False},
								'bet': {'moneyline': False, 'hdp': False}
							})
							log.info(f'Got new event row: "{item[0]} - {item[1]} @ {item[2]} - {item[3]}"')

			elif len(allvalues) < 1:
				log.warning('Got fully empty sheet')


class Pinnacle:
	AUTH = ''
	URL = 'https://api.pinnacle.com'
	proxydict = {}
	def __init__(self):
		config = configparser.ConfigParser()
		if os.path.isfile('config.ini'):
			config.read('config.ini')
			try:
				self.AUTH = config['Pinnacle']['KEY']
			except Exception as e:
				log.error(f'[Pinnacle] "KEY" constant with auth key not found: {e}' )
			try:
				self.proxydict['main'] = config['Proxy']['Main']
			except Exception as e:
				log.error(f'Proxy not found: {e}')
		else:
			log.error('config.ini file not found')


	def lines_sports(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		try:
			res = requests.get(f'{self.URL}/v2/sports', headers=headers)
			if res.status_code == requests.codes.ok:
				log.debug(f'Lines Sports:\n{res.json()}')
				return res.json()
			else:
				log.error(f'Lines Sports request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get Lines Sports: ', exc_info=True)


	def find_sport_tennis(self, sports_list):
		for index in sports_list['sports']:
			if index['name'] == 'Tennis':
				return index['id']


	def lines_fixtures(self, sportId, since=None):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/fixtures?sportId={sportId}{since}', headers=headers)
			if res.status_code == requests.codes.ok:
				if res and len(res.content) > 0:
					return res.json()
				else:
					return None
			else:
				log.error(f'Lines Fixtures request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get Lines Fixtures: ', exc_info=True)


	def lines_odds(self, sportId, since=None, eventIds=None):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		if eventIds is None:
			events = ''
		else:
			# Сюда добавить список
			events = f'&eventIds=[{eventIds}]'
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			url = f'{self.URL}/v1/odds?sportId={sportId}&oddsFormat=Decimal&toCurrencyCode={balancedict["currency"]}{events}{since}'
			res = requests.get(url, headers=headers)
			if res.status_code == requests.codes.ok:
				if res and len(res.content) > 0:
					return res.json()
				else:
					return None
			else:
				log.error(f'Lines Parlay Odds request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.critical(f'Get Lines Parlay Odds: ', exc_info=True)


	def client_balance(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		try:
			res = requests.get(f'{self.URL}/v1/client/balance', headers=headers)
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Client balance request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get client balance: ', exc_info=True)


	def check_exists(self, predict, current):
		if current:
			for league in current['league']:
				for event in league['events']:
					if event['liveStatus'] != 1:
						for alexevent in predict:
							if not alexevent['isfound']:
								c_h = event['home']
								c_a = event['away']
								p_1 = alexevent['p1']
								p_2 = alexevent['p2']

								if (fuzz.token_sort_ratio(c_h, p_1) > 69 or fuzz.token_sort_ratio(c_a, p_1) > 69) and \
									(fuzz.token_sort_ratio(c_h, p_2) > 69 or fuzz.token_sort_ratio(c_a, p_2) > 69) and \
									('1.5 Sets' not in c_h and '2.5 Sets' not in c_h): # Убрать это позже и добавить возможность по сетам
									if fuzz.token_sort_ratio(c_h, p_1) < 70:
										alexevent['p1'] = c_h
										alexevent['p2'] = c_a
										alexevent['p1_odds'], alexevent['p2_odds'] = alexevent['p2_odds'], alexevent['p1_odds']
									alexevent['isfound'] = True
									alexevent['league'] = league['name']
									alexevent['league_id'] = league['id']
									alexevent['id'] = event['id']
									alexevent['starts'] = event['starts']
									log.debug(f'FOUND!\nID: {event["id"]}\nLeague: {league["name"]}\nPlayers: {event["home"]} - {event["away"]}\n{predict}')


	def check_odds(self, predict, odds):
		if odds:
			for league in odds['leagues']:
				for event in predict:
					if event['isfound'] and event['league_id'] == league['id']:
						for event_odds in league['events']:
							if event_odds['id'] == event['id']:
								for period in event_odds['periods']:
									if period['number'] == 0 and 'moneyline' in period.keys(): # ПРОВЕРИТЬ NUMBER == 0
										if 'home_found' not in event['odds'].keys():
											event['odds']['home_found'] = period['moneyline']['home']
											event['odds']['away_found'] = period['moneyline']['away']
											log.debug(f'Found odds: {event}')
										event['odds']['home'] = period['moneyline']['home']
										event['odds']['away'] = period['moneyline']['away']
										event['odds']['lineid'] = period['lineId']
										if period['moneyline']['home'] - event['odds']['home'] >= 0.01:
											event['odds']['value'] = True
											event['odds']['valueplayer'] = 'home'
											log.debug(f'Found value {event}')
										if period['moneyline']['away'] - event['odds']['away'] >= 0.01:
											event['odds']['value'] = True
											event['odds']['valueplayer'] = 'away'
											log.debug(f'Found value {event}')
										if 'spreads' in period.keys():
											hdp = period['spreads'][0]['hdp']
											if (hdp < 0 and hdp <= 2.0) or (hdp > 0 and hdp >= 2.0):
												event['hdp_dict'] = period['spreads'][0]
												log.debug(f'Found Handicap in:\n{event}')


	def placebet(self, bank, odds, lineid, eventid, bettype, team, altlineid=None):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		payload = {
			"oddsFormat": "DECIMAL",
			"acceptBetterLine": True,
			"stake": float(self.stakeamount(bank, odds)),
			"winRiskStake": "RISK",
			"lineId": lineid,
			"altLineId": altlineid,
			"fillType": "NORMAL",
			"sportId": TENNIS,
			"eventId": eventid,
			"periodNumber": 0,
			"betType": "MONEYLINE",
			"team": team
		}
		# ДОПИСАТЬ
		try:
			res = requests.post(f'{self.URL}/v2/bets/straight', headers=headers, data=json.dumps(payload))
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Lines Parlay Odds request: Code {res.status_code} / {res.json()}')
				return None
		except Exception:
			log.critical(f'Get Lines Parlay Odds: ', exc_info=True)


	def stakeamount(self, bank, odds):
		return round((bank * LOG(1 - (1 / (odds / (1 + 0.04))), 10 ** -40)), 1)


	def gethometeam(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		try:
			res = requests.get(f'{self.URL}/v2/leagues', headers=headers)
			if res.status_code == requests.codes.ok:
				r = res.json()
				d = {}
				for league in r['leagues']:
					d[league['id']] = league['homeTeamType']
				return d
			else:
				log.error(f'Get Leagues(hometeam): Code {res.status_code} / {res.json()}')
				return None
		except Exception:
			log.critical(f'Get leagues: ', exc_info=True)



if __name__ == '__main__':
	try:
		log.info('Started')
		alexline = []
		sheet = Sheets()
		pin = Pinnacle()
		TENNIS = 33
		balance = pin.client_balance()
		balancedict = {'bank': balance['availableBalance'], 'currency': balance['currency']}
		log.debug(pin.lines_fixtures(TENNIS))
		log.debug(pin.lines_odds(TENNIS))
		exit()
		last = last_odds = None
		currTime = checkTime = datetime.datetime.now()
		while True:
			log.debug('Getting values from Sheets...')
			sheet.getvalues()
			log.debug(f'Done. Values: {alexline}')
			deltaTime = currTime - checkTime
			if deltaTime.seconds > 61:
				last = last_odds = None
				checkTime = datetime.datetime.now()
			log.debug(f'Getting line since {last}...')
			line = pin.lines_fixtures(TENNIS, last)
			log.debug(f'Done.')
			currTime = datetime.datetime.now()

			if line:
				last = line['last']
				log.debug('Checking exists...')
				pin.check_exists(alexline, line)
				log.debug('Done.')
			log.debug(f'Getting odds since {last_odds}...')
			odds = pin.lines_odds(TENNIS, last_odds)
			log.debug(f'Done.')

			if odds:
				last_odds = odds['last']
				log.debug('Checking Odds...')
				pin.check_odds(alexline, odds)
				log.debug('Done.')
			log.debug('Sleep for 5 secs')
			sleep(5)


	except Exception:
		log.error(f'Main got: ', exc_info=True)
	finally:
		log.info('Closed')