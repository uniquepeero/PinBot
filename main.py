import requests
import json
import configparser
import logging
import os
import gspread
import datetime
from time import sleep
#from pprint import pformat
#from fuzzywuzzy import fuzz
from math import log as LOG
from oauth2client.service_account import ServiceAccountCredentials


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", 'w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

CHAT = ''
BOTKEY = ''

class Sheets:
	def __init__(self):
		try:
			log.info('Connecting to Google Sheets...')
			self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			self.creds = ServiceAccountCredentials.from_json_keyfile_name('secret.json', self.scope)
			self.client = gspread.authorize(self.creds)
			self.sheet = self.client.open('Pinn Line').sheet1
			log.info('Successfuly connected to Google Sheet')
		except:
			log.error('GSheets connect error: ', exc_info=True)

	def getvalues(self):
		if self.creds.access_token_expired: self.client.login()
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
							if '1' in item[2]: moneyline = 'home'
							elif '2' in item[2]: moneyline = 'away'
							else: moneyline = None
							good_odds = item[3]
							if ',' in good_odds: good_odds.replace(',', '.')

							alexline.append({
								'event': f'{item[0]} - {item[1]}',
								'p1': item[0],
								'p2': item[1],
								'moneyline': moneyline,
								'good_odds': float(good_odds),
								'isfound': False,
								'sended': False,
								'index': index + 2
							})
							log.debug(f'Got new event row: "{item[0]} - {item[1]}"')
			
			elif len(allvalues) < 1:
				log.warning('Got fully empty sheet')


	def deleterow(self, index):
		return self.sheet.delete_row(index)

