import tkinter as tk
from tkinter import filedialog, ttk
from PIL import ImageTk, Image
import clipboard, json, threading

from support import *
import settings, password_generator, login

class PasswordManager(tk.Tk):
	def __init__(self, email):
		super().__init__()

		# Read config
		with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r') as file:
			config = dict(json.load(file))
		if 'window_width' not in config.keys() or 'window_height' not in config.keys(): 
			with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w') as file:
				config['window_width'], config['window_height'] = 920, 600
				json.dump(config, file)
		self.width, self.height = config['window_width'], config['window_height']

		# General
		self.title('FjordPass - Password Manager')
		self.iconbitmap(os.path.join(DIRECTORY, 'icon.ico'))
		centerx = int(self.winfo_screenwidth()//2-self.width//2)
		centery = int(self.winfo_screenheight()//2-(self.height//2))
		self.geometry(f'{self.width}x{self.height}+{centerx}+{centery-50}') # Centers window
		self.minsize(970, 600)

		# Styling vertical scrollbars
		scroll_style = ttk.Style()
		scroll_style.theme_use('clam')
		scroll_style.configure("Vertical.TScrollbar", gripcount=0,
                background=ACCENT, darkcolor=ACCENT, lightcolor=ACCENT,
                troughcolor=BACKGROUND_DARK, bordercolor=BACKGROUND, arrowcolor='white')
		scroll_style.map('Vertical.TScrollbar', background=[('pressed', '!disabled', 'active', ACCENT)])

		# User data
		self.user_email = email
		self.cursor, self.connection = init_database()
		self.cursor.execute(f"SELECT username, profile_picture FROM Users WHERE email = '{self.user_email}'")
		self.user, self.profilepic = self.cursor.fetchone()

		# Load images
		self.images = import_images(os.path.join(DIRECTORY, 'images', ''))
		for key, value in self.images.items():
			self.images[key] = ImageTk.PhotoImage(Image.open(value))
		
		self.container = tk.Frame(self, bg=BACKGROUND)
		self.container.place(x=250, y=0, relwidth=1, width=-250, relheight=1)

		# Init widgets
		self.sidebar()
		self.switch_view('view_all')
		self.bind('<Configure>', self.get_size)

	def sidebar(self):
		sidebar = tk.Frame(self, bg=BACKGROUND_DARK)
		sidebar.pack(fill='y', side='left')

		sidebar.grid_rowconfigure(8, weight=1) # Bottom widgets stick to bottom when resized

		# User details
		self.image_pfp = ImageTk.PhotoImage(Image.open(self.profilepic).resize((32, 32)))
		self.user_icon = tk.Label(sidebar, image=self.image_pfp, bg=BACKGROUND_DARK, width=34, height=34)
		self.user_icon.grid(column=0, row=0, padx=(15, 5), pady=20, sticky='w')
		self.user_welcome = tk.Label(sidebar, text=f'Hello, {self.user}', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12))
		self.user_welcome.grid(column=0, columnspan=3, row=0, padx=(60, 15), pady=20, sticky='w')
		for index in range(len(self.user), 0, -1):
			if self.user_welcome.winfo_reqwidth() > 175: # If length of username excedes maximum length, only display visible characters
				displayed_username = self.user[0:index]
				self.user_welcome['text'] = f'Hello, {displayed_username}...'
			else: break

		# Searchbar
		searchbar_frame = tk.Frame(sidebar, bg='white', highlightbackground="black", highlightthickness=1, highlightcolor='black')
		searchbar_frame.grid(column=0, columnspan=3, row=1, padx=10, sticky='we')
		searchbar = tk.Entry(searchbar_frame, bg='white', fg='black', font=(FONT, 10), bd=0)
		searchbar.pack(expand=True, fill='x', side='left', padx=(5, 22))
		def clear():
			searchbar.delete(0, 'end')
			self.focus()
		tk.Button(searchbar_frame, image=self.images['clear_search'], bg='white', activebackground='white', bd=0, command=clear, cursor='hand2').place(x=176, y=9)
		searchbutton = tk.Button(searchbar_frame, image=self.images['search'], bg=ACCENT, activebackground=BACKGROUND_DARK, bd=0, cursor='hand2', command=lambda:self.switch_view('search_results', searchbar.get()))
		searchbutton.pack(side='right')

		searchbar.bind('<FocusIn>', lambda event: searchbar.bind('<Return>', lambda event: self.switch_view('search_results', searchbar.get())))
		searchbar.bind('<FocusOut>', lambda event: searchbar.unbind('<Return>'))

		# Categories
		category_title = tk.Label(sidebar, text='CATEGORIES', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 10))
		category_title.grid(column=0, columnspan=3, row=2, sticky='we', pady=20)

		category_all_items = tk.Button(sidebar, text='All Items', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=FOREGROUND, bd=0, font=(FONT, 10), cursor='hand2', command=lambda:self.switch_view('view_all'))
		category_all_items.grid(column=0, columnspan=3, row=3, sticky='w', padx=40)
		category_passwords = tk.Button(sidebar, text='Passwords', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=FOREGROUND, bd=0, font=(FONT, 10), cursor='hand2', command=lambda:self.switch_view('view_passwords'))
		category_passwords.grid(column=0, columnspan=3, row=4, sticky='w', padx=40, pady=15)
		category_cards = tk.Button(sidebar, text='Cards', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=FOREGROUND, bd=0, font=(FONT, 10), cursor='hand2', command=lambda:self.switch_view('view_cards'))
		category_cards.grid(column=0, columnspan=3, row=5, sticky='w', padx=40)

		category_all_items_icon = tk.Label(sidebar, image=self.images['all_items'], bg=BACKGROUND_DARK)
		category_all_items_icon.grid(column=0, row=3, sticky='w', padx=15)
		category_passwords_icon = tk.Label(sidebar, image=self.images['password'], bg=BACKGROUND_DARK)
		category_passwords_icon.grid(column=0, row=4, sticky='w', padx=15)
		category_cards_icon = tk.Label(sidebar, image=self.images['card'], bg=BACKGROUND_DARK)
		category_cards_icon.grid(column=0, row=5, sticky='w', padx=15)

		# Tools
		tools_title = tk.Label(sidebar, text='TOOLS', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 10))
		tools_title.grid(column=0, columnspan=3, row=6, sticky='we', pady=20)

		tools_generator_icon = tk.Label(sidebar, image=self.images['padlock'], bg=BACKGROUND_DARK)
		tools_generator_icon.grid(column=0, row=7, sticky='w', padx=15)
		def open_password_generator():
			window = password_generator.PasswordGenerator()
			window.wm_transient(self)
			window.focus()
			window.mainloop()
		tools_generator = tk.Button(sidebar, text='Password Generator', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=FOREGROUND, bd=0, font=(FONT, 10), cursor='hand2', command=open_password_generator)
		tools_generator.grid(column=0, columnspan=3, row=7, sticky='w', padx=40)

		# Options
		button_logout = tk.Button(sidebar, text='LOGOUT', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=ACCENT, bd=0, font=(FONT, 10, 'bold'), cursor='hand2', command=self.logout)
		button_logout.grid(column=0, columnspan=2, row=8, sticky='sw', padx=(10, 52), pady=10)
		def open_settings():
			window = settings.Settings(self, self.user_email)
			window.wm_transient(self)
			window.focus()
			window.mainloop()
		button_settings = tk.Button(sidebar, text='SETTINGS', bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, fg=FOREGROUND, bd=0, font=(FONT, 10, 'bold'), cursor='hand2', command=open_settings)
		button_settings.grid(column=2, row=8, sticky='se', padx=(51, 10), pady=10)
		
	def switch_view(self, page, *args):
		for widget in self.container.winfo_children():
			widget.destroy()
		pages = {'view_all': self.view_all_items,
				'view_passwords': self.view_passwords,
				'new_password': self.new_password,
				'expanded_password': self.expanded_password_view,
				'edit_password': self.edit_password,
				'view_cards': self.view_cards,
				'new_card': self.new_card,
				'expanded_card': self.expanded_card_view,
				'edit_card': self.edit_card,
				'search_results': self.view_search_results}
		pages[page](*args)

	def get_size(self, *args):
		self.width, self.height = self.winfo_width(), self.winfo_height()

	def handle_resize(self, event, tag):
		canvas = event.widget
		canvas_frame = canvas.nametowidget(canvas.itemcget(tag, "window"))
		if canvas_frame.winfo_reqwidth() < event.width:
			canvas.itemconfigure(tag, width=event.width)
		if canvas_frame.winfo_reqheight() < event.height:
			canvas_frame.configure(height=event.height)
		canvas.configure(scrollregion=canvas.bbox("all"))
		if (canvas.winfo_height() / 75) >= len(self.items):
			self.scrollbar.grid_remove()
		else:
			self.scrollbar.grid()

	def delete_record(self, oid, prev_page, *args):
		popup = tk.Toplevel()
		width, height = 140, 80
		popup.overrideredirect(1)
		popup.focus()
		popup.attributes('-topmost', True)

		# x position
		pos_x, halfwidth = 0, width//2
		if self.winfo_pointerx() >= halfwidth and self.winfo_pointerx() <= (self.winfo_screenwidth() - halfwidth):
			pos_x = self.winfo_pointerx() - halfwidth
		elif self.winfo_pointerx() >= (self.winfo_screenwidth() - halfwidth):
			pos_x = self.winfo_screenwidth() - width

		# y position
		pos_y = 0
		if self.winfo_pointery() >= (height + 20):
			pos_y = self.winfo_pointery() - 20 - height
		popup.geometry(f'{width}x{height}+{pos_x}+{pos_y}')

		# Destroy box on lost focus
		popup.bind('<FocusOut>', lambda event: popup.destroy())

		box = tk.Frame(popup, bg=BACKGROUND_DARK)
		box.pack(fill='both', expand=True)

		def delete(*args):
			self.cursor.execute(f"DELETE FROM Vault WHERE oid = '{oid}'")
			self.connection.commit()
			self.switch_view(prev_page, *args)
			popup.destroy()

		tk.Label(box, text='Are you sure?', font=(FONT, 11), bg=BACKGROUND_DARK, fg=FOREGROUND).pack(padx=8, pady=5)
		tk.Button(box, text='Delete', font=(FONT, 11), bd=0, bg=ACCENT, activebackground=ACCENT, fg=FOREGROUND, activeforeground=FOREGROUND, command=lambda:delete(*args)).pack(padx=10, ipadx=15)
		popup.mainloop()

	def view_all_items(self):
		main_viewer = tk.Frame(self.container, bg=BACKGROUND)
		main_viewer.pack(fill='both', expand=True, padx=30, pady=25)
		main_viewer.grid_columnconfigure((1, 2), weight=1)
		
		self.add_item = tk.Button(main_viewer, image=self.images['add_item_open'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=self.new_item)
		
		# Checking if any items are in database
		self.cursor.execute(f"SELECT name FROM Vault WHERE master_email = '{self.user_email}'")
		self.check_for_items = self.cursor.fetchone()
		if self.check_for_items:
			self.add_item.place(relx=1, anchor='ne', y=0)
			page_title = tk.Label(main_viewer, text='All Items', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
			page_title.grid(column=0, columnspan=5, row=0, sticky='w', padx=(0, 150))

			self.scrollbar = ttk.Scrollbar(main_viewer, orient='vertical')
			self.scrollbar.grid(column=3, row=3, sticky='nse')

			self.canvas = tk.Canvas(main_viewer, bd=0, highlightthickness=0, bg=BACKGROUND, yscrollcommand=self.scrollbar.set)
			self.canvas.grid(column=0, columnspan=3, row=3, sticky='nesw')
			main_viewer.grid_rowconfigure(3, weight=1)

			self.scrollbar.configure(command=self.canvas.yview)

			viewer = tk.Frame(self.canvas, bg=BACKGROUND)
			self.canvas.create_window((0, 0), window=viewer, anchor="nw", tags="canvas_frame")
			viewer.grid_columnconfigure((2, 3), weight=1)

			self.canvas.bind('<Configure>', lambda event: self.handle_resize(event, "canvas_frame"))
			self.canvas.bind('<Enter>', lambda event: self.canvas.bind_all('<MouseWheel>', lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')))
			self.canvas.bind('<Leave>', lambda event: self.canvas.unbind_all('<MouseWheel>'))

			def load_widgets():				
				self.image_list, row = [], 0
				for item in self.items:
					current_row = 2 * row + 1
					# Counter
					temp_frame = tk.Frame(viewer, width=30, height=25, bg=BACKGROUND)
					temp_frame.grid(row=current_row, column=0, sticky='we', padx=(5, 25))
					temp_frame.grid_propagate(0)
					temp_frame.grid_columnconfigure(0, weight=1)
					tk.Label(temp_frame, text=row+1, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11)).grid(row=0, column=0, sticky='e')
					try: 
						open(item[0], 'rb').close()
						file_image = item[0]
					except FileNotFoundError:
						file_image = os.path.join(DIRECTORY, 'images' ,'default.png')
					self.image_list.append(ImageTk.PhotoImage(Image.open(file_image).resize((50, 50))))
					tk.Label(viewer, image=self.image_list[row], bg=BACKGROUND, width=50, height=50).grid(row=current_row, column=1, sticky='w', padx=(0, 25))
					# If image is default then display first two characters from title over top
					if file_image == os.path.join(DIRECTORY, 'images', 'default.png'):
						tk.Label(viewer, text=item[1].title().replace(' ', '')[0:2], bg='#bebebe', fg='#606060', font=(FONT, 12, 'bold')).grid(row=current_row, column=1, sticky='we', padx=(9, 34))
					for n in range(0, 4, 3):
						# Create frame with maximum width so that if length of text is too big, nothing is impacted
						temp_frame = tk.Frame(viewer, width=180, height=50, bg=BACKGROUND)
						temp_frame.grid_propagate(0)
						temp_frame.grid_rowconfigure(1, weight=1)
						temp = tk.Label(temp_frame, text=item[n+1], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10)) # name
						temp.grid(row=0, column=0, sticky='nw')
						if n == 0:
							if item[4] == 'password': # identifier
								tk.Label(temp_frame, text=item[2], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9)).grid(row=1, column=0, sticky='sw')
							else:
								tk.Label(temp_frame, text="•"*12 + cypher(item[2])[12:], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9)).grid(row=1, column=0, sticky='sw')
							temp_frame.grid(row=current_row, column=2, padx=(0, 30), sticky='we')
						else:
							temp['text'] = item[4].title() # type
							temp_frame['height'] = 25
							temp_frame.grid(row=current_row, column=3, padx=(0, 30), sticky='we')

					open_record = tk.Button(viewer, image=self.images['full_view'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item: self.switch_view(f'expanded_{item[4]}', item[3], 'view_all'))
					open_record.grid(column=4, row=current_row, padx=(0, 5), sticky='e')
					delete_record = tk.Button(viewer, image=self.images['delete'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item:self.delete_record(item[3], 'view_all'))
					delete_record.grid(column=5, row=current_row, sticky='e', padx=(0, 10))

					tk.Frame(viewer, bg=BACKGROUND_DARK).grid(column=0, columnspan=5, row=current_row+1, sticky='we', pady=10) # Divider
					row += 1

			# Sorting data
			def sort_by(field, order='asc', button=None):
				self.cursor.execute(f"SELECT display_image, name, identifier, oid, type FROM Vault WHERE master_email='{self.user_email}'")
				result = self.cursor.fetchall()
				self.items = sorted(result, key=lambda result: result[3])
				if button:
					button.config(command=lambda:sort_by(field, 'desc', button))
					self.info_dir.grid_forget()
					self.type_dir.grid_forget()
					if button['text'].lower() == 'info':
						self.items = sorted(result, key=lambda result: result[1].lower())
						self.type_header['command'] = lambda:sort_by('type', 'asc', self.type_header)
						self.info_dir['image'] = self.images[f'sort_{order}']
						self.info_dir.place(in_=self.info_header, x=34, y=5)
					else:
						self.items = sorted(result, key=lambda result: result[4])
						self.info_header['command'] = lambda:sort_by('name', 'asc', self.info_header)
						self.type_dir['image'] = self.images[f'sort_{order}']
						self.type_dir.place(in_=self.type_header, x=32, y=5)
				if order == 'desc':
					self.items.reverse()
					if button:
						button.config(command=lambda:sort_by(field, 'asc', button))
				load_widgets()
			sort_by('oid')

			# Column headers
			tk.Label(main_viewer, text='#', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9, 'bold')).grid(column=0, row=1, sticky='w', padx=(22, 25), pady=(17, 0))
			self.info_header = tk.Button(main_viewer, text='INFO', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('name', 'asc', self.info_header))
			self.info_header.grid(column=1, row=1, sticky='w', pady=(17, 0))
			self.type_header = tk.Button(main_viewer, text='TYPE', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('type', 'asc', self.type_header))
			self.type_header.grid(column=2, row=1, sticky='w', padx=(0, 15), pady=(17, 0))
			tk.Frame(main_viewer, bg='grey').grid(column=0, columnspan=3, row=2, sticky='we', pady=(9, 11))
			
			# Sort indicators
			self.info_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
			self.type_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
		else:
			# If no items found, display this instead
			first_password = tk.Label(main_viewer, text='Add your first item', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 24))
			first_password.place(anchor='center', relx=.5, rely=.5, y=-30)
			self.add_item.place(anchor='center', relx=.5, rely=.5, y=+30)

	def new_item(self): # Dropdown menu
		self.dropdown_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, padx=10, pady=10)
		if self.check_for_items:
			self.dropdown_frame.place(anchor='ne', relx=1, rely=0, x=-30, y=70)
		else:
			self.dropdown_frame.place(anchor='ne', relx=.5, rely=.5, x=66, y=60)

		add_password = tk.Button(self.dropdown_frame, text='ADD PASSWORD', bg=BACKGROUND_DARK, fg=FOREGROUND, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, font=(FONT, 10), cursor='hand2', bd=0, command=lambda: self.switch_view('new_password', 'view_all'))
		add_password.grid(row=0, column=0, sticky='e')

		add_card = tk.Button(self.dropdown_frame, text='ADD CARD', bg=BACKGROUND_DARK, fg=FOREGROUND, activebackground=BACKGROUND_DARK, activeforeground=FOREGROUND, font=(FONT, 10), cursor='hand2', bd=0, command=lambda: self.switch_view('new_card', 'view_all'))
		add_card.grid(row=1, column=0, sticky='e', pady=(5,0))

		add_password.bind('<Enter>', lambda event: add_password.config(font=(FONT, 10, 'underline')))
		add_password.bind('<Leave>', lambda event: add_password.config(font=(FONT, 10)))
		add_card.bind('<Enter>', lambda event: add_card.config(font=(FONT, 10, 'underline')))
		add_card.bind('<Leave>', lambda event: add_card.config(font=(FONT, 10)))

		self.add_item.configure(image=self.images['add_item_collapse'], command=self.close_dropdown)

	def close_dropdown(self):
		self.dropdown_frame.destroy()
		self.add_item.configure(image=self.images['add_item_open'], command=self.new_item)
		
	# Passwords

	def view_passwords(self):
		main_viewer = tk.Frame(self.container, bg=BACKGROUND)
		main_viewer.pack(fill='both', expand=True, padx=30, pady=25)
		main_viewer.grid_columnconfigure((1, 2), weight=1)
		
		add_password = tk.Button(main_viewer, image=self.images['add_password'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda:self.switch_view('new_password', 'view_passwords'))
		
		# Checking if any items are in database
		self.cursor.execute(f"SELECT name FROM Vault WHERE master_email = '{self.user_email}'")
		if self.cursor.fetchone():
			add_password.place(relx=1, anchor='ne', y=0)
			page_title = tk.Label(main_viewer, text='Passwords', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
			page_title.grid(column=0, columnspan=5, row=0, sticky='w', padx=(0, 150))

			self.scrollbar = ttk.Scrollbar(main_viewer, orient='vertical')
			self.scrollbar.grid(column=3, row=3, sticky='nse')

			self.password_canvas = tk.Canvas(main_viewer, bd=0, highlightthickness=0, bg=BACKGROUND, yscrollcommand=self.scrollbar.set)
			self.password_canvas.grid(column=0, columnspan=3, row=3, sticky='nesw')
			main_viewer.grid_rowconfigure(3, weight=1)

			self.scrollbar.configure(command=self.password_canvas.yview)

			viewer = tk.Frame(self.password_canvas, bg=BACKGROUND)
			self.password_canvas.create_window((0, 0), window=viewer, anchor="nw", tags="password_canvas_frame")
			viewer.grid_columnconfigure((2, 3), weight=1)

			self.password_canvas.bind('<Configure>', lambda event: self.handle_resize(event, "password_canvas_frame"))
			self.password_canvas.bind('<Enter>', lambda event: self.password_canvas.bind_all('<MouseWheel>', lambda event: self.password_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')))
			self.password_canvas.bind('<Leave>', lambda event: self.password_canvas.unbind_all('<MouseWheel>'))

			# Load widgets
			def load_widgets():
				self.image_list, row = [], 0
				for item in self.items:
					current_row = 2 * row + 1
					# Counter
					temp_frame = tk.Frame(viewer, width=30, height=25, bg=BACKGROUND)
					temp_frame.grid(row=current_row, column=0, sticky='we', padx=(5, 25))
					temp_frame.grid_propagate(0)
					temp_frame.grid_columnconfigure(0, weight=1)
					tk.Label(temp_frame, text=row+1, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11)).grid(row=0, column=0, sticky='e')
					try: 
						open(item[0], 'rb').close()
						file_image = item[0]
					except FileNotFoundError:
						file_image = os.path.join(DIRECTORY, 'images', 'default.png')

					self.image_list.append(ImageTk.PhotoImage(Image.open(file_image).resize((50, 50))))
					tk.Label(viewer, image=self.image_list[row], bg=BACKGROUND, width=50, height=50).grid(row=current_row, column=1, sticky='w', padx=(0, 25))
					# If image is default then display first two characters from title over top
					if file_image == os.path.join(DIRECTORY, 'images', 'default.png'):
						tk.Label(viewer, text=item[1].title().replace(' ', '')[0:2], bg='#bebebe', fg='#606060', font=(FONT, 12, 'bold')).grid(row=current_row, column=1, sticky='we', padx=(9, 34))
					for n in range(2):
						# Create frame with maximum width so that if length of text is too big, nothing is impacted
						temp_frame = tk.Frame(viewer, width=180, height=25, bg=BACKGROUND)
						temp_frame.grid(row=current_row, column=n+2, padx=(0, 30), sticky='we')
						temp_frame.grid_propagate(0)
						tk.Label(temp_frame, text=item[n+1], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10)).grid(row=0, column=0, sticky='nsw')				

					open_record = tk.Button(viewer, image=self.images['full_view'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item: self.switch_view('expanded_password', item[3], 'view_passwords'))
					open_record.grid(column=4, row=current_row, padx=(0, 5), sticky='e')
					delete_record = tk.Button(viewer, image=self.images['delete'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item: self.delete_record(item[3], 'view_passwords'))
					delete_record.grid(column=5, row=current_row, sticky='e', padx=(0, 10))

					tk.Frame(viewer, bg=BACKGROUND_DARK).grid(column=0, columnspan=5, row=current_row+1, sticky='we', pady=10) # Divider
					row += 1
				
			# Retrieving data
			def sort_by(field, order='asc', button=None):
				self.cursor.execute(f"SELECT display_image, name, identifier, oid FROM Vault WHERE master_email='{self.user_email}' AND type='password'")
				result = self.cursor.fetchall()
				self.items = sorted(result, key=lambda result: result[3])
				if button:
					button.config(command=lambda:sort_by(field, 'desc', button))
					self.title_dir.place_forget()
					self.identifier_dir.place_forget()
					if button['text'].lower() == 'title':
						self.items = sorted(result, key=lambda result: result[1].lower())
						self.identifier_header['command'] = lambda:sort_by('identifier', 'asc', self.identifier_header)
						self.title_dir['image'] = self.images[f'sort_{order}']
						self.title_dir.place(in_=self.title_header, x=32, y=5)
					else:
						self.items = sorted(result, key=lambda result: result[2].lower())
						self.title_header['command'] = lambda:sort_by('name', 'asc', self.title_header)
						self.identifier_dir['image'] = self.images[f'sort_{order}']
						self.identifier_dir.place(in_=self.identifier_header, x=115, y=5)
				if order == 'desc':
					self.items.reverse()
					if button:
						button.config(command=lambda:sort_by(field, 'asc', button))
				load_widgets()
			sort_by('oid')

			# Column headers
			tk.Label(main_viewer, text='#', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9, 'bold')).grid(column=0, row=1, sticky='e', padx=(22, 25), pady=(17, 0))
			self.title_header = tk.Button(main_viewer, text='TITLE', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('name', 'asc', self.title_header))
			self.title_header.grid(column=1, row=1, sticky='w', padx=(0, 113), pady=(17, 0))
			self.identifier_header = tk.Button(main_viewer, text='USERNAME / EMAIL', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('identifier', 'asc', self.identifier_header))
			self.identifier_header.grid(column=2, row=1, sticky='w', padx=(0, 38), pady=(17, 0))
			tk.Frame(main_viewer, bg='grey').grid(column=0, columnspan=3, row=2, sticky='we', pady=(9, 11))

			# Sort indicators
			self.title_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
			self.identifier_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
		else:
			first_password = tk.Label(main_viewer, text='Add your first password', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 24))
			first_password.place(anchor='center', relx=.5, rely=.5, y=-30)
			add_password.place(anchor='center', relx=.5, rely=.5, y=+30)

	def new_password(self, prevpage):
		new_item_frame = tk.Frame(self.container, bg=BACKGROUND)
		new_item_frame.place(anchor='center', relx=.5, rely=.5)
		new_item_frame.grid_columnconfigure(1, weight=1)
		
		page_title = tk.Label(new_item_frame, text='Add New Password', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
		page_title.grid(column=0, row=0, columnspan=2, pady=(0, 30), ipadx=100)
		
		# Item icon
		self.item_image_location = os.path.join(DIRECTORY, 'images', 'default.png')
		def item_image():
			self.item_image_location = tk.filedialog.askopenfilename(title="Select Image", filetypes=(("PNG", "*.png"),("JPG", "*.jpg"),("All Files","*.*")))
			if self.item_image_location:
				self.new_image = ImageTk.PhotoImage(Image.open(self.item_image_location).resize((90, 90)))
				self.item_icon['image'] = self.new_image
				if self.letters.winfo_exists(): self.letters.destroy()

		self.item_icon = tk.Button(new_item_frame, image=self.images['default'], width=90, height=90, bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=item_image)
		self.item_icon.grid(column=0, row=1, rowspan=2, sticky='w', padx=(0, 20))
		if self.item_image_location == os.path.join(DIRECTORY, 'images', 'default.png'): # Get first two characters and display over default icon
			self.letters = tk.Button(new_item_frame, text='', bd=0, bg='#bebeb4', activebackground='#bebebe', fg='#606060', activeforeground='#606060', font=(FONT, 18, 'bold'), cursor='hand2', command=item_image)
			self.letters.grid(column=0, row=1, rowspan=2, sticky='we', padx=(14, 34), pady=(3, 0))
		
		# Item title
		def update(*args):
			self.update_check.set(self.title_input.get()[:25])
			if self.letters.winfo_exists(): self.letters['text'] = str(self.title_input.get()).title().replace(' ', '')[0:2]

		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', update) # Updates every time input changes

		title_label = tk.Label(new_item_frame, text='TITLE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		title_label.grid(column=1, row=1, sticky='w', padx=10, pady=(10,0))
		title_frame = tk.Frame(new_item_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		title_frame.grid(column=1, row=2, sticky='we')
		self.title_input = tk.Entry(title_frame, textvariable=self.update_check, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.title_input.pack(fill='both')
		
		# Item url
		platform_label = tk.Label(new_item_frame, text='WEBSITE URL  (NOT REQUIRED)', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		platform_label.grid(column=0, row=3, columnspan=2, sticky='w', padx=10, pady=(10,0))
		platform_frame = tk.Frame(new_item_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		platform_frame.grid(column=0, row=4, columnspan=2, sticky='we')
		self.platform_input = tk.Entry(platform_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.platform_input.pack(fill='both')
		
		# Item identifier (email or username)
		identifier_label = tk.Label(new_item_frame, text='USERNAME / EMAIL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		identifier_label.grid(column=0, row=5, columnspan=2, sticky='w', padx=10, pady=(10,0))
		identifier_frame = tk.Frame(new_item_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		identifier_frame.grid(column=0, row=6, columnspan=2, sticky='we')
		self.identifier_input = tk.Entry(identifier_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.identifier_input.pack(fill='both')
		
		# Item password
		password_label = tk.Label(new_item_frame, text='PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		password_label.grid(column=0, row=7, columnspan=2, sticky='w', padx=10, pady=(10,0))
		password_frame = tk.Frame(new_item_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		password_frame.grid(column=0, row=8, columnspan=2, sticky='we')
		self.password_input = tk.Entry(password_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), show='•', insertbackground=FOREGROUND, bd=0)
		self.password_input.pack(expand=True, fill='both', side='left')

		def show_password():
			self.password_input['show'] = ''
			toggle_password['image'] = self.images['visible']
			toggle_password['command'] = hide_password

		def hide_password():
			self.password_input['show'] = '•'
			toggle_password['image'] = self.images['invisible']
			toggle_password['command'] = show_password

		toggle_password = tk.Button(password_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_password)
		toggle_password.pack(padx=5, side='right')

		# Frame to evenly space buttons
		button_frame = tk.Frame(new_item_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, columnspan=2, pady=(4, 0), sticky='we')
	
		save = tk.Button(button_frame, image=self.images['save'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.save_new_password)
		save.pack(side='left')
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view(prevpage))
		back.pack(side='right')

		# Displays whether data is valid or not
		self.function_output = tk.Label(new_item_frame, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=9, columnspan=2, pady=4, padx=10, sticky='w')

	def expanded_password_view(self, oid, prev_page, *args):
		self.cursor.execute(f"SELECT display_image, name, identifier, encrypted_data, extra FROM Vault WHERE oid = '{oid}'")
		image, title, identifier, encrypted_password, platform = self.cursor.fetchone()
		password = cypher(encrypted_password)
		
		record_frame = tk.Frame(self.container, bg=BACKGROUND)
		record_frame.place(anchor='center', relx=.5, rely=.5)
		record_frame.grid_columnconfigure(1, weight=1)
		
		try: # Icon
			open(image, 'rb').close()
			file_image = image
		except FileNotFoundError:
			file_image = os.path.join(DIRECTORY, 'images', 'default.png')

		self.display_image = ImageTk.PhotoImage(Image.open(file_image).resize((100, 100)))
		item_icon = tk.Label(record_frame, image=self.display_image, width=100, height=100, bg=BACKGROUND)
		item_icon.grid(column=0, columnspan=2, row=0, sticky='we')

		if file_image == os.path.join(DIRECTORY, 'images', 'default.png'): # Get first two characters and display over default icon
			self.letters = tk.Label(record_frame, text=title.title().replace(' ', '')[0:2], bd=0, bg='#bebeb4', fg='#606060', font=(FONT, 24, 'bold'))
			self.letters.grid(column=0, columnspan=2, row=0)

		title_display = tk.Label(record_frame, text=title, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20, 'bold'))
		title_display.grid(column=0, columnspan=2, row=1, sticky='we', padx=10, pady=10)
		
		# Platform
		plat_var = tk.StringVar()
		tk.Label(record_frame, text='WEBSITE URL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=3, columnspan=2, sticky='w', padx=10, pady=(10,0))
		platform_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		platform_frame.grid(column=0, row=4, columnspan=2, sticky='we')
		platform_display = tk.Entry(platform_frame, textvariable=plat_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', bd=0)
		platform_display.pack(expand=True, fill='both', side='left')

		copy_platform = tk.Button(platform_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:threading.Thread(target=lambda:clipboard.copy(plat_var.get())).start())
		copy_platform.pack(padx=5, side='right')
		
		# Email / Username
		iden_var = tk.StringVar()
		tk.Label(record_frame, text='USERNAME / EMAIL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=5, columnspan=2, sticky='w', padx=10, pady=(10,0))
		identifier_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		identifier_frame.grid(column=0, row=6, columnspan=2, sticky='we')
		identifier_display = tk.Entry(identifier_frame, textvariable=iden_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', bd=0)
		identifier_display.pack(expand=True, fill='both', side='left')

		copy_identifier = tk.Button(identifier_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:threading.Thread(target=lambda:clipboard.copy(iden_var.get())).start())
		copy_identifier.pack(padx=5, side='right')
		
		# Password
		pass_var = tk.StringVar()
		tk.Label(record_frame, text='PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=7, columnspan=2, sticky='w', padx=10, pady=(10,0))
		password_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		password_frame.grid(column=0, row=8, columnspan=2, sticky='we')
		password_display = tk.Entry(password_frame, textvariable=pass_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', show='•', bd=0)
		password_display.pack(expand=True, fill='both', side='left')

		copy_password = tk.Button(password_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:threading.Thread(target=lambda:clipboard.copy(pass_var.get())).start())
		copy_password.pack(padx=5, side='right')

		def show_password():
			password_display['show'] = ''
			toggle_password['image'] = self.images['visible']
			toggle_password['command'] = hide_password

		def hide_password():
			password_display['show'] = '•'
			toggle_password['image'] = self.images['invisible']
			toggle_password['command'] = show_password

		toggle_password = tk.Button(password_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_password)
		toggle_password.pack(padx=5, side='right', fill='y')

		# Display Data
		plat_var.set(platform)
		if not platform:
			plat_var.set('None')
			platform_display['foreground'] = 'grey'
		iden_var.set(identifier)
		pass_var.set(password)

		button_frame = tk.Frame(record_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, columnspan=2, pady=(20, 0))
	
		edit = tk.Button(button_frame, image=self.images['edit'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view('edit_password', oid, prev_page, *args))
		edit.pack(side='left', padx=(0, 10))
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view(prev_page, *args))
		back.pack(side='right', padx=(10, 0))

	def edit_password(self, oid, prev_page, *args):
		self.cursor.execute(f"SELECT display_image, name, identifier, encrypted_data, extra FROM Vault WHERE oid = '{oid}'")
		image, title, identifier, password, platform = self.cursor.fetchone()

		edit_frame = tk.Frame(self.container, bg=BACKGROUND)
		edit_frame.place(anchor='center', relx=.5, rely=.5)
		edit_frame.grid_columnconfigure(1, weight=1)
		
		page_title = tk.Label(edit_frame, text='Edit Password', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
		page_title.grid(column=0, row=0, columnspan=2, pady=(0, 30), ipadx=135)
		
		# Item icon
		self.item_image_location = image
		def item_image():
			self.item_image_location = tk.filedialog.askopenfilename(title="Select Image", filetypes=(("PNG", "*.png"),("JPG", "*.jpg"),("All Files","*.*")))
			if self.item_image_location != '':
				self.new_image = ImageTk.PhotoImage(Image.open(self.item_image_location).resize((90, 90)))
				self.item_icon['image'] = self.new_image
				if self.letters.winfo_exists(): self.letters.destroy()
		try:
			open(image, 'rb').close()
			file_image = image
		except:
			file_image = os.path.join(DIRECTORY, 'images', 'default.png')
		self.display_image = ImageTk.PhotoImage(Image.open(file_image).resize((90, 90)))
		self.item_icon = tk.Button(edit_frame, image=self.display_image, width=90, height=90, bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=item_image)
		self.item_icon.grid(column=0, row=1, rowspan=2, sticky='w', padx=(0, 20))
		if file_image == os.path.join(DIRECTORY, 'images', 'default.png'):
			self.letters = tk.Button(edit_frame, text='', bd=0, bg='#bebeb4', activebackground='#bebebe', fg='#606060', activeforeground='#606060', font=(FONT, 18, 'bold'), cursor='hand2', command=item_image)
			self.letters.grid(column=0, row=1, rowspan=2, sticky='we', padx=(14, 34), pady=(3, 0))
		
		# Item title
		def update(*args):
			self.update_check.set(self.title_input.get()[:25]) 
			if not self.letters.winfo_exists(): self.letters['text'] = str(self.title_input.get()).title().replace(' ', '')[0:2]

		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', update) # Updates every time input changes

		tk.Label(edit_frame, text='TITLE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=1, row=1, sticky='w', padx=10, pady=(10,0))
		title_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		title_frame.grid(column=1, row=2, sticky='we')
		self.title_input = tk.Entry(title_frame, textvariable=self.update_check, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.title_input.insert(0, title)
		self.title_input.pack(fill='both')
		
		# Item url
		tk.Label(edit_frame, text='WEBSITE URL  (NOT REQUIRED)', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=3, columnspan=2, sticky='w', padx=10, pady=(10,0))
		platform_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		platform_frame.grid(column=0, row=4, columnspan=2, sticky='we')
		self.platform_input = tk.Entry(platform_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.platform_input.insert(0, platform)
		self.platform_input.pack(fill='both', expand=True, side='right')
		
		# Item identifier (email or username)
		tk.Label(edit_frame, text='USERNAME / EMAIL', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=5, columnspan=2, sticky='w', padx=10, pady=(10,0))
		identifier_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		identifier_frame.grid(column=0, row=6, columnspan=2, sticky='we')
		self.identifier_input = tk.Entry(identifier_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.identifier_input.insert(0, identifier)
		self.identifier_input.pack(fill='both')
		
		# Item password
		tk.Label(edit_frame, text='PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=7, columnspan=2, sticky='w', padx=10, pady=(10,0))
		password_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		password_frame.grid(column=0, row=8, columnspan=2, sticky='we')
		self.password_input = tk.Entry(password_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), show='•', insertbackground=FOREGROUND, bd=0)
		self.password_input.insert(0, cypher(password))
		self.password_input.pack(expand=True, fill='both', side='left')

		def show_password():
			self.password_input['show'] = ''
			toggle_password['image'] = self.images['visible']
			toggle_password['command'] = hide_password

		def hide_password():
			self.password_input['show'] = '•'
			toggle_password['image'] = self.images['invisible']
			toggle_password['command'] = show_password

		toggle_password = tk.Button(password_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_password)
		toggle_password.pack(padx=5, side='right')

		button_frame = tk.Frame(edit_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, columnspan=2, pady=(4, 0), sticky='we')
	
		save = tk.Button(button_frame, image=self.images['save'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.save_password_changes(prev_page, oid, self.item_image_location, self.title_input.get(), self.platform_input.get(), self.identifier_input.get(), self.password_input.get(), *args))
		save.pack(side='left')
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view('expanded_password', oid, prev_page, *args))
		back.pack(side='right')

		# Displays whether data is valid or not
		self.function_output = tk.Label(edit_frame, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=9, columnspan=2, pady=4, padx=10, sticky='w')

	def save_password_changes(self, prev_page, oid, display_image, title, platform, identifier, password, *args):
		if title and identifier and password:
			self.cursor.execute(f"UPDATE Vault SET type = ?, display_image = ?, name = ?, identifier = ?, encrypted_data = ?, extra = ? WHERE oid = ?", ('password', display_image, title, identifier, cypher(password), platform, oid))
			self.connection.commit()
			self.switch_view('expanded_password', oid, prev_page, *args)
		else:
			self.function_output['text'] = '* Please provide valid data.'
	
	# Cards
	
	def view_cards(self):
		main_viewer = tk.Frame(self.container, bg=BACKGROUND)
		main_viewer.pack(fill='both', expand=True, padx=30, pady=25)
		main_viewer.grid_columnconfigure(1, weight=1)
		main_viewer.grid_columnconfigure(2, weight=1)
		
		add_card = tk.Button(main_viewer, image=self.images['add_card'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda:self.switch_view('new_card', 'view_cards'))
		
		# Checking if any items are in database
		self.cursor.execute(f"SELECT name FROM Vault WHERE master_email = '{self.user_email}' AND type = 'card'")
		check_for_items = self.cursor.fetchone()

		if check_for_items:
			add_card.place(relx=1, anchor='ne', y=0)
			page_title = tk.Label(main_viewer, text='Cards', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
			page_title.grid(column=0, columnspan=5, row=0, sticky='w', padx=(0, 150))

			self.scrollbar = ttk.Scrollbar(main_viewer, orient='vertical')
			self.scrollbar.grid(column=3, row=3, sticky='nse')

			self.card_canvas = tk.Canvas(main_viewer, bd=0, highlightthickness=0, bg=BACKGROUND, yscrollcommand=self.scrollbar.set)
			self.card_canvas.grid(column=0, columnspan=3, row=3, sticky='nesw')
			main_viewer.grid_rowconfigure(3, weight=1)

			self.scrollbar.configure(command=self.card_canvas.yview)

			viewer = tk.Frame(self.card_canvas, bg=BACKGROUND)
			self.card_canvas.create_window((0, 0), window=viewer, anchor="nw", tags="card_canvas_frame")
			self.card_canvas.bind('<Configure>', lambda event: self.handle_resize(event, "card_canvas_frame"))
			self.card_canvas.bind('<Enter>', lambda event: self.card_canvas.bind_all('<MouseWheel>', lambda event: self.card_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')))
			self.card_canvas.bind('<Leave>', lambda event: self.card_canvas.unbind_all('<MouseWheel>'))

			viewer.grid_columnconfigure((2, 3), weight=1)
			
			def load_widgets():
				row = 0
				for item in self.items:
					current_row = 2 * row + 1 # Multiplied by two to allow space for divider
					# Counter
					temp_frame = tk.Frame(viewer, width=30, height=25, bg=BACKGROUND)
					temp_frame.grid(row=current_row, column=0, sticky='we', padx=(5, 25))
					temp_frame.grid_propagate(0)
					temp_frame.grid_columnconfigure(0, weight=1)
					tk.Label(temp_frame, text=row+1, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11)).grid(row=0, column=0, sticky='e')

					tk.Label(viewer, image=self.images['card_view_icon'], bg=BACKGROUND, width=50, height=50).grid(row=current_row, column=1, sticky='w', padx=(0, 25))
					# Loop to create labels
					for n in range(2):
						# Create frame with maximum width so that if length of text is too big, nothing is impacted
						temp_frame = tk.Frame(viewer, width=180, height=25, bg=BACKGROUND)
						temp_frame.grid(row=current_row, column=n+2, padx=(0, 30), sticky='we')
						temp_frame.grid_propagate(0)
						if n == 0:
							tk.Label(temp_frame, text=item[n], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10)).grid(row=0, column=0, sticky='nsw')
						else:
							tk.Label(temp_frame, text="•"*12 + cypher(item[n])[12:], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10)).grid(row=0, column=0, sticky='nsw')
					# Open, delete butons
					open_record = tk.Button(viewer, image=self.images['full_view'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item:self.switch_view('expanded_card', item[2], 'view_cards'))
					open_record.grid(column=4, row=current_row, padx=(0, 5), sticky='e')
					delete_record = tk.Button(viewer, image=self.images['delete'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item:self.delete_record(item[2], 'view_cards'))
					delete_record.grid(column=5, row=current_row, sticky='e', padx=(0, 10))

					tk.Frame(viewer, bg=BACKGROUND_DARK).grid(column=0, columnspan=5, row=current_row+1, sticky='we', pady=10) # Divider
					row += 1
			
			# Retrieving data
			def sort_by(field, order='asc', button=None):
				self.cursor.execute(f"SELECT name, identifier, oid FROM Vault WHERE master_email='{self.user_email}' AND type='card'")
				result = self.cursor.fetchall()
				self.items = sorted(result, key=lambda result: result[2])
				if button:
					button.config(command=lambda:sort_by(field, 'desc', button))
					self.items = sorted(result, key=lambda result: result[0].lower())
					self.cardholder_dir['image'] = self.images[f'sort_{order}']
					self.cardholder_dir.place(in_=self.cardholder_header, x=80, y=5)
				if order == 'desc':
					self.items.reverse()
					if button:
						button.config(command=lambda:sort_by(field, 'asc', button))
				load_widgets()
			sort_by('oid')

			# Column headers
			tk.Label(main_viewer, text='#', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9, 'bold')).grid(column=0, row=1, sticky='w', padx=(22, 24), pady=(17, 0))
			self.cardholder_header = tk.Button(main_viewer, text='CARDHOLDER', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('name', 'asc', self.cardholder_header))
			self.cardholder_header.grid(column=1, row=1, sticky='w', pady=(17, 0))
			card_num_header = tk.Label(main_viewer, text='CARD NUMBER', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9, 'bold'))
			card_num_header.grid(column=2, row=1, sticky='w', padx=(0, 3), pady=(18, 0))
			tk.Frame(main_viewer, bg='grey').grid(column=0, columnspan=3, row=2, sticky='we', pady=(9, 11)) # Divider

			# Sort indicators
			self.cardholder_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
		else:
			# If no items found, display this instead
			first_card = tk.Label(main_viewer, text='Add your first card', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 24))
			first_card.place(anchor='center', relx=.5, rely=.5, y=-30)
			add_card.place(anchor='center', relx=.5, rely=.5, y=+30)
	
	def new_card(self, prevpage):
		new_card_frame = tk.Frame(self.container, bg=BACKGROUND)
		new_card_frame.place(anchor='center', relx=.5, rely=.5)
		new_card_frame.grid_columnconfigure((0, 1), weight=1)
		
		page_title = tk.Label(new_card_frame, text='Add New Card', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
		page_title.grid(column=0, row=0, pady=(0, 30), ipadx=130)
		
		# Item cardholder
		tk.Label(new_card_frame, text='CARDHOLDER NAME', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=1, sticky='w', padx=10, pady=(10,0))
		cardholder_frame = tk.Frame(new_card_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		cardholder_frame.grid(column=0, row=2, sticky='we')
		self.cardholder_input = tk.Entry(cardholder_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.cardholder_input.pack(fill='both')
		
		# Item card number
		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', lambda *args:self.update_check.set(self.card_num_input.get()[:16]))

		tk.Label(new_card_frame, text='CARD NUMBER', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=3, sticky='w', padx=10, pady=(10,0))
		card_num_frame = tk.Frame(new_card_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		card_num_frame.grid(column=0, row=4, sticky='we')
		self.card_num_input = tk.Entry(card_num_frame, show='•', textvariable=self.update_check, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.card_num_input.pack(expand=True, fill='both', side='left')
		
		# Item expiration date
		tk.Label(new_card_frame, text='EXPIRY DATE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=5, sticky='w', padx=10, pady=(10,0))
		expiry_frame = tk.Frame(new_card_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		expiry_frame.grid(column=0, row=6, sticky='we')
		self.expiry_input = tk.Entry(expiry_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.expiry_input.pack(fill='both')
		
		# Item cvv
		tk.Label(new_card_frame, text='CVV', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=7, sticky='w', padx=10, pady=(10,0))
		cvv_frame = tk.Frame(new_card_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		cvv_frame.grid(column=0, row=8, sticky='we')
		self.cvv_input = tk.Entry(cvv_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.cvv_input.pack(fill='both')

		def show_card_num():
			self.card_num_input['show'] = ''
			toggle_card_num['image'] = self.images['visible']
			toggle_card_num['command'] = hide_card_num

		def hide_card_num():
			self.card_num_input['show'] = '•'
			toggle_card_num['image'] = self.images['invisible']
			toggle_card_num['command'] = show_card_num

		toggle_card_num = tk.Button(card_num_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_card_num)
		toggle_card_num.pack(padx=5, side='right')

		# Frame to evenly space buttons
		button_frame = tk.Frame(new_card_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, pady=(4, 0), sticky='we')
	
		save = tk.Button(button_frame, image=self.images['save'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.save_new_card)
		save.pack(side='left')
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view(prevpage))
		back.pack(side='right')

		# Displays whether data is valid or not
		self.function_output = tk.Label(new_card_frame, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=9, pady=4, padx=10, sticky='w')

	def expanded_card_view(self, oid, prev_page, *args):
		self.cursor.execute(f"SELECT display_image, name, identifier, encrypted_data, extra FROM Vault WHERE oid = '{oid}'")
		image, cardholder, card_number, cvv, expiry_date = self.cursor.fetchone()
		card_number = cypher(card_number)
		cvv = cypher(cvv)
		
		record_frame = tk.Frame(self.container, bg=BACKGROUND)
		record_frame.place(anchor='center', relx=.5, rely=.5)
		record_frame.grid_columnconfigure(1, weight=1)
		
		def copy(var): 
			threading.Thread(target=lambda:clipboard.copy(var.get())).start()
		
		# Icon
		self.display_image = ImageTk.PhotoImage(Image.open(image).resize((100, 100)))
		item_icon = tk.Label(record_frame, image=self.display_image, width=100, height=100, bg=BACKGROUND)
		item_icon.grid(column=0, columnspan=2, row=0, sticky='we')

		cardholder_display = tk.Label(record_frame, text=cardholder, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20, 'bold'))
		cardholder_display.grid(column=0, columnspan=2, row=1, sticky='we', padx=10, pady=10)
		
		# Platform
		num_var = tk.StringVar(value=card_number)
		card_num_label = tk.Label(record_frame, text='CARD NUMBER', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		card_num_label.grid(column=0, row=3, columnspan=2, sticky='w', padx=10, pady=(10,0))
		card_num_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		card_num_frame.grid(column=0, row=4, columnspan=2, sticky='we')
		card_num_display = tk.Entry(card_num_frame, textvariable=num_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', show='•', bd=0)
		card_num_display.pack(expand=True, fill='both', side='left')

		copy_card_num = tk.Button(card_num_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:copy(num_var))
		copy_card_num.pack(padx=5, side='right')

		def show_card_num():
			card_num_display['show'] = ''
			toggle_card_num['image'] = self.images['visible']
			toggle_card_num['command'] = hide_card_num

		def hide_card_num():
			card_num_display['show'] = '•'
			toggle_card_num['image'] = self.images['invisble']
			toggle_card_num['command'] = show_card_num

		toggle_card_num = tk.Button(card_num_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_card_num)
		toggle_card_num.pack(padx=5, side='right', fill='y')
		
		# Email / Username
		exp_var = tk.StringVar(value=expiry_date)
		expiry_label = tk.Label(record_frame, text='EXPIRY DATE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		expiry_label.grid(column=0, row=5, columnspan=2, sticky='w', padx=10, pady=(10,0))
		expiry_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		expiry_frame.grid(column=0, row=6, columnspan=2, sticky='we')
		expiry_display = tk.Entry(expiry_frame, textvariable=exp_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', bd=0)
		expiry_display.pack(expand=True, fill='both', side='left')

		copy_expiry = tk.Button(expiry_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:copy(exp_var))
		copy_expiry.pack(padx=5, side='right')
		
		# Password
		cvv_var = tk.StringVar(value=cvv)
		cvv_label = tk.Label(record_frame, text='CVV', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold'))
		cvv_label.grid(column=0, row=7, columnspan=2, sticky='w', padx=10, pady=(10,0))
		cvv_frame = tk.Frame(record_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
		cvv_frame.grid(column=0, row=8, columnspan=2, sticky='we')
		cvv_display = tk.Entry(cvv_frame, textvariable=cvv_var, readonlybackground=BACKGROUND_DARK, foreground=FOREGROUND, font=(FONT, 12), state='readonly', bd=0)
		cvv_display.pack(expand=True, fill='both', side='left')

		copy_cvv = tk.Button(cvv_frame, image=self.images['copy_small'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:copy(cvv_var))
		copy_cvv.pack(padx=5, side='right')

		# Frame to evenly space buttons
		button_frame = tk.Frame(record_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, columnspan=2, pady=(20, 0))
	
		edit = tk.Button(button_frame, image=self.images['edit'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view('edit_card', oid, prev_page, *args))
		edit.pack(side='left', padx=(0, 10))
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view(prev_page, *args))
		back.pack(side='right', padx=(10, 0))

	def edit_card(self, oid, prev_page, *args):
		self.cursor.execute(f"SELECT name, identifier, encrypted_data, extra FROM Vault WHERE oid = '{oid}'")
		cardholder, card_number, cvv, expiry_date = self.cursor.fetchone()
		card_number = cypher(card_number)
		cvv = cypher(cvv)

		edit_frame = tk.Frame(self.container, bg=BACKGROUND)
		edit_frame.place(anchor='center', relx=.5, rely=.5)
		edit_frame.grid_columnconfigure(0, weight=1)
		
		page_title = tk.Label(edit_frame, text='Edit Card', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
		page_title.grid(column=0, row=0, pady=(0, 30), ipadx=170)
		
		# Item cardholder
		tk.Label(edit_frame, text='CARDHOLDER NAME', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=1, sticky='w', padx=10, pady=(10,0))
		cardholder_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		cardholder_frame.grid(column=0, row=2, sticky='we')
		self.cardholder_input = tk.Entry(cardholder_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.cardholder_input.insert(0, cardholder)
		self.cardholder_input.pack(fill='both')
		
		# Item card number
		self.update_check = tk.StringVar()
		self.update_check.trace_add('write', lambda *args:self.update_check.set(self.card_num_input.get()[:16]))

		tk.Label(edit_frame, text='CARD NUMBER', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=3, sticky='w', padx=10, pady=(10,0))
		card_num_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		card_num_frame.grid(column=0, row=4, sticky='we')
		self.card_num_input = tk.Entry(card_num_frame, show='•', textvariable=self.update_check, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.card_num_input.insert(0, card_number)
		self.card_num_input.pack(expand=True, fill='both', side='left')
		
		# Item expiration date
		tk.Label(edit_frame, text='EXPIRY DATE', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=5, sticky='w', padx=10, pady=(10,0))
		expiry_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		expiry_frame.grid(column=0, row=6, sticky='we')
		self.expiry_input = tk.Entry(expiry_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.expiry_input.insert(0, expiry_date)
		self.expiry_input.pack(fill='both')
		
		# Item cvv
		tk.Label(edit_frame, text='CVV', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=7, sticky='w', padx=10, pady=(10,0))
		cvv_frame = tk.Frame(edit_frame, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor=FOREGROUND, highlightthickness=1)
		cvv_frame.grid(column=0, row=8, sticky='we')
		self.cvv_input = tk.Entry(cvv_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.cvv_input.insert(0, cvv)
		self.cvv_input.pack(fill='both')

		def show_card_num():
			self.card_num_input['show'] = ''
			toggle_card_num['image'] = self.images['visible']
			toggle_card_num['command'] = hide_card_num

		def hide_card_num():
			self.card_num_input['show'] = '•'
			toggle_card_num['image'] = self.images['invisible']
			toggle_card_num['command'] = show_card_num

		toggle_card_num = tk.Button(card_num_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=show_card_num)
		toggle_card_num.pack(padx=5, side='right')

		# Frame to evenly space buttons
		button_frame = tk.Frame(edit_frame, bg=BACKGROUND)
		button_frame.grid(column=0, row=10, columnspan=2, pady=(4, 0), sticky='we')
	
		save = tk.Button(button_frame, image=self.images['save'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.save_card_changes(prev_page, oid, self.card_num_input.get(), self.expiry_input.get(), self.cvv_input.get(), self.cardholder_input.get(), *args))
		save.pack(side='left')
		back = tk.Button(button_frame, image=self.images['back'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.switch_view('expanded_card', oid, prev_page, *args))
		back.pack(side='right')

		# Displays whether data is valid or not
		self.function_output = tk.Label(edit_frame, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=9, columnspan=2, pady=4, padx=10, sticky='w')

	def save_card_changes(self, prev_page, oid, card_number, expiry_date, cvv, cardholder, *args):
		if not card_number.isdigit():
			self.function_output['text'] = '* Card number must be an integer.'
			return False
		if cardholder and expiry_date and cvv: # If boxes are not empty
			if len(card_number) == 16:
				self.cursor.execute(f"UPDATE Vault SET type = ?, display_image = ?, name = ?, identifier = ?, encrypted_data = ?, extra = ? WHERE oid = ?", ('card', 'images/card_view_icon.png', cardholder, cypher(card_number), cypher(cvv), expiry_date, oid))
				self.connection.commit()
				self.switch_view('expanded_card', oid, prev_page, *args)
			else:
				self.function_output['text'] = '* Card number must be 16 digits.'
		else:
			self.function_output['text'] = '* Please provide valid data.'

	# General Functions

	def logout(self):		
		file = open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w')
		config = {'data': None,
				'window_width': self.width,
				'window_height': self.height}
		json.dump(config, file) # Saving config
		file.close()

		self.destroy()
		login.LoginWindow().mainloop()

	def refresh(self, pfp_dir, username):
		self.image_pfp = ImageTk.PhotoImage(Image.open(pfp_dir).resize((32, 32)))
		self.user_icon.config(image=self.image_pfp)
		self.user_welcome['text'] = f'Hello, {username}'
		for index in range(len(username), 0, -1):
			if self.user_welcome.winfo_reqwidth() > 175: # If length of username excedes maximum length, only display visible characters
				displayed_user = username[0:index]
				self.user_welcome['text'] = f'Hello, {displayed_user}...'
			else: break

	def search(self, query, field) -> list:
		self.cursor.execute(f"SELECT oid, type, display_image, name, identifier, encrypted_data, extra FROM Vault WHERE master_email = '{self.user_email}' ORDER by {field}")
		items = self.cursor.fetchall()
		array = []
		for item in items:
			item = list(item)
			item[5] = cypher(item[5])
			if item[1] == 'card':
				item[4] = cypher(item[4])
			item = tuple(item)
			for text in item[3:]:
				if (text and query) and (query.lower() in text.lower()):
					array.append((item[2], item[3], item[4], item[0], item[1]))
					break
		return array

	def view_search_results(self, query):
		item_check = self.search(query, 'oid')

		main_viewer = tk.Frame(self.container, bg=BACKGROUND)
		main_viewer.pack(fill='both', expand=True, padx=30, pady=25)
		main_viewer.grid_columnconfigure((1, 2), weight=1)

		if item_check:
			page_title = tk.Label(main_viewer, text=f'Search Results For "{query[:12] + "..." if len(query) > 14 else query}"', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 20))
			page_title.grid(column=0, columnspan=5, row=0, sticky='w')

			# Canvas for records so they are able to be scrolled
			self.scrollbar = ttk.Scrollbar(main_viewer, orient='vertical')
			self.scrollbar.grid(column=3, row=3, sticky='nse')

			self.canvas = tk.Canvas(main_viewer, bd=0, highlightthickness=0, bg=BACKGROUND, yscrollcommand=self.scrollbar.set)
			self.canvas.grid(column=0, columnspan=3, row=3, sticky='nesw')
			main_viewer.grid_rowconfigure(3, weight=1)

			self.scrollbar.configure(command=self.canvas.yview)

			viewer = tk.Frame(self.canvas, bg=BACKGROUND)
			self.canvas.create_window((0, 0), window=viewer, anchor="nw", tags="results_canvas_frame")
			self.canvas.bind('<Configure>', lambda event: self.handle_resize(event, "results_canvas_frame"))
			self.canvas.bind('<Enter>', lambda event: self.canvas.bind_all('<MouseWheel>', lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')))
			self.canvas.bind('<Leave>', lambda event: self.canvas.unbind_all('<MouseWheel>'))

			viewer.grid_columnconfigure((2, 3), weight=1)

			def load_widgets(search_results):
				self.image_list, row = [], 0
				for item in search_results:
					current_row = 2 * row + 1
					# Counter
					temp_frame = tk.Frame(viewer, width=30, height=25, bg=BACKGROUND)
					temp_frame.grid(row=current_row, column=0, sticky='we', padx=(5, 25))
					temp_frame.grid_propagate(0)
					temp_frame.grid_columnconfigure(0, weight=1)
					tk.Label(temp_frame, text=row+1, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11)).grid(row=0, column=0, sticky='e')
					try: 
						open(item[0], 'rb').close()
						file_image = item[0]
					except FileNotFoundError:
						file_image = os.path.join(DIRECTORY, 'images', 'default.png')
					self.image_list.append(ImageTk.PhotoImage(Image.open(file_image).resize((50, 50))))
					tk.Label(viewer, image=self.image_list[row], bg=BACKGROUND, width=50, height=50).grid(row=current_row, column=1, sticky='w', padx=(0, 25))
					# If image is default then display first two characters from title over top
					if file_image == os.path.join(DIRECTORY, 'images', 'default.png'):
						tk.Label(viewer, text=item[1].title().replace(' ', '')[0:2], bg='#bebebe', fg='#606060', font=(FONT, 12, 'bold')).grid(row=current_row, column=1, sticky='we', padx=(9, 34))
					for n in range(0, 4, 3):
						# Create frame with maximum width so that if length of text is too big, nothing is impacted
						temp_frame = tk.Frame(viewer, width=180, height=50, bg=BACKGROUND)
						temp_frame.grid_propagate(0)
						temp_frame.grid_rowconfigure(1, weight=1)
						temp = tk.Label(temp_frame, text=item[n+1], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 10))
						temp.grid(row=0, column=0, sticky='nw')
						if n == 0:
							if item[4] == 'password':
								tk.Label(temp_frame, text=item[n+2], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9)).grid(row=1, column=0, sticky='sw')
							else:
								tk.Label(temp_frame, text="•"*12 + item[n+2][12:], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9)).grid(row=1, column=0, sticky='sw')
							temp_frame.grid(row=current_row, column=2, padx=(0, 30), sticky='we')
						else:
							temp['text'] = item[n+1].title()
							temp_frame['height'] = 25
							temp_frame.grid(row=current_row, column=3, padx=(0, 30), sticky='we')
					def expand(item): # Full view of individual record
						if item[4] == 'password':
							self.switch_view('expanded_password', item[3], 'search_results', query)
						else:
							self.switch_view('expanded_card', item[3], 'search_results', query)
					def delete(item):
						search_results.remove(item)
						self.delete_record(item[3], 'search_results', query)

					# Open, delete butons
					open_record = tk.Button(viewer, image=self.images['full_view'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item:expand(item))
					open_record.grid(column=4, row=current_row, padx=(0, 5), sticky='e')
					delete_record = tk.Button(viewer, image=self.images['delete'], bd=0, bg=BACKGROUND, activebackground=BACKGROUND, cursor='hand2', command=lambda item=item: delete(item))
					delete_record.grid(column=5, row=current_row, sticky='e', padx=(0, 10))

					tk.Frame(viewer, bg=BACKGROUND_DARK).grid(column=0, columnspan=5, row=current_row+1, sticky='we', pady=10) # Divider
					row += 1
			
			# Retrieving data
			def sort_by(field, order='asc', button=None):
				search_results = self.search(query, field)
				search_results.sort(key=lambda search_results: search_results[3])
				if button:
					button.config(command=lambda:sort_by(field, 'desc', button))
					self.info_dir.place_forget()
					self.type_dir.place_forget()
					if button['text'].lower() == 'info':
						search_results.sort(key=lambda search_results: search_results[1].lower())
						self.type_header['command'] = lambda:sort_by('type', 'asc', self.type_header)
						self.info_dir['image'] = self.images[f'sort_{order}']
						self.info_dir.place(in_=self.info_header, x=34, y=5)
					else:
						search_results.sort(key=lambda search_results: search_results[4])
						self.info_header['command'] = lambda:sort_by('name', 'asc', self.info_header)
						self.type_dir['image'] = self.images[f'sort_{order}']
						self.type_dir.place(in_=self.type_header, x=32, y=5)
				if order == 'desc':
					search_results.reverse()
					if button:
						button.config(command=lambda:sort_by(field, 'asc', button))
				load_widgets(search_results)
			sort_by('oid')

			# Column headers
			tk.Label(main_viewer, text='#', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 9, 'bold')).grid(column=0, row=1, sticky='w', padx=(22, 25), pady=(17, 0))
			self.info_header = tk.Button(main_viewer, text='INFO', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('name', 'asc', self.info_header))
			self.info_header.grid(column=1, row=1, sticky='w', pady=(17, 0))
			self.type_header = tk.Button(main_viewer, text='TYPE', bg=BACKGROUND, fg=FOREGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND, font=(FONT, 9, 'bold'), bd=0, cursor='hand2', command=lambda:sort_by('type', 'asc', self.type_header))
			self.type_header.grid(column=2, row=1, sticky='w', padx=(0, 15), pady=(17, 0))
			tk.Frame(main_viewer, bg='grey').grid(column=0, columnspan=3, row=2, sticky='we', pady=(9, 11))

			# Sort indicators
			self.info_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
			self.type_dir = tk.Label(image=self.images['sort_asc'], bg=BACKGROUND, fg=FOREGROUND)
		else:
			# If no items found, display this instead
			no_result = tk.Label(main_viewer, text='No items found.', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 24))
			no_result.place(anchor='center', relx=.5, rely=.5)

	def save_new_password(self):
		if self.title_input.get() and self.identifier_input.get() and self.password_input.get(): # If boxes are not empty
			encrypted_password = cypher(self.password_input.get())
			data = [self.user_email, self.item_image_location, self.title_input.get(), self.identifier_input.get(), encrypted_password, self.platform_input.get()]
			self.cursor.execute("INSERT INTO Vault VALUES(?, 'password', ?, ?, ?, ?, ?)", data)
			self.connection.commit()
			self.function_output['text'] = '* Item has been successfully added.'
		else:
			self.function_output['text'] = '* Please fill all required fields.'

	def save_new_card(self):
		if not self.card_num_input.get().isdigit():
			self.function_output['text'] = '* Card number must be an integer.'
			return False
		if self.expiry_input.get() and self.cvv_input.get() and self.cardholder_input.get(): # If boxes are not empty
			if len(self.card_num_input.get()) == 16:
				data = [self.user_email, os.path.join(DIRECTORY, 'images', 'card_view_icon.png'), self.cardholder_input.get(), cypher(self.card_num_input.get()), cypher(self.cvv_input.get()), self.expiry_input.get()]
				self.cursor.execute("INSERT INTO Vault VALUES(?, 'card', ?, ?, ?, ?, ?)", data)
				self.connection.commit()
				self.function_output['text'] = '* Item has been successfully added.'
			else:
				self.function_output['text'] = '* Card number must be 16 digits.'
		else:
			self.function_output['text'] = '* Please fill all fields.'

if __name__ == '__main__':
	user = init_user()
	cursor, connection = init_database()
	cursor.execute(f"SELECT oid FROM Users WHERE email = '{user}'")
	result = cursor.fetchall()
	connection.close()

	if user and result:
		PasswordManager(user).mainloop()
	else:
		login.LoginWindow().mainloop()