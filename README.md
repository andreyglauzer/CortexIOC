# CortexIOC

### Description
This script aims to automate the sending of IOC to Cortex XDR. IOCs are obtained from feeds like `MalwareBaazar` and `MISP`. It is also possible to obtain `website` IOCs and `text files`.

### Use
The use of the script is simple and does not have many functions.
#### Feed
To obtain Feed IOCs, just run the command below:

```
.\CortexIOC.py --feed --config .\tools\config.yml
```
#### TextFile
To obtain text file IOCs just execute the command below, it is necessary to inform what you are trying to obtain as IP / Domain / Hash, if you want all of them, inform `--all`

```
.\send_ioc.py -e --file C:\Temp\ioc.txt --ip --config .\tools\config.yml
```

#### Website
To obtain file IOCs for a website, just execute the command below, it is necessary to inform what you are trying to obtain as IP / Domain / Hash, if you want everyone to inform `--all`

```
python .\send_ioc.py -e -u "https://www.cybereason.com/blog/brazilian-financial-malware-banking-europe-south-america" --all
```
### Configuration
To use the script it is necessary to provide the following information in the `.yml` file

```
baseurl: 'https://fqdn.paloaltonetworks.com/rules/ioc'
user: user
passwd: passwd
database_path: 'tools/'
database_name: 'iocs.db'
webdriver_path: 'tools/driver/chromedriver.exe'
debug: False
headless: True

```

### Help

```
.\send_ioc.py -h
usage: send_ioc.py [-h] [-c CONFIG] [-e] [--url URL] [--file EXTRACT_FILE] [--hash] [--domain] [--ip] [--all] [--feed]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        The directory of the settings file, in Yaml format.
  -e, --extraction      Extraction of IOCs from websites and reports
  --url URL             URL you want to do IOC extraction
  --file EXTRACT_FILE   Directory and file that has IOCs
  --hash                States that you just want to collect hash
  --domain              States that you just want to collect domain
  --ip                  States that you just want to collect IP
  --all                 Claims that you collect everything IP/Hash/Domain. This should be used for extracting websites and files.
  --feed                This states that you want to get feed IOCs that I provided in the script myself, like MIPS / MalwareBaazar
```