class Pinnacle:
	AUTH = ''
	URL = 'https://api.pinnacle.com'
	proxydict = {}
	def __init__(self):
		config = configparser.ConfigParser()
		if os.path.isfile('config.ini'):
			config.read('config.ini')
			try:
				global CHAT, BOTKEY
				self.AUTH = config['Pinnacle']['KEY']
				CHAT = config['TG']['chat']
				BOTKEY = config['TG']['API']
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
			events = f'&eventIds=[{eventIds}]'
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			url = f'{self.URL}/v1/odds?sportId={sportId}&oddsFormat=Decimal{events}{since}'
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
							if not alexevent['isfound'] and 'starts' in event.keys() and event['home'] == alexevent['p1'] and\
									event['away'] == alexevent['p2']:
								starts = event['starts']
								alexevent['isfound'] = True
								alexevent['league'] = league['name']
								alexevent['league_id'] = league['id']
								alexevent['id'] = event['id']
								alexevent['starts'] = datetime.datetime.strptime(event['starts'], '%Y-%m-%dT%H:%M:%SZ')
								log.debug(f'FOUND!\nID: {event["id"]}\nLeague: {league["name"]}\nPlayers: {event["home"]} - {event["away"]}\n{predict}\nStarts: {alexevent["starts"]}')


	def check_odds(self, predict, odds):
		msg = """"""
		if odds:
			for league in odds['leagues']:
				for event in predict:
					if event['isfound'] and event['league_id'] == league['id']:
						for event_odds in league['events']:
							if event_odds['id'] == event['id']:
								for period in event_odds['periods']:
									if period['number'] == 0:
										event['lineid'] = period['lineId']

										if event['moneyline'] and 'moneyline' in period.keys() \
												and period['moneyline'][event['moneyline']] >= event['good_odds']:

											event['home'] = period['moneyline']['home']
											event['away'] = period['moneyline']['away']

											if event['moneyline'] == 'home':
												two_players = f"{event['p1']} ({event['good_odds']}) - {event['p2']}"
											else: two_players = f"{event['p1']} - {event['p2']} ({event['good_odds']})"

											msg += f"{event['league']}\n{two_players}\n{event['home']} @ {event['away']}\n\n"
											event['sended'] = True
											log.debug(f'Trying to delete event row: {event}')
											sheet.deleterow(event['index'])
											log.debug(f'event sended set to True and deleted: {event}')
		if len(msg) > 0: send_tg(msg)
		for event in predict:
			log.debug(f'Time now: {datetime.datetime.utcnow()} / {event["starts"]}')
			if event['sended'] or datetime.datetime.utcnow() > event['starts']:
				del event
				log.debug('Event deleted')
										

	def placebet(self, bank, odds, leagueid, lineid, eventid, bettype, team, altlineid=None, side=None):
		teams = {
			'home': 'Team1',
			'away': 'Team2',
			'empty': None
		}
		if team is not None:
			try:
				if self.gethometeam()[leagueid] != 'Team1': teams['home'], teams['away'] = teams['away'], teams['home']
			except Exception:
				log.error('Get home team value in placebet(): ', exc_info=True)
		else: team = 'empty'

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
			"betType": bettype,
			"team": teams[team],
			"side": side
		}
		log.debug(f'{payload}')
		try:
			res = requests.post(f'{self.URL}/v2/bets/straight', headers=headers, data=json.dumps(payload))
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Bet request: Code {res.status_code} / {res.json()}')
				return None
		except Exception:
			log.critical(f'Bet Odds: ', exc_info=True)


	def stakeamount(self, bank, odds):
		return round((bank * LOG(1 - (1 / (odds / (1 + 0.04))), 10 ** -40)), 1)


	def gethometeam(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		try:
			res = requests.get(f'{self.URL}/v2/leagues?sportId={TENNIS}', headers=headers)
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

def send_tg(msg):
	url = f'https://api.telegram.org/bot{BOTKEY}/sendMessage?chat_id={CHAT}&text={msg}'
	try:
		response = requests.get(url)
		if response.status_code == requests.codes.ok:
			log.debug('Message sended successfully')
		else:
			log.error(f'Message got: {response.status_code}')
	except requests.exceptions.RequestException as e:
		log.error(f'Sending: {e}')
	except ValueError as e:
		log.error(f'Sending: {response.text}')

if __name__ == '__main__':
	try:
		log.info('Started')
		alexline = []
		sheet = Sheets()
		pin = Pinnacle()
		TENNIS = 33
		#last = last_odds = None
		#currTime = checkTime = balancetimecheck = datetime.datetime.now()
		while True:
			# Присваивание банка на день в 6:00 UTC
			#if currTime >= balancetimecheck:
			#	balancetimecheck.replace(hour=6, minute=00)
			#	balancetimecheck += datetime.timedelta(days=1)
			#	balance = pin.client_balance()
			#	balancedict = {'bank': balance['availableBalance'], 'currency': balance['currency']}

			log.debug('Getting values from Sheets...')
			sheet.getvalues()
			log.debug(f'Done. Values: {alexline}')
			#deltaTime = currTime - checkTime
			#if deltaTime.seconds > 61:
			#	last = last_odds = None
			#	checkTime = datetime.datetime.now()
			log.debug(f'Getting line...')
			line = pin.lines_fixtures(TENNIS, None)
			#log.debug(f'Done. Fixtures:\n{line}')
			#currTime = datetime.datetime.now()

			if line:
				#last = line['last']
				log.debug('Checking exists...')
				pin.check_exists(alexline, line)
				log.debug('Done.')
			log.debug(f'Getting odds...')
			odds = pin.lines_odds(TENNIS, None)
			#log.debug(f'Done. Odds:\n{odds}')

			if odds:
				#last_odds = odds['last']
				log.debug('Checking Odds...')
				pin.check_odds(alexline, odds)
				log.debug('Done.')
			log.debug('Sleep for one minute')
			sleep(60)


	except Exception:
		log.error(f'Main got: ', exc_info=True)
	finally:
		log.info('Closed')

# TODO переписать except
#TODO Просмотреть и сверить отчет odds. Какие там period number, везде ли 0.
#TODO Присваивать кэфы для нужных событий (if event['moneyline'] and 'moneyline' in period.keys() and ВОЗМОЖНО not  event['bet']['moneyline']
# Нашли все кэфы - вызываем функцию проставления. В ней дописать сохранение размера ставки
# Если есть parentid - сохранять его (Fixtures). Если есть altline в нужных hdp/points в ответе с odds - сохранять их