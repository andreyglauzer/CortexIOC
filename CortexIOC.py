import datetime
import requests
import json
import pprint
import time
import sqlite3
import logging
import yaml
import os
import iocextract
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DataBase:
	def __init__(self,database_path=None,
		database_name=None):
		self.logger = logging.getLogger('DataBase')
		self.database_path = database_path
		self.database_name = database_name
		if not os.path.exists('{path}/{filename}'.format(path=self.database_path, filename=self.database_name)):
			conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
			cursor = conn.cursor()
			cursor.execute('CREATE TABLE IF NOT EXISTS IOCs ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,'
					 'file_name TEXT, IOC TEXT, type TEXT, signature TEXT, tags TEXT, font TEXT, EDL BLOB, date TEXT);')
			conn.commit()
			conn.close()
		else:
			conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
			cursor = conn.cursor()
			cursor.execute('CREATE TABLE IF NOT EXISTS IOCs ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,'
					 'file_name TEXT, IOC TEXT, signature TEXT, tags TEXT, font TEXT, date TEXT);')
			conn.commit()
			conn.close()

	def compare_ioc(self,IOC=None):
		self.logger.debug('Checking if the IOC has already been registered.')
		conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
		cursor = conn.cursor()
		r = cursor.execute("SELECT * FROM IOCs WHERE IOC='{0}';".format(IOC))
		return r.fetchall()

	def save_ioc(self,
		file_name=None,
		IOC=None,
		signature=None,
		tags=None,
		font=None,
		type=None):
		self.logger.debug('Saving IOC in the database.')
		conn = sqlite3.connect('{path}/{filename}'.format(path=self.database_path, filename=self.database_name))
		cursor = conn.cursor()
		cursor.execute("""
		INSERT INTO IOCs (file_name,IOC,type,signature,tags,font,date)
		VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')
		""" % (file_name,IOC,type,signature,tags,font,datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")))
		conn.commit()
		conn.close()


class MalwareBaazar:
	def __init__(self,):
		self.baseurl = 'https://mb-api.abuse.ch/api/v1/'
		self.logger = logging.getLogger('Baazar')

	@property
	def start(self):
		self.logger.info('Obtaining IOC from Baazar')
		request = requests.post(self.baseurl,
			headers={'User-Agent': 'Mozilla/5.0'},
			data={'query':'get_recent', 'selector':'100'}).json()
		return request['data']

class CortexXDR:
	def __init__(self,
		hash=None,
		domain=None,
		ip=None,
		extract_all=None,
		extract_url=None,
		extract_file=None,
		feed=None,
		debug=None,
		baseurl=None,
		user=None,
		passwd=None,
		database_path=None,
		database_name=None,
		webdriver_path=None,
		headless=None):

		self.hash= hash
		self.domain= domain
		self.ip= ip
		self.extract_all = extract_all
		self.extract_url = extract_url
		self.extract_file = extract_file
		self.feed = feed
		self.baseurl = baseurl
		self.user = user
		self.passwd = passwd
		self.debug = debug
		self.database = DataBase(database_path=database_path,
			database_name=database_name)

		if headless:
			chrome_options = Options()
			chrome_options.add_argument("--headless")
			chrome_options.add_argument('log-level=3')
			self.driver = webdriver.Chrome(webdriver_path, chrome_options=chrome_options)
		else:
			self.driver = webdriver.Chrome(webdriver_path)

		if self.debug:
			logging.basicConfig(
					level=logging.DEBUG,
					format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S')
		else:
			logging.basicConfig(
					level=logging.INFO,
					format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S')

		self.logger = logging.getLogger("Send IOC's to Cortex XDR")

	def logging(self):
		self.logger.info('Logging in to cortex.')
		self.driver.get(self.baseurl)
		wait = WebDriverWait(self.driver,15)
		wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="email"]'))).send_keys(self.user)
		wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="next"]'))).click()
		wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]'))).send_keys(self.passwd)
		wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="password-form"]/button'))).click()

	def uploadIOC(self, IOC=None, comment=None,count=None,name=None):
		self.logger.info(f'Sending IOC from {name} to cortex.')
		if count <= 0:
			time.sleep(60)
		else:
			time.sleep(10)

		wait = WebDriverWait(self.driver,15)
		wait.until(EC.visibility_of_element_located((By.XPATH,
			'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button'))).click()
		wait.until(EC.visibility_of_element_located((By.XPATH,
			'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button/div/div/create-ioc-form/div/div/div[1]/div[1]/secdo-text/secdo-generic/div/input'))).send_keys(
			IOC)
		wait.until(EC.visibility_of_element_located((By.XPATH,
			'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button/div/div/create-ioc-form/div/div/div[1]/div[3]/secdo-ddl/div/secdo-generic/p-dropdown/div/label'))).click()
		wait.until(EC.visibility_of_element_located((By.XPATH,
			'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button/div/div/create-ioc-form/div/div/div[1]/div[3]/secdo-ddl/div/secdo-generic/p-dropdown/div/div[4]/div/ul/li[4]'))).click()
		wait.until(EC.visibility_of_element_located((By.XPATH,
			'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button/div/div/create-ioc-form/div/div/div[1]/secdo-text/secdo-generic/div/input'))).send_keys(
			comment)
		try:
			wait.until(EC.visibility_of_element_located((By.XPATH,
				'/html/body/xdr-app/secdo-ng/div/div/secdo-ng-rules-ioc/div/div/secdo-grid/div/grid-header/div/div[1]/span[2]/div[2]/popup-button/div/div/create-ioc-form/div/div/div[2]/div/secdo-button[2]/span/button'
				))).click()
		except:
			self.driver.get(self.baseurl)
			self.logger.error('The hash could not be sent an error occurred.')

	@property
	def start(self):
		self.logging()

		# Extraction
		if self.extract_all is not None \
			or self.ip is not None \
			or self.hash is not None \
			or self.domain is not None \
			or self.extract_file is not None:
			self.logger.info('Checking the type of extraction will be performed.')

			if self.extract_file is not None:
				self.logger.info(f'Obtaining IOC from file: {self.extract_file}')
				if os.path.exists(self.extract_file):
					openfile = open(self.extract_file,'r+')
					all_text = openfile.read()
					title = self.extract_file
					file_name = self.extract_file
				else:
					self.logger.error('The given directory or file was not found.')
			elif self.extract_url is not None:
				self.logger.info(f'Obtaining IOC from WebSite: {self.extract_url}')
				self.driver.get(self.extract_url)
				soup = BeautifulSoup(self.driver.page_source, "html.parser")
				title = soup.find('title').get_text()
				all_text = self.select_all_text(soup=soup)
				file_name = self.extract_url

			if self.extract_all:
				self.driver.get(self.baseurl)
				count = 0
				for extract_iocs in iocextract.extract_iocs(all_text):
					if '/' not in extract_iocs \
						and '[at]' not in extract_iocs:
						if len(self.database.compare_ioc(IOC=extract_iocs.replace('[.]','.'))) == 0:
							self.database.save_ioc(IOC=extract_iocs.replace('[.]','.'),
							  signature=title,
							  tags="Extract from URL",
							  font="Extract",
							  type="IOCS",
							  file_name=file_name)

							self.uploadIOC(comment=f'IOC extraction: {title}',
							  IOC=extract_iocs.replace('[.]','.'),
							  count=count,
							  name=extract_iocs.replace('[.]','.'))
							count += 1
						else:
							self.logger.debug(f'IOC already registered: {extract_iocs}')
			elif self.domain:
				self.driver.get(self.baseurl)
				count = 0
				for extract_urls in iocextract.extract_urls(all_text):
					if '/' not in extract_urls \
						and '[at]' not in extract_urls:
						if len(self.database.compare_ioc(IOC=extract_urls.replace('[.]','.'))) == 0:
							self.database.save_ioc(IOC=extract_urls.replace('[.]','.'),
							  signature=title,
							  tags="Extract from URL",
							  font="Extract",
							  type="Domain",
							  file_name=file_name)

							self.uploadIOC(comment=f'IOC extraction: {title}',
							  IOC=extract_urls.replace('[.]','.'),
							  count=count,
							  name=extract_urls.replace('[.]','.'))
							count += 1
						else:
							self.logger.debug(f'IOC already registered: {extract_urls}')
			elif self.ip:
				self.driver.get(self.baseurl)
				count = 0
				for extract_ipv4s in iocextract.extract_ipv4s(all_text):
					if '/' not in extract_ipv4s \
						and '[at]' not in extract_ipv4s:
						if len(self.database.compare_ioc(IOC=extract_ipv4s.replace('[.]','.'))) == 0:
							self.database.save_ioc(IOC=extract_ipv4s.replace('[.]','.'),
							  signature=title,
							  tags="Extract from URL",
							  font="Extract",
							  type="ipv4",
							  file_name=file_name)

							self.uploadIOC(comment=f'IOC extraction: {title}',
							  IOC=extract_ipv4s.replace('[.]','.'),
							  count=count,
							  name=extract_ipv4s.replace('[.]','.'))
							count += 1
						else:
							self.logger.debug(f'IOC already registered: {extract_ipv4s}')
			elif self.hash:
				self.logger.info('Getting only the Hashes from the site.')
				self.driver.get(self.baseurl)
				count = 0
				for extract_hashes in iocextract.extract_hashes(all_text):
					if '/' not in extract_hashes \
						and '[at]' not in extract_hashes:
						if len(self.database.compare_ioc(IOC=extract_hashes.replace('[.]','.'))) == 0:
							self.database.save_ioc(IOC=extract_hashes.replace('[.]','.'),
							  signature=title,
							  tags="Extract from URL",
							  font="Extract",
							  type="Hash",
							  file_name=file_name)

							self.uploadIOC(comment=f'IOC extraction: {title}',
							  IOC=extract_hashes.replace('[.]','.'),
							  count=count,
							  name=extract_hashes.replace('[.]','.'))
							count += 1
						else:
							self.logger.debug(f'IOC already registered: {extract_hashes}')

		if self.feed is not None:
			# MalwareBaazar
			count = 0
			for iocs in MalwareBaazar().start:
				if len(self.database.compare_ioc(IOC=iocs['sha256_hash'])) == 0:
					comment = "Name: {name}, signature: {signature}, tags: {tags}, font: {font}".format(
						name=iocs['file_name'],
						signature=iocs['signature'],
						tags=iocs['tags'],
						font='Bazaar')

					self.database.save_ioc(file_name=iocs['file_name'],
						IOC=iocs['sha256_hash'],
						signature=iocs['signature'],
						tags=str(iocs['tags']).replace("'",'') \
							.replace('[','') \
							.replace(']',''),
						font='Bazaar',
						type="Hash")

					self.uploadIOC(comment=comment,
						IOC=iocs['sha256_hash'],
						count=count,
						name=iocs['file_name'])
					count += 1
				else:
					self.logger.debug(f"IOC already registered: {iocs['sha256_hash']}")

			# Circl
			for feed in MISPFeed(url="https://www.circl.lu/doc/misp/feed-osint/").start:
				request = requests.get(feed,
				  headers={'User-Agent': 'Mozilla/5.0'}).json()

				count = 0
				for iocs in request['Event']['Attribute']:
					if iocs['category'] == 'Payload delivery':
						if '.' not in iocs['value'] \
							and len(iocs['value']) == 32 \
							or len(iocs['value']) == 64:

							if len(self.database.compare_ioc(IOC=iocs['value'])) == 0:
								comment = "Name: {name}, signature: {signature}, tags: {tags}, font: {font}".format(
							  		name=iocs['comment'].split(' ')[0],
							  		signature=iocs['category'],
							  		tags=iocs['category'],
							  		font="Circl")

								self.database.save_ioc(file_name=iocs['comment'].split(' ')[0],
								  IOC=iocs['value'],
								  signature=iocs['category'],
								  tags=iocs['category'],
								  font="Circl",
								  type="Hash")

								self.uploadIOC(comment=comment,
								  IOC=iocs['value'],
								  count=count,
								  name=iocs['comment'].split(' ')[0])
								count += 1
							else:
								self.logger.debug(f"IOC already registered: {iocs['value']}")

					elif iocs['category'] == 'External analysis':
						if 'virustotal' in iocs['value']:
							hash = iocs['value'].split('/')[4]
							if len(self.database.compare_ioc(IOC=hash)) == 0:
								comment = "Name: {name}, signature: {signature}, tags: {tags}, font: {font}".format(
							  		name=iocs['comment'].split(' ')[0],
							  		signature=iocs['category'],
							  		tags=iocs['category'],
							  		font="Circl")

								self.database.save_ioc(file_name=iocs['comment'].split(' ')[0],
								  IOC=hash,
								  signature=iocs['category'],
								  tags=iocs['category'],
								  font="Circl",
								  type="Hash")

								self.uploadIOC(comment=comment,
								  IOC=iocs['value'],
								  count=count,
								  name=iocs['comment'].split(' ')[0])
								count += 1
							else:
								self.logger.debug(f"IOC already registered: {iocs['value']}")

					elif iocs['category'] == 'Artifacts dropped':
						hash = iocs['value']
						if len(self.database.compare_ioc(IOC=hash)) == 0:
							comment = "Name: {name}, signature: {signature}, tags: {tags}, font: {font}".format(
								name=iocs['comment'].split(' ')[0],
								signature=iocs['category'],
								tags=iocs['category'],
								font="Circl")

							self.database.save_ioc(file_name=iocs['comment'].split(' ')[0],
							  IOC=hash,
							  signature=iocs['category'],
							  tags=iocs['category'],
							  font="Circl",
							  type="Hash")

							self.uploadIOC(comment=comment,
							  IOC=iocs['value'],
							  count=count,
							  name=iocs['comment'].split(' ')[0])
							count += 1
						else:
							self.logger.debug(f'IOC already registered: {hash}')

	def select_all_text(self, soup=None):
		for s in soup(['script', 'style']):
			s.decompose()

		return '\n'.join(soup.stripped_strings)


class MISPFeed:
	def __init__(self, url=None):
		self.baseurl = url
		self.logger = logging.getLogger('MISP Feed')

	def table(self,soup=None,baseurl=None):
		if soup is not None:
			data = []
			table = soup.find('table')
			rows = table.find_all('tr')
			for row in rows:
				for urls in row.find_all('a'):
					if '.json' in str(urls['href']):
						data.append(baseurl+urls['href'])

			return data

	@property
	def start(self):
		self.logger.info('Obtaining IOC from the MISP Feed')
		request = requests.get(self.baseurl,
			headers={'User-Agent': 'Mozilla/5.0'})
		return self.table(soup=BeautifulSoup(request.content, "html.parser"),baseurl=self.baseurl)


class ArgsIOC:
	def __init__(self):
		parser = argparse.ArgumentParser()
		parser.add_argument('-c', '--config', help='The directory of the settings file, in Yaml format.',
						   action='store', dest = 'config')
		parser.add_argument('-e', '--extraction', help='Extraction of IOCs from websites and reports',
						   action='store_true', dest = 'extraction')
		parser.add_argument('--url', help='URL you want to do IOC extraction',
						   action='store', dest = 'url')
		parser.add_argument('--file', help='Directory and file that has IOCs',
						   action='store', dest = 'extract_file')
		parser.add_argument('--hash', help='States that you just want to collect hash',
						   action='store_true', dest = 'hash')
		parser.add_argument('--domain', help='States that you just want to collect domain',
						   action='store_true', dest = 'domain')
		parser.add_argument('--ip', help='States that you just want to collect IP',
						   action='store_true', dest = 'ip')
		parser.add_argument('--all', help='Claims that you collect everything IP/Hash/Domain.\nThis should be used for extracting websites and files.',
						   action='store_true', dest = 'extract_all')
		parser.add_argument('--feed', help='This states that you want to get feed IOCs that I provided in the script myself, like MIPS / MalwareBaazar',
						   action='store_true', dest = 'feed')
		args = parser.parse_args()

		self.config = args.config
		self.extraction = args.extraction
		self.extract_url = args.url
		self.hash = args.hash
		self.domain = args.domain
		self.ip = args.ip
		self.extract_all = args.extract_all
		self.extract_file = args.extract_file
		self.feed = args.feed


		if os.path.exists(args.config):
			if '.yml' in args.config:
				with open(args.config, 'r') as stream:
					data = yaml.load(stream, Loader=yaml.FullLoader)
					self.debug = data.get('debug', '')
					self.baseurl = data.get('baseurl', '')
					self.user = data.get('user', '')
					self.passwd = data.get('passwd', '')
					self.database_path = data.get('database_path', '')
					self.database_name = data.get('database_name', '')
					self.webdriver_path = data.get('webdriver_path', '')
					self.headless = data.get('headless', '')

					if self.debug:
						logging.basicConfig(
								level=logging.DEBUG,
								format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
								datefmt='%Y-%m-%d %H:%M:%S',
							)
					else:
						logging.basicConfig(
								level=logging.INFO,
								format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
								datefmt='%Y-%m-%d %H:%M:%S',
							)

					self.logger = logging.getLogger('Start send IOCs')
			else:
				self.logger.error(f'File does not exist or path is incorrect: {args.config}.\n')
				sys.exit(1)
		else:
			self.logger.error(f'File does not exist or path is incorrect: {args.config}\n')
			sys.exit(1)


	@property
	def start(self):

		banner ="""

 ██████╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗██╗ ██████╗  ██████╗
██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝██║██╔═══██╗██╔════╝
██║     ██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ ██║██║   ██║██║
██║     ██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ ██║██║   ██║██║
╚██████╗╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗██║╚██████╔╝╚██████╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═════╝

INFO: Script to send IOCs to the PaloAlto Cortex XDR

		"""
		print(banner)
		CortexXDR(hash=self.hash,
			domain=self.domain,
			ip=self.ip,
			extract_all=self.extract_all,
			extract_url=self.extract_url,
			extract_file=self.extract_file,
			feed=self.feed,
			debug=self.debug,
			baseurl=self.baseurl,
			user=self.user,
			passwd=self.passwd,
			database_path=self.database_path,
			database_name=self.database_name,
			webdriver_path=self.webdriver_path,
			headless=self.headless).start

ArgsIOC().start
