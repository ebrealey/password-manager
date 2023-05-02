from support import *
import login, password_manager

class App:
	def __init__(self):
		self.user = init_user()
		cursor, connection = init_database()
		cursor.execute(f"SELECT oid FROM Users WHERE email = '{self.user}'")
		self.result = cursor.fetchall()
		connection.close()

	def save_config(self):
		file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w')
		json.dump(self.config, file)
		file.close()

	def run(self):
		if self.result:
			window = password_manager.PasswordManager(self.user)
			window.mainloop()

			with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r') as file:
				self.config = json.load(file)
			self.config['window_width'] = window.width
			self.config['window_height'] = window.height
			self.save_config()
		else:
			window = login.LoginWindow()
			window.mainloop()

if __name__ == '__main__':
	App().run()