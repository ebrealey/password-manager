import json, random, sqlite3, os
from email.mime.text import MIMEText
from smtplib import SMTP

# Password Manager directory
os_separator = os.path.sep
DIRECTORY = os_separator.join(os.path.dirname(__file__).split(os_separator)[0:-1]) + os_separator

# Constants
FONT = 'Century Gothic'
ACCENT = '#4B409E'
LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NUMBERS = '0123456789'
SPECIALCHARS = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
CHARACTERS = LOWERCASE + UPPERCASE + NUMBERS + SPECIALCHARS

# Colour scheme
BACKGROUND = '#1D2033'
FOREGROUND = '#fafafa'
BACKGROUND_DARK = '#0E1019'

# Create encryption key
def init_key():
	random.seed(61211095151110161915141119101)
	key = ''
	for _ in range(500):
		key += random.choice(CHARACTERS)
	return key
KEY = init_key()

# Encrypts and decrypts strings using a vernam cypher
def cypher(text: str) -> str:
	result = ''
	for i, char in enumerate(text):
		result += chr(ord(char) ^ ord(KEY[i]))
	return result

# Remember me + config
def init_user():
	try:
		file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r')
	except FileNotFoundError:
		file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w')
		config = {'data': None, 
			'window_width': 920, 
			'window_height': 600}
		json.dump(config, file)
		file.close()
		file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r')
		
	config = json.load(file)
	if config['data'] != None:
		user = cypher(config['data'])
		file.close()
		return user
	file.close()
	return False

# Connect to database, create if doesn't exist
def init_database() -> tuple[sqlite3.Cursor, sqlite3.Connection]:
	connection = sqlite3.connect(os.path.join(DIRECTORY, 'data', 'database.db'))
	cursor = connection.cursor()
	
	cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
						email TEXT PRIMARY KEY,
						profile_picture TEXT,
						username TEXT,
						password TEXT)""")
	cursor.execute("""CREATE TABLE IF NOT EXISTS Vault (
						master_email TEXT,
						type TEXT,
						display_image TEXT,
						name TEXT,
						identifier TEXT,
						encrypted_data TEXT,
						extra TEXT)""")
	return cursor, connection

# Import images from specified folder into dictionary
def import_images(path: str) -> dict:
	images = {}
	for _, _, img_files in os.walk(path):
		for filename in img_files:
			name = filename.split('.')[0] # Separate filetype from name
			images[name] = path + filename
	return images

# Send verification email to specified user
def send_email(sender, password, receiver, verify_code) -> bool:
    html_code = open(os.path.join(DIRECTORY, 'code', 'verification.html'), 'r')
    html = html_code.read().replace('VERIFYCODE', str(verify_code)) # Edit html to use a different code each time
    html_code.close()

    message = MIMEText(html, 'html')
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = 'Reset your password'

    try:
        server = SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        return True
    except:
        return False
