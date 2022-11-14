# Password Manager

import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image
from email_validator import validate_email, EmailNotValidError
import clipboard
import requests
from io import BytesIO
import secrets
import string
import bcrypt
import json
import sqlite3
import threading

# Constants
font_family = 'Century Gothic'
accent_colour = '#4B409E'

def colours(mode): # background, foreground, background_dark, show, hide
	if mode == 'dark':
		return '#1D2033', '#fafafa', '#0E1019', 'img/visible.png', 'img/invisible.png'
	else: # Light mode
		return '#e2e2e2', '#111111', '#cecece', 'img/visible_inverted.png', 'img/invisible_inverted.png'

def already_signed_in():
	file = open('config.json', 'r')
	config = json.load(file)
	if config['ask_to_login'] == False:
		user = config['user_email']
		file.close()
		return user
	file.close()
	return False

def init_database():
	connection = sqlite3.connect('database.db')
	cursor = connection.cursor()
	
	cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
						email TEXT PRIMARY KEY,
						username TEXT,
						password TEXT)""")
	cursor.execute("""CREATE TABLE IF NOT EXISTS Vault (
						master_email TEXT,
						display_image,
						title TEXT,
						platform TEXT,
						identifier TEXT,
						password TEXT)""")
	return cursor, connection

class LoginWindow(tk.Tk):
	def __init__(self):
		super().__init__()
		self.background, self.foreground, self.background_dark, show, hide = colours('dark') # Login window will always be dark mode as to not mess up images with white text
		self.title('Password Manager - Login')
		self.iconbitmap('password_manager.ico')
		self.geometry(f'400x500+{int(self.winfo_screenwidth()/2-200)}+{int(self.winfo_screenheight()/2-300)}')
		self.resizable(False, False)

		self.remember_me = False
		self.cursor, self.connection = init_database()

		self.image_logo = tk.PhotoImage(file='img/logo.png')
		self.image_login = tk.PhotoImage(file='img/login.png')
		self.image_register = tk.PhotoImage(file='img/register.png')
		self.image_checked = tk.PhotoImage(file='img/checked.png')
		self.image_unchecked = tk.PhotoImage(file='img/unchecked.png')
		self.image_show = tk.PhotoImage(file=show)
		self.image_hide = tk.PhotoImage(file=hide)
		
		self.container = tk.Frame(self, bg=self.background)
		self.container.pack(expand=True, fill='both')

		self.title_ = tk.Label(self.container, text='LOGIN TO YOUR ACCOUNT', bg=self.background, fg=self.foreground, font=(font_family, 16, 'bold'))
		self.title_.grid(column=0, columnspan=2, row=1, padx=60)

		self.login_widgets()

	def login_widgets(self):
		self.logo = tk.Label(self.container, image=self.image_logo, bg=self.background)
		self.logo.grid(column=0, columnspan=2, row=0, pady=12)
		self.inputs(False) # Create entry boxes excluding username box
		def toggle_off(value):
			self.remember_me = False
			self.checkbox['image'] = self.image_unchecked
			self.checkbox['command'] = lambda:toggle_on(value)

		def toggle_on(value):
			self.remember_me = True
			self.checkbox['image'] = self.image_checked
			self.checkbox['command'] = lambda:toggle_off(value)

		self.checkbox = tk.Button(self.container, image=self.image_unchecked, bg=self.background, activebackground=self.background, bd=0, padx=5, command=lambda:toggle_on(0))
		self.checkbox.grid(column=0, row=8, sticky='w', padx=30, pady=20)
		
		self.signin = tk.Button(self.container, image=self.image_login, bg=self.background, activebackground=self.background, bd=0, command=lambda:self.login(self.email_input.get(), self.pass_input.get()))
		self.signin.grid(column=0, columnspan=2, row=9)

		self.signup = tk.Button(self.container, text='Create new account.', cursor='hand2', bg=self.background, fg=self.foreground, activebackground=self.background, activeforeground=self.foreground, bd=0, font=(font_family, 10), command=lambda:self.switch_windows('register'))
		self.signup.grid(column=0, row=10, sticky='w', padx=30, pady=15)

		self.forgot_password = tk.Button(self.container, text='Forgot password?', cursor='hand2', bg=self.background, fg=self.foreground, activebackground=self.background, activeforeground=self.foreground, bd=0, font=(font_family, 10))
		self.forgot_password.grid(column=1, row=10, sticky='e', padx=30, pady=15)

	def register_widgets(self):
		self.inputs(True) # Create entry boxes including username box

		self.signup = tk.Button(self.container, image=self.image_register, bg=self.background, activebackground=self.background, bd=0, command=lambda:self.register(self.email_input.get(), self.user_input.get(), self.pass_input.get()))
		self.signup.grid(column=0, columnspan=2, row=8, pady=(20, 0))

		self.signin = tk.Button(self.container, text='Login to an existing account.', cursor='hand2', bg=self.background, fg=self.foreground, activebackground=self.background, activeforeground=self.foreground, bd=0, font=(font_family, 10), command=lambda:self.switch_windows('login'))
		self.signin.grid(column=0, columnspan=2, row=9, sticky='w', padx=30, pady=15)

	def inputs(self, with_username):
		# Email widgets
		self.email_label = tk.Label(self.container, text='EMAIL', bg=self.background, fg=self.foreground, font=(font_family, 11, 'bold'))
		self.email_label.grid(column=0, row=2, sticky='w', padx=(30, 0), pady=(15,5))
		self.email_frame = tk.Frame(self.container, bg=self.background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		self.email_frame.grid(column=0, columnspan=2, row=3, sticky='we', padx=20)
		self.email_input = tk.Entry(self.email_frame, bg=self.background_dark, fg=self.foreground, font=(font_family, 12), insertbackground=self.foreground, bd=0)
		self.email_input.pack(fill='both')

		if with_username: # Username widgets
			self.user_label = tk.Label(self.container, text='USERNAME', bg=self.background, fg=self.foreground, font=(font_family, 11, 'bold'))
			self.user_label.grid(column=0, row=4, sticky='w', padx=30, pady=5)
			self.user_frame = tk.Frame(self.container, bg=self.background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
			self.user_frame.grid(column=0, columnspan=2, row=5, sticky='we', padx=20)
			self.user_input = tk.Entry(self.user_frame, bg=self.background_dark, fg=self.foreground, font=(font_family, 12), insertbackground=self.foreground, bd=0)
			self.user_input.pack(expand=True, fill='both', side='left')

		# Password widgets
		self.pass_label = tk.Label(self.container, text='PASSWORD', bg=self.background, fg=self.foreground, font=(font_family, 11, 'bold'))
		self.pass_label.grid(column=0, row=6, sticky='w', padx=30, pady=5)
		self.pass_frame = tk.Frame(self.container, bg=self.background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		self.pass_frame.grid(column=0, columnspan=2, row=7, sticky='we', padx=20)
		self.pass_input = tk.Entry(self.pass_frame, bg=self.background_dark, fg=self.foreground, font=(font_family, 12), show='•', insertbackground=self.foreground, bd=0)
		self.pass_input.pack(expand=True, fill='both', side='left')

		# Display whether data is valid or not
		self.function_outputs = tk.Label(self.container, text='', bg=self.background, fg=accent_colour, font=(font_family, 11, 'bold'))
		self.function_outputs.grid(column=0, columnspan=2, row=2, sticky='e', padx=(0, 30), pady=(15,5))

		def show_password():
			self.pass_input['show'] = ''
			self.toggle_password['image'] = self.image_show
			self.toggle_password['command'] = hide_password

		def hide_password():
			self.pass_input['show'] = '•'
			self.toggle_password['image'] = self.image_hide
			self.toggle_password['command'] = show_password

		self.toggle_password = tk.Button(self.pass_frame, image=self.image_hide, bg=self.background_dark, activebackground=self.background_dark, bd=0, command=show_password)
		self.toggle_password.pack(padx=5, side='right')

	def switch_windows(self, window):
		self.container.destroy()
		self.container = tk.Frame(self, bg=self.background)
		self.container.pack(expand=True, fill='both')
		if window == 'register':
			self.title('Password Manager - Register')
			self.title_ = tk.Label(self.container, text='REGISTER AN ACCOUNT', bg=self.background, fg=self.foreground, font=(font_family, 16, 'bold'))
			self.title_.grid(column=0, columnspan=2, row=1, padx=78, pady=(45,0))
			self.register_widgets()
		if window == 'login':
			self.title('Password Manager - Login')
			self.title_ = tk.Label(self.container, text='LOGIN TO YOUR ACCOUNT', bg=self.background, fg=self.foreground, font=(font_family, 16, 'bold'))
			self.title_.grid(column=0, columnspan=2, row=1, padx=60)
			self.login_widgets()

	def register(self, email, username, password):
		self.cursor.execute(f"SELECT email from users WHERE email='{email}'")
		if self.cursor.fetchone(): # Each emaik can only be used once, no duplicates
			self.function_outputs['text'] = 'Email already in use.'
			return False
		try: # Checks if email fits criterea, e.g. has @url and .com
			validate = validate_email(email)
		except EmailNotValidError:
			self.function_outputs['text'] = 'Please enter a vaild email address.'
			return False

		hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))
		self.cursor.execute(f"INSERT INTO users VALUES('{email}', '{username}', '{hashed_password.decode('utf-8')}')")
		self.connection.commit()

		self.switch_windows('login')
		self.function_outputs['text'] = 'Account created successfully.'

	def login(self, email, password):
		self.cursor.execute(f"SELECT username, password from users WHERE email='{email}'")
		try: # If enetered email doesn't exist within database
			username, hashed = self.cursor.fetchone()
		except:
			self.function_outputs['text'] = 'Invalid email/password.'
			return False
		
		if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')): # If password is correct
			self.destroy()
			PasswordManager(email).mainloop()
			if self.remember_me:
				config = {'ask_to_login': False, 'user_email': email}
			else:
				config = {'ask_to_login': True}
			file = open('config.json', 'w')
			json.dump(config, file, indent=4) # Saving config
			file.close()
		else:
			self.function_outputs['text'] = 'Invalid email/password.'
			return False

class PasswordGenerator(tk.Toplevel):
	def __init__(self):
		super().__init__()
		self.title('Password Generator')
		self.iconbitmap('password_manager.ico')
		self.geometry(f'360x480+{int(self.winfo_screenwidth()/2-180)}+{int(self.winfo_screenheight()/2-290)}')
		self.resizable(False, False)

		self.lowercase = 'abcdefghijklmnopqrstuvwxyz'
		self.uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		self.numbers = string.digits
		self.special_chars = string.punctuation

		# Images
		self.image_generate = tk.PhotoImage(file='img/generate.png')
		self.image_toggle_on = tk.PhotoImage(file='img/toggle_on.png')
		self.image_toggle_off = tk.PhotoImage(file='img/toggle_off.png')
		self.image_copy = tk.PhotoImage(file='img/copy.png')

		self.container = tk.Frame(self, bg=background)
		self.container.pack(expand=True, fill='both')

		self.widgets()

	def widgets(self):
		self.title = tk.Label(self.container, text='PASSWORD  GENERATOR', bg=background, 
								fg=foreground, font=(font_family, 14, 'bold'))
		self.title.grid(column=0, columnspan=2, row=0, padx=(27, 28), pady=30, sticky='we')

		self.output_frame = tk.Frame(self.container, bg=background_dark)
		self.output_frame.grid(column=0, columnspan=2, row=1, sticky='we')
		self.output = tk.Entry(self.output_frame, bg=background_dark, fg=foreground, font=(font_family, 12), 
								bd=0, width=29, insertbackground=foreground)
		self.output.grid(column=0, row=0, padx=(20, 0))

		self.copy = tk.Button(self.output_frame, image=self.image_copy, bg=background_dark, activebackground=background_dark, font=(font_family, 12), 
									bd=0, command=lambda:clipboard.copy(self.output.get()))
		self.copy.grid(column=1, row=0, padx=5, pady=5, sticky='e')

		self.length_label = tk.Label(self.container, text='Password Length', bg=background, fg=foreground, font=(font_family, 12))
		self.length_label.grid(column=0, row=2, sticky='w', padx=30, pady=(30, 20))

		self.password_length = tk.IntVar()
		self.default_length = 15
		self.length_display = tk.Label(self.container, text=self.default_length, bg=background, fg=foreground, font=(font_family, 12))
		self.length_display.grid(column=1, row=2, sticky='e', padx=30, pady=(30, 20))

		self.length_slider = tk.Scale(self.container, orient='horizontal', from_=5, to=25, bg=accent_colour, fg=foreground, resolution=1, 
										variable=self.password_length, showvalue=False, sliderlength=15, highlightthickness=0, bd=0, troughcolor=background_dark, 
										sliderrelief='flat', command=lambda args:self.length_display.config(text=self.length_slider.get()))
		self.length_slider.set(self.default_length)
		self.length_slider.grid(column=0, columnspan=2, row=3, sticky='we', padx=30)

		self.re_roll = tk.Button(self.container, image=self.image_generate, bg=background, activebackground=background, bd=0, command=self.generate_password)
		self.re_roll.grid(column=0, columnspan=2, row=5)

		self.toggles()

	def toggles(self):
		self.toggles_frame = tk.Frame(self.container, bg=background)
		self.toggles_frame.grid(column=0, columnspan=2, row=4, padx=27, pady=40, sticky='we')

		self.toggle_labels = ['a-z', 'A-Z', '0-9', '!@#']
		for n in range(4):
			tk.Label(self.toggles_frame, text=self.toggle_labels[n], bg=background, fg=foreground, font=(font_family, 12)).grid(column=n, row=0, sticky='w')

		def toggle_off(widget):
			widget['image'] = self.image_toggle_off
			buffer = widget['text']
			widget['command'] = lambda:toggle_on(widget, buffer)
			widget['text'] = ''

		def toggle_on(widget, value):
			widget['text'] = value
			widget['image'] = self.image_toggle_on
			widget['command'] = lambda:toggle_off(widget)

		self.toggle_a_z = tk.Button(self.toggles_frame, image=self.image_toggle_on, text=self.lowercase, bg=background, activebackground=background, bd=0, command=lambda:toggle_off(self.toggle_a_z))
		self.toggle_a_z.grid(column=0, row=1, padx=(0, 32))
		self.toggle_A_Z = tk.Button(self.toggles_frame, image=self.image_toggle_on, text=self.uppercase, bg=background, activebackground=background, bd=0, command=lambda:toggle_off(self.toggle_A_Z))
		self.toggle_A_Z.grid(column=1, row=1, padx=(0, 33))
		self.toggle_0_9 = tk.Button(self.toggles_frame, image=self.image_toggle_on, text=self.numbers, bg=background, activebackground=background, bd=0, command=lambda:toggle_off(self.toggle_0_9))
		self.toggle_0_9.grid(column=2, row=1, padx=(0, 33))
		self.toggle_sc = tk.Button(self.toggles_frame, image=self.image_toggle_on, text=self.special_chars, bg=background, activebackground=background, bd=0, command=lambda:toggle_off(self.toggle_sc))
		self.toggle_sc.grid(column=3, row=1)

	def generate_password(self):
		self.alphabet = ''
		for widget in self.toggles_frame.winfo_children()[4:8]:
			if widget['text'] != '':
				self.alphabet += widget['text']
		
		self.length = self.password_length.get()

		password = ''
		if self.alphabet != '':
			for n in range(self.length):
				password += ''.join(secrets.choice(self.alphabet))

			self.output.delete(0, 'end')
			self.output.insert('end', password)

class SettingsWindow(tk.Toplevel):
	def __init__(self):
		super().__init__()
		self.placeholder = tk.Label(self, text='Settings').pack()

class PasswordManager(tk.Tk):
	def __init__(self, email):
		super().__init__()
		self.title('Password Manager')
		self.iconbitmap('password_manager.ico')
		self.geometry(f'+{int(self.winfo_screenwidth()/2-500)}+{int(self.winfo_screenheight()/2-350)}') # Centers window
		self.minsize(900, 600)

		self.user_email = email
		self.cursor, self.connection = init_database()
		self.cursor.execute(f"SELECT username FROM Users WHERE email = '{self.user_email}'")
		self.user = self.cursor.fetchone()[0]

		# Images
		self.image_all_items = tk.PhotoImage(file='img/all_items.png')
		self.image_passwords = tk.PhotoImage(file='img/password.png')
		self.image_cards = tk.PhotoImage(file='img/card.png')
		self.image_padlock = tk.PhotoImage(file='img/padlock.png')
		self.image_search = tk.PhotoImage(file='img/search.png')
		self.image_default_user = tk.PhotoImage(file='img/user_icon.png')
		self.image_save = tk.PhotoImage(file='img/save.png')
		self.image_cancel = tk.PhotoImage(file='img/cancel.png')
		self.image_default = tk.PhotoImage(file='img/default.png')
		self.image_add_item = tk.PhotoImage(file='img/add_item.png')
		self.image_open = tk.PhotoImage(file='img/full_view.png')
		self.image_trash = tk.PhotoImage(file='img/delete.png')
		self.image_show = tk.PhotoImage(file=show)
		self.image_hide = tk.PhotoImage(file=hide)
		
		self.container = tk.Frame(self, bg=background)
		self.container.place(x=250, y=0, relwidth=1, width=-250, relheight=1)

		# Init widgets
		self.sidebar()
		self.view_all_items()

	def logout(self):
		self.destroy()
		file = open('config.json', 'w')
		json.dump({'ask_to_login': True}, file, indent=4) # Saving config
		file.close()
		LoginWindow().mainloop()

	def sidebar(self):
		background, foreground, background_dark = colours('dark')[0:3] # Resets colour scheme for sidebar only
		self.sidebar = tk.Frame(self, bg=background_dark)
		self.sidebar.pack(fill='y', side='left')

		self.sidebar.grid_rowconfigure(8, weight=1) # Bottom widgets stick to bottom when resized

		# User details
		self.user_icon = tk.Button(self.sidebar, image=self.image_default_user, bg=background_dark, activebackground=background_dark, bd=0, command=None, cursor='hand2')
		self.user_icon.grid(column=0, row=0, padx=(15, 5), pady=20, sticky='w')
		self.user_welcome = tk.Label(self.sidebar, text=f'Hello, {self.user}', bg=background_dark, fg=foreground, font=(font_family, 12))
		self.user_welcome.grid(column=0, columnspan=3, row=0, padx=(60, 15), pady=20, sticky='w')
		if len(str(self.user)) > 12: # If length of username excedes 12 characters, only display first 12
			self.user_welcome['text'] = f'Hello, {self.user[0:10]}...'

		# Searchbar
		self.searchbar_frame = tk.Frame(self.sidebar, bg='white', highlightbackground="black", highlightthickness=1, highlightcolor='black')
		self.searchbar_frame.grid(column=0, columnspan=3, row=1, padx=10, sticky='we')
		self.searchbar = tk.Entry(self.searchbar_frame, bg='white', fg='black', font=(font_family, 10), bd=0)
		self.searchbar.pack(expand=True, fill='x', side='left', padx=5)
		self.searchbutton = tk.Button(self.searchbar_frame, image=self.image_search, bg=accent_colour, activebackground=background_dark, bd=0)
		self.searchbutton.pack(side='right')

		# Categories
		self.category_title = tk.Label(self.sidebar, text='CATEGORIES', bg=background_dark, fg=foreground, font=(font_family, 10))
		self.category_title.grid(column=0, columnspan=3, row=2, sticky='we', pady=20)

		## Categories - Buttons
		self.category_all_items = tk.Button(self.sidebar, text='All Items', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=foreground, bd=0, font=(font_family, 10), cursor='hand2', command=lambda:self.change_page('view_all'))
		self.category_all_items.grid(column=0, columnspan=3, row=3, sticky='w', padx=40)
		self.category_passwords = tk.Button(self.sidebar, text='Passwords', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=foreground, bd=0, font=(font_family, 10), cursor='hand2', command=lambda:self.change_page('view_passwords'))
		self.category_passwords.grid(column=0, columnspan=3, row=4, sticky='w', padx=40, pady=15)
		self.category_cards = tk.Button(self.sidebar, text='Cards', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=foreground, bd=0, font=(font_family, 10), cursor='hand2', command=lambda:self.change_page('view_cards'))
		self.category_cards.grid(column=0, columnspan=3, row=5, sticky='w', padx=40)

		## Categories - Icons
		self.category_all_items_icon = tk.Label(self.sidebar, image=self.image_all_items, bg=background_dark)
		self.category_all_items_icon.grid(column=0, row=3, sticky='w', padx=15)
		self.category_passwords_icon = tk.Label(self.sidebar, image=self.image_passwords, bg=background_dark)
		self.category_passwords_icon.grid(column=0, row=4, sticky='w', padx=15)
		self.category_cards_icon = tk.Label(self.sidebar, image=self.image_cards, bg=background_dark)
		self.category_cards_icon.grid(column=0, row=5, sticky='w', padx=15)

		# Tools
		self.tools_title = tk.Label(self.sidebar, text='TOOLS', bg=background_dark, fg=foreground, font=(font_family, 10))
		self.tools_title.grid(column=0, columnspan=3, row=6, sticky='we', pady=20)

		self.tools_generator_icon = tk.Label(self.sidebar, image=self.image_padlock, bg=background_dark)
		self.tools_generator_icon.grid(column=0, row=7, sticky='w', padx=15)
		self.tools_generator = tk.Button(self.sidebar, text='Password Generator', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=foreground, bd=0, font=(font_family, 10), cursor='hand2', command=lambda:PasswordGenerator().mainloop())
		self.tools_generator.grid(column=0, columnspan=3, row=7, sticky='w', padx=40)

		# Options
		self.button_logout = tk.Button(self.sidebar, text='LOGOUT', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=accent_colour, bd=0, font=(font_family, 10, 'bold'), cursor='hand2', command=self.logout)
		self.button_logout.grid(column=0, columnspan=2, row=8, sticky='sw', padx=(10, 52), pady=10)
		self.button_settings = tk.Button(self.sidebar, text='SETTINGS', bg=background_dark, activebackground=background_dark, activeforeground=foreground, fg=foreground, bd=0, font=(font_family, 10, 'bold'), cursor='hand2', command=lambda:SettingsWindow().mainloop())
		self.button_settings.grid(column=2, row=8, sticky='se', padx=(51, 10), pady=10)
			
	def change_page(self, page):
		self.container.destroy()
		self.container = tk.Frame(self, bg=background)
		self.container.pack(expand=True, fill='both', side='right')

		if page == 'new_item':
			self.new_item()
		if page == 'new_password':
			self.new_password()
		if page == 'new_card':
			self.new_card()
		if page == 'view_all':
			self.view_all_items()
		if page == 'view_passwords':
			self.view_passwords()
		if page == 'view_cards':
			self.view_cards()

	def view_all_items(self):
		self.viewer = tk.Frame(self.container, bg=background)
		self.viewer.pack(fill='both', expand=True, padx=30, pady=25)
		self.viewer.grid_columnconfigure(1, weight=1)
		self.viewer.grid_columnconfigure(2, weight=1)
		
		self.add_item = tk.Button(self.viewer, image=self.image_add_item, bd=0, bg=background, activebackground=background, cursor='hand2', command=lambda:self.change_page('new_password'))
		
		# Checking if any items are in database
		self.cursor.execute(f"SELECT title FROM Vault WHERE master_email = '{self.user_email}'")
		check_for_items = self.cursor.fetchone()

		if check_for_items != None:
			self.add_item.place(relx=1, anchor='ne', y=0)
			self.page_title = tk.Label(self.viewer, text='All Items', bg=background, fg=foreground, font=(font_family, 20))
			self.page_title.grid(column=0, columnspan=5, row=0, sticky='w', padx=(0, 150))

			# Column headers
			self.image_header = tk.Label(self.viewer, text='IMAGE', bg=background, fg=foreground, font=(font_family, 9, 'bold'))
			self.image_header.grid(column=0, row=1, sticky='w', pady=(20, 0))
			
			self.title_header = tk.Label(self.viewer, text='TITLE', bg=background, fg=foreground, font=(font_family, 9, 'bold'))
			self.title_header.grid(column=1, row=1, sticky='w', padx=(0, 75), pady=(20, 0))
			
			self.identifier_header = tk.Label(self.viewer, text='USERNAME / EMAIL', bg=background, fg=foreground, font=(font_family, 9, 'bold'))
			self.identifier_header.grid(column=2, row=1, sticky='w', padx=(0, 75), pady=(20, 0))
			
			self.divider = tk.Frame(self.viewer, bg='grey')
			self.divider.grid(column=0, columnspan=5, row=2, sticky='we', pady=10)
			
			# Retrieving data
			self.cursor.execute(f"SELECT display_image, title, identifier, oid FROM Vault WHERE master_email = '{self.user_email}'")
			items = self.cursor.fetchall()
			
			self.image_list, image = [], 0
			for item in items:
				# Setting current row based on current item's oid
				current_row = 2*item[3]+1 # Multiplied by two to allow space for divider
				# If image is url then load url else display image
				if item[0][0:4] == 'http':
					response = requests.get(item[0])
					img_data = response.content
					self.image_list.append(ImageTk.PhotoImage(Image.open(BytesIO(img_data)).resize((50, 50))))
				else:
					self.image_list.append(ImageTk.PhotoImage(Image.open(item[0]).resize((50, 50))))
				tk.Label(self.viewer, image=self.image_list[image], bg=background).grid(row=current_row, column=0, sticky='w', padx=(0, 25))
				# If image is default then display first two characters from title over top
				if item[0] == 'img/default.png':
					tk.Label(self.viewer, text=item[1][0:2].title(), bg='#bebebe', fg='#606060', font=(font_family, 12, 'bold')).grid(row=current_row, column=0, sticky='we', padx=(9, 34))
				# Loop to create title and username labels
				height_from_top_to_fisrt_divider = 117
				height_of_each_record = 75
				for n in range(2):
					# Create frame with maximum width so that if length of text is too big, nothing is impacted
					temp_frame = tk.Frame(self.viewer, width=180, height=25, bg=background)
					temp_frame.grid(row=current_row, column=n+1, padx=(0, 30), sticky='we')
					temp_frame.grid_propagate(0)
					tk.Label(temp_frame, text=item[n+1], bg=background, fg=foreground, font=(font_family, 10)).grid(row=0, column=0, sticky='nsw')
				def open(record): # Full view of individual record
					print(self.expanded_record_view(record//2))
					print((self.viewer.winfo_height()+50-117)/75)
				def delete(record): # Delete selected record
					self.cursor.execute(f"DELETE FROM Vault WHERE oid = '{record//2}'")
					self.connection.commit()
					self.change_page('view_all')
				# Open, delete butons
				self.open_record = tk.Button(self.viewer, image=self.image_open, bd=0, bg=background, activebackground=background, cursor='hand2', command=lambda current_row=current_row:open(current_row))
				self.open_record.grid(column=3, row=current_row, padx=(0, 5), sticky='e')
				self.delete_record = tk.Button(self.viewer, image=self.image_trash, bd=0, bg=background, activebackground=background, cursor='hand2', command=lambda current_row=current_row:delete(current_row))
				self.delete_record.grid(column=4, row=current_row, sticky='e')

				tk.Frame(self.viewer, bg=background_dark).grid(column=0, columnspan=5, row=current_row+1, sticky='we', pady=10) # Divider
				image += 1 # Go to next image in list

		else:
			# If no items found, display this instead
			self.first_item = tk.Label(self.viewer, text='Add your first item', bg=background, fg=foreground, font=(font_family, 24))
			self.first_item.place(anchor='center', relx=.5, rely=.5, y=-30)
			self.add_item.place(anchor='center', relx=.5, rely=.5, y=+30)
		
	def view_passwords(self):
		return

	def view_cards(self):
		return

	def expanded_record_view(self, oid):
		return oid

	def new_item(self):
		return

	def new_password(self):
		self.new_item_frame = tk.Frame(self.container, bg=background)
		self.new_item_frame.place(anchor='center', relx=.5, rely=.5)
		self.new_item_frame.grid_columnconfigure(1, weight=1)
		
		self.page_title = tk.Label(self.new_item_frame, text='Add New Password', bg=background, fg=foreground, font=(font_family, 20))
		self.page_title.grid(column=0, row=0, columnspan=2, pady=(0, 30), ipadx=100)
		
		# Item icon
		self.item_image_location = 'img/default.png' # Default image
		def item_image(): # Allow user to choose new icon to display
			self.item_image_location = tk.filedialog.askopenfilename(title="Select Image", filetypes =(("PNG", "*.png"),("JPG", "*.jpg"),("All Files","*.*")))
			if self.item_image_location != '':
				self.new_image = Image.open(self.item_image_location)
				self.new_image = self.new_image.resize((90, 90))
				self.new_image = ImageTk.PhotoImage(self.new_image)
				self.item_icon['image'] = self.new_image
				self.letters.destroy()

		self.item_icon = tk.Button(self.new_item_frame, image=self.image_default, width=90, height=90, bd=0, bg=background, activebackground=background, command=item_image)
		self.item_icon.grid(column=0, row=1, rowspan=2, sticky='w', padx=(0, 20))
		if self.item_image_location == 'img/default.png': # Get first two characters and display over default icon
			self.letters = tk.Button(self.new_item_frame, text='', bd=0, bg='#bebeb4', activebackground='#bebebe', fg='#606060', activeforeground='#606060', font=(font_family, 18, 'bold'), command=item_image)
			self.letters.grid(column=0, row=1, rowspan=2, sticky='we', padx=(14, 34), pady=(3, 0))
		
		# Item title
		def update(*args):
			try: # If image is default then display first 2 chars, else return false
				self.letters['text'] = str(self.title_input.get())[0:2].title()
			except:
				return False

		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', update) # Updates every time input changes

		self.title_label = tk.Label(self.new_item_frame, text='TITLE', bg=background, fg=foreground, font=(font_family, 11, 'bold'))
		self.title_label.grid(column=1, row=1, sticky='w', padx=10, pady=(10,0))
		self.title_frame = tk.Frame(self.new_item_frame, bg=background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor=foreground, highlightthickness=1)
		self.title_frame.grid(column=1, row=2, sticky='we')
		self.title_input = tk.Entry(self.title_frame, textvariable=self.update_check, bg=background_dark, fg=foreground, font=(font_family, 12), insertbackground=foreground, bd=0)
		self.title_input.pack(fill='both')
		
		# Item url
		self.platform_label = tk.Label(self.new_item_frame, text='WEBSITE URL', bg=background, fg=foreground, font=(font_family, 11, 'bold'))
		self.platform_label.grid(column=0, row=3, columnspan=2, sticky='w', padx=10, pady=(10,0))
		self.platform_frame = tk.Frame(self.new_item_frame, bg=background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor=foreground, highlightthickness=1)
		self.platform_frame.grid(column=0, row=4, columnspan=2, sticky='we')
		self.platform_input = tk.Entry(self.platform_frame, bg=background_dark, fg=foreground, font=(font_family, 12), insertbackground=foreground, bd=0)
		self.platform_input.pack(fill='both')

		def thread(event=None): # New thread to not slow down program
		    threading.Thread(target=update_image).start()
		
		def update_image():
			# Refining URL
			url = f'{self.platform_input.get()}/favicon.ico'
			if url[0:8] != 'https://' and url[0:7] != 'http://':
				url = f'http://{url}'
			try:
				response = requests.get(url)
				img_data = response.content
				image = Image.open(BytesIO(img_data))
				image = image.resize((90, 90))
				self.new_image = ImageTk.PhotoImage(image)
				self.item_icon['image'] = self.new_image
				self.item_image_location = url
				try: # Nested try so that code above still functions
					self.letters.destroy()
				except:
					pass
			except:
				return False
		
		self.platform_input.bind('<FocusOut>', thread) # When not focused on entry widget, run function
		
		# Item identifier (email or username)
		self.identifier_label = tk.Label(self.new_item_frame, text='USERNAME / EMAIL', bg=background, fg=foreground, font=(font_family, 11, 'bold'))
		self.identifier_label.grid(column=0, row=5, columnspan=2, sticky='w', padx=10, pady=(10,0))
		self.identifier_frame = tk.Frame(self.new_item_frame, bg=background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor=foreground, highlightthickness=1)
		self.identifier_frame.grid(column=0, row=6, columnspan=2, sticky='we')
		self.identifier_input = tk.Entry(self.identifier_frame, bg=background_dark, fg=foreground, font=(font_family, 12), insertbackground=foreground, bd=0)
		self.identifier_input.pack(fill='both')
		
		# Item password
		self.password_label = tk.Label(self.new_item_frame, text='PASSWORD', bg=background, fg=foreground, font=(font_family, 11, 'bold'))
		self.password_label.grid(column=0, row=7, columnspan=2, sticky='w', padx=10, pady=(10,0))
		self.password_frame = tk.Frame(self.new_item_frame, bg=background_dark, pady=15, padx=10, highlightbackground='grey', highlightcolor=foreground, highlightthickness=1)
		self.password_frame.grid(column=0, row=8, columnspan=2, sticky='we')
		self.password_input = tk.Entry(self.password_frame, bg=background_dark, fg=foreground, font=(font_family, 12), show='•', insertbackground=foreground, bd=0)
		self.password_input.pack(expand=True, fill='both', side='left')

		def show_password():
			self.password_input['show'] = ''
			self.toggle_password['image'] = self.image_show
			self.toggle_password['command'] = hide_password

		def hide_password():
			self.password_input['show'] = '•'
			self.toggle_password['image'] = self.image_hide
			self.toggle_password['command'] = show_password

		self.toggle_password = tk.Button(self.password_frame, image=self.image_hide, bg=background_dark, activebackground=background_dark, bd=0, command=show_password)
		self.toggle_password.pack(padx=5, side='right')

		# Frame to evenly space buttons
		self.button_frame = tk.Frame(self.new_item_frame, bg=background)
		self.button_frame.grid(column=0, row=10, columnspan=2, pady=(4, 0), sticky='we')
	
		self.save = tk.Button(self.button_frame, image=self.image_save, bg=background, activebackground=background, bd=0, cursor='hand2', command=self.save_new_item)
		self.save.pack(side='left')
		self.cancel = tk.Button(self.button_frame, image=self.image_cancel, bg=background, activebackground=background, bd=0, cursor='hand2', command=lambda:self.change_page('view_all'))
		self.cancel.pack(side='right')

		# Displays whether data is valid or not
		self.function_output = tk.Label(self.new_item_frame, text='', bg=background, fg=accent_colour, font=(font_family, 11, 'bold'))
		self.function_output.grid(column=0, row=9, columnspan=2, pady=4, padx=10, sticky='w')
	
	def new_card(self):
		return
	
	def save_new_item(self):
		if self.title_input.get() != '' and self.platform_input.get() != '' and self.identifier_input.get() != '' and self.password_input.get() != '': # If all boxes are not empty
			data = [self.user_email, self.item_image_location, self.title_input.get(), self.platform_input.get(), self.identifier_input.get(), self.password_input.get()]
			self.cursor.execute("INSERT INTO Vault VALUES(?, ?, ?, ?, ?, ?)", data)
			self.connection.commit()
			self.function_output['text'] = '* Item has been successfully added.'
		else:
			self.function_output['text'] = '* Please fill out all of the boxes.'

	def test_spacing(self):
		# [DEBUG] helps with aligning widgets
		colors = ['red', 'green', 'blue', 'yellow', 'purple', 'white', 'black', 'brown', 'pink', 'orange']
		for widget in self.sidebar.winfo_children():
			widget['bg'] = random.choice(colors)


if __name__ == '__main__':
	background, foreground, background_dark, show, hide = colours('dark') # Set colour theme
	user = already_signed_in()
	if user == False:
		LoginWindow().mainloop()
	else:
		PasswordManager(user).mainloop()
