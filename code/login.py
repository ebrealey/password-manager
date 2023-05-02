import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from email_validator import validate_email, EmailNotValidError
import bcrypt, json, secrets, os

from support import *
import password_manager

class LoginWindow(tk.Tk):
	def __init__(self):
		super().__init__()

		# General
		self.title('FjordPass - Login')
		self.iconbitmap(os.path.join(DIRECTORY, 'icon.ico'))
		self.geometry(f'400x500+{int(self.winfo_screenwidth()/2-200)}+{int(self.winfo_screenheight()/2-300)}')
		self.resizable(False, False)

		self.remember_me = False
		self.cursor, self.connection = init_database()

		# Load images
		self.images = import_images(os.path.join(DIRECTORY, 'images', ''))
		for key, value in self.images.items():
			self.images[key] = ImageTk.PhotoImage(Image.open(value))
		
		self.container = tk.Frame(self, bg=BACKGROUND)
		self.container.pack(expand=True, fill='both')

		self.change_page('login')

	def login_page(self):
		page_title = tk.Label(self.container, text='LOGIN TO YOUR ACCOUNT', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, columnspan=2, row=1, padx=60)
		logo = tk.Label(self.container, image=self.images['blurred_logo'], bg=BACKGROUND)
		logo.grid(column=0, columnspan=2, row=0, pady=8)

		self.input_fields(False) # Create entry boxes excluding username box

		def toggle_off(value):
			self.remember_me = False
			checkbox['image'] = self.images['unchecked']
			checkbox['command'] = lambda:toggle_on(value)

		def toggle_on(value):
			self.remember_me = True
			checkbox['image'] = self.images['checked']
			checkbox['command'] = lambda:toggle_off(value)

		checkbox = tk.Button(self.container, image=self.images['unchecked'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, padx=5, command=lambda:toggle_on(0))
		checkbox.grid(column=0, row=8, sticky='w', padx=30, pady=20)
		
		signin = tk.Button(self.container, image=self.images['login'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:self.login(self.email_input.get().lower(), self.pass_input.get()))
		signin.grid(column=0, columnspan=2, row=9)
		
		signup = tk.Button(self.container, text='Create new account.', cursor='hand2', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('register'))
		signup.grid(column=0, row=10, sticky='w', padx=30, pady=15)

		forgot_password = tk.Button(self.container, text='Forgot password?', cursor='hand2', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('forgot_password'))
		forgot_password.grid(column=1, row=10, sticky='e', padx=30, pady=15)

	def register_page(self):
		page_title = tk.Label(self.container, text='REGISTER AN ACCOUNT', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, columnspan=2, row=1, padx=(77, 78), pady=(45, 0))

		self.input_fields(True) # Create entry boxes including username box

		signup = tk.Button(self.container, image=self.images['register'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:self.register(self.email_input.get().lower(), self.user_input.get(), self.pass_input.get()))
		signup.grid(column=0, columnspan=2, row=8, pady=(20, 0))

		signin = tk.Button(self.container, text='Login to an existing account.', cursor='hand2', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('login'))
		signin.grid(column=0, columnspan=2, row=9, sticky='w', padx=30, pady=15)

	def input_fields(self, with_username):
		# Email widgets
		tk.Label(self.container, text='EMAIL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=2, sticky='w', padx=(30, 0), pady=(15,5))
		email_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		email_frame.grid(column=0, columnspan=2, row=3, sticky='we', padx=20)
		self.email_input = tk.Entry(email_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.email_input.pack(fill='both')

		if with_username: # Username widgets
			tk.Label(self.container, text='USERNAME', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=4, sticky='w', padx=30, pady=5)
			user_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
			user_frame.grid(column=0, columnspan=2, row=5, sticky='we', padx=20)
			self.user_input = tk.Entry(user_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
			self.user_input.pack(expand=True, fill='both', side='left')

		# Password widgets
		tk.Label(self.container, text='PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=6, sticky='w', padx=30, pady=5)
		pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		pass_frame.grid(column=0, columnspan=2, row=7, sticky='we', padx=20)
		self.pass_input = tk.Entry(pass_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), show='•', insertbackground=FOREGROUND, bd=0)
		self.pass_input.pack(expand=True, fill='both', side='left')

		# Display whether data is valid or not
		self.function_outputs = tk.Label(self.container, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_outputs.grid(column=0, columnspan=2, row=2, sticky='e', padx=(0, 30), pady=(15,5))

		def show_password():
			self.pass_input['show'] = ''
			toggle_password['image'] = self.images['visible']
			toggle_password['command'] = hide_password

		def hide_password():
			self.pass_input['show'] = '•'
			toggle_password['image'] = self.images['invisible']
			toggle_password['command'] = show_password

		toggle_password = tk.Button(pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_password)
		toggle_password.pack(padx=5, side='right')

	def forgot_password_page(self):
		self.container.grid_columnconfigure(0, weight=1)
		self.container.grid_rowconfigure(6, weight=1)
		
		logo = tk.Label(self.container, image=self.images['blurred_logo'], bg=BACKGROUND)
		logo.grid(column=0, row=0, pady=30)
		page_title = tk.Label(self.container, text='FORGOT PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, row=1)
		description = tk.Label(self.container, text='A code will be sent to your email', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10))
		description.grid(column=0, row=2, pady=(10, 20))

		tk.Label(self.container, text='EMAIL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=3, sticky='w', padx=30, pady=5)
		email_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		email_frame.grid(column=0, row=4, padx=20, sticky='we')
		self.email_input = tk.Entry(email_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.email_input.pack(fill='both')
		self.function_output = tk.Label(self.container, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=3, sticky='e', padx=(0, 30), pady=5)

		send_code = tk.Button(self.container, image=self.images['send_code'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:self.send_code_to_user(self.email_input.get().lower()))
		send_code.grid(column=0, row=5, padx=20, pady=30)
		back_button = tk.Button(self.container, text='Go back', bg=BACKGROUND, activebackground=BACKGROUND, fg=FOREGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('login'))
		back_button.grid(column=0, row=6, padx=30, pady=(0, 24), sticky='sw')

	def enter_code_page(self, email, verify_code):
		self.container.grid_columnconfigure(0, weight=1)
		self.container.grid_columnconfigure(1, weight=1)
		self.container.grid_rowconfigure(6, weight=1)
		
		logo = tk.Label(self.container, image=self.images['blurred_logo'], bg=BACKGROUND)
		logo.grid(column=0, columnspan=2, row=0, pady=30)
		page_title = tk.Label(self.container, text='ENTER CODE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, columnspan=2, row=1, pady=(0, 10))

		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', lambda *args:self.update_check.set(self.code_input.get()[:8])) # Updates every time input changes

		code_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		code_frame.grid(column=0, columnspan=2, row=3, padx=70, sticky='we')
		self.code_input = tk.Entry(code_frame, textvariable=self.update_check, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 18), insertbackground=FOREGROUND, bd=0)
		self.code_input.pack(fill='both')
		self.function_output = tk.Label(self.container, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, columnspan=2, row=2, sticky='w', pady=5, padx=(75, 0))

		enter_code = tk.Button(self.container, image=self.images['enter'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:self.check_verify_code(email, verify_code, self.code_input.get().upper()))
		enter_code.grid(column=0, columnspan=2, row=4, padx=20, pady=25)

		retry_label = tk.Label(self.container, text="Didn't receive an email?", bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10))
		retry_label.grid(column=0, row=5, pady=5, padx=5, sticky='e')
		retry_button = tk.Button(self.container, text="Retry", bg=BACKGROUND, activebackground=BACKGROUND, fg=ACCENT, activeforeground=ACCENT, bd=0, font=(FONT, 10), command=lambda:self.send_code_to_user(email))
		retry_button.grid(column=1, row=5, pady=5, padx=5, sticky='w')
		
		back_button = tk.Button(self.container, text='Go back', bg=BACKGROUND, activebackground=BACKGROUND, fg=FOREGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('login'))
		back_button.grid(column=0, row=6, padx=30, pady=(0, 24), sticky='sw')

	def reset_password_page(self, email):
		self.container.grid_columnconfigure(0, weight=1)
		self.container.grid_rowconfigure(7, weight=1)
		
		logo = tk.Label(self.container, image=self.images['blurred_logo'], bg=BACKGROUND)
		logo.grid(column=0, row=0, pady=(30, 15))
		page_title = tk.Label(self.container, text='RESET PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, row=1)

		tk.Label(self.container, text='PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=2, sticky='w', padx=30, pady=5)
		pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		pass_frame.grid(column=0, row=3, padx=20, sticky='we')
		self.pass_input = tk.Entry(pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.pass_input.pack(fill='both', side='left', expand=True)
		
		def show_password():
			self.pass_input['show'] = ''
			toggle_password['image'] = self.images['visible']
			toggle_password['command'] = hide_password

		def hide_password():
			self.pass_input['show'] = '•'
			toggle_password['image'] = self.images['invisible']
			toggle_password['command'] = show_password

		toggle_password = tk.Button(pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_password)
		toggle_password.pack(padx=5, side='right')

		tk.Label(self.container, text='CONFIRM PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=4, sticky='w', padx=30, pady=5)
		confirm_pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		confirm_pass_frame.grid(column=0, row=5, padx=20, sticky='we')
		self.confirm_pass_input = tk.Entry(confirm_pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.confirm_pass_input.pack(fill='both', side='left', expand=True)
		
		def show_confirm_password():
			self.confirm_pass_input['show'] = ''
			toggle_confirm_password['image'] = self.images['visible']
			toggle_confirm_password['command'] = hide_confirm_password

		def hide_confirm_password():
			self.confirm_pass_input['show'] = '•'
			toggle_confirm_password['image'] = self.images['invisible']
			toggle_confirm_password['command'] = show_confirm_password

		toggle_confirm_password = tk.Button(confirm_pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_confirm_password)
		toggle_confirm_password.pack(padx=5, side='right')

		self.function_output = tk.Label(self.container, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=2, sticky='e', padx=(0, 30), pady=5)

		reset_password = tk.Button(self.container, image=self.images['reset'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:self.reset_password(email, self.pass_input.get().lower(), self.confirm_pass_input.get().lower()))
		reset_password.grid(column=0, row=6, padx=20, pady=20)
		back_button = tk.Button(self.container, text='Go back', bg=BACKGROUND, activebackground=BACKGROUND, fg=FOREGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('login'))
		back_button.grid(column=0, row=7, padx=30, pady=(0, 24), sticky='sw')

	def change_page(self, page, *args):
		self.container.destroy()
		self.container = tk.Frame(self, bg=BACKGROUND)
		self.container.pack(expand=True, fill='both')
		pages = {'register': self.register_page,
				'login': self.login_page,
				'forgot_password': self.forgot_password_page,
				'enter_code': self.enter_code_page,
				'reset_password': self.reset_password_page}
		pages[page](*args)			

	def register(self, email, username, password):
		self.cursor.execute(f"SELECT email from users WHERE email='{email}'")
		if self.cursor.fetchone(): # Each email can only be used once, no duplicates
			self.function_outputs['text'] = 'Email already in use.'
			return False
		try: # Checks if email fits criterea, e.g. has @url and .com
			validate_email(email)
		except NameError:
			pass
		except EmailNotValidError:
			self.function_outputs['text'] = 'Please enter a vaild email address.'
			return False

		hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))
		self.cursor.execute(f"INSERT INTO users VALUES('{email}', '{os.path.join(DIRECTORY, 'images', 'user_icon.png')}', '{username}', '{hashed_password.decode('utf-8')}')")
		self.connection.commit()

		self.change_page('login')
		self.function_outputs['text'] = 'Account created successfully.'
		self.email_input.insert(0, email)

	def login(self, email, password):
		self.cursor.execute(f"SELECT password from users WHERE email='{email}'")
		result = self.cursor.fetchone()
		if not result:
			self.function_outputs['text'] = 'Invalid email/password.'
			return False
		hashed = result[0]
		
		if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')): # If password is correct
			file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r')
			self.config = json.load(file)
			file.close()
			self.config['data'] = None
			if self.remember_me:
				self.config['data'] = cypher(email)
			with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w') as file:
				json.dump(self.config, file) # Saving config
			self.destroy()
			password_manager.PasswordManager(email).mainloop()
		else:
			self.function_outputs['text'] = 'Invalid email/password.'
			return False

	def send_code_to_user(self, recipient):
		self.cursor.execute(f"SELECT password from users WHERE email='{recipient}'")
		if not self.cursor.fetchone(): # returns true if user exists
			self.function_output['text'] = 'User not found.'
			return False

		characters = UPPERCASE + NUMBERS
		verify_code = ''
		for _ in range(8):
			# First choice chooses letter or number, second choice choses individual character
			verify_code += secrets.choice(secrets.choice(characters))

		if send_email('fjordpass.noreply@gmail.com', 'lnynprsdtgqzuotq', recipient, verify_code):
			self.change_page('enter_code', recipient, verify_code)
			return True
		messagebox.showerror('Error', 'Confirmation email was not sent. Please check your internet connection and try again.')

	def check_verify_code(self, email, verify_code, entered_code):
		if entered_code == verify_code:
			self.change_page('reset_password', email)
		else:
			self.function_output['text'] = 'Code is incorrect.'
			return False

	def reset_password(self, email, new_password, confirmed_password):
		if confirmed_password == new_password:
			self.cursor.execute(f"SELECT password from users WHERE email='{email}'")
			password = self.cursor.fetchone()[0]
			if bcrypt.checkpw(new_password.encode('utf-8'), password.encode('utf-8')):
				self.function_output['text'] = 'This is your current password.'
				return False
			new_password_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(10))
			self.cursor.execute(f"UPDATE Users SET password = ? WHERE email = ?", (new_password_hashed.decode('utf-8'), email))
			self.connection.commit()
			self.change_page('login')
			self.email_input.insert(0, email)
			self.function_outputs['text'] = 'Password successfully changed.'
			return True
		else:
			self.function_output['text'] = 'Passwords do not match.'
			return False
		
if __name__ == '__main__':
	LoginWindow().mainloop()