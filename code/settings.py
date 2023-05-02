import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import bcrypt, json, os

from support import *

class Settings(tk.Toplevel):
	def __init__(self, master, user_email):
		super().__init__()

		# General
		self.master = master
		self.title('User Settings')
		self.iconbitmap(os.path.join(DIRECTORY, 'icon.ico'))
		self.geometry(f'500x700+{int(self.winfo_screenwidth()/2-250)}+{int(self.winfo_screenheight()/2-400)}')
		self.resizable(False, False)

		# Load images
		self.images = import_images(os.path.join(DIRECTORY, 'images', ''))
		for key, value in self.images.items():
			self.images[key] = ImageTk.PhotoImage(Image.open(value))

		# Get user
		self.user_email = user_email
		self.cursor, self.connection = init_database()
		self.cursor.execute(f"SELECT oid, profile_picture, username FROM Users WHERE email = '{self.user_email}'")
		result = self.cursor.fetchone()
		if result:	
			self.oid, self.user_image, self.username = result

		self.container = tk.Frame(self)
		self.container.pack()
		self.change_page('settings')

	def change_page(self, page, *args):
		self.container.destroy()
		self.container = tk.Frame(self, bg=BACKGROUND, padx=30, pady=5)
		self.container.pack(expand=True, fill='both')
		pages = {'settings': self.settings,
				'change_password': self.change_password_page}
		pages[page](*args)	

	def check_password(self):
		self.window = tk.Toplevel()
		self.window.iconbitmap(os.path.join(DIRECTORY, 'icon.ico'))
		self.window.title('Enter Password')
		self.window.geometry(f'350x150+{int(self.winfo_screenwidth()//2-175)}+{int(self.winfo_screenheight()//2-125)}')
		self.window.wm_transient(self)
		self.window.resizable(False, False)
		self.window.config(background=BACKGROUND)

		def check():
			self.cursor.execute(f"SELECT password from users WHERE email='{self.user_email}'")
			hashed_password = self.cursor.fetchone()[0]
			
			if bcrypt.checkpw(self.pass_input.get().encode('utf-8'), hashed_password.encode('utf-8')): # If password is correct
				self.user_email = self.email.get()
				self.cursor.execute(f"UPDATE Vault SET master_email = ? WHERE master_email = ?", (self.user_email, self.master.user_email))
				self.connection.commit()
				self.cursor.execute(f"UPDATE Users SET email = ? WHERE oid = ?", (self.user_email, self.oid))
				self.connection.commit()
				with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'r') as file:
					config = json.load(file)
				with open(os.path.join(DIRECTORY, 'data', 'config.json'), 'w') as file:
					if config['data'] != None: 
						config['data'] = cypher(self.user_email)
					json.dump(config, file)
				self.master.user_email = self.user_email
				self.window.destroy()
			else:
				tk.Label(self.window, bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'), text='* Password is incorrect.').grid(column=0, row=2, sticky='w', padx=10)
				return False

		tk.Label(self.window, text='ENTER PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=0, sticky='w', padx=10, pady=(10, 0))
		pass_frame = tk.Frame(self.window, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		pass_frame.grid(column=0, row=1, padx=10, pady=5, sticky='we')
		self.pass_input = tk.Entry(pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, width=30, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
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

		tk.Button(self.window, text='E N T E R', bg=ACCENT, fg=FOREGROUND, activebackground=ACCENT, activeforeground=FOREGROUND, bd=0, font=(FONT, 12, 'bold'), cursor='hand2', command=check).grid(column=0, row=3, sticky='we', ipady=4, padx=10, pady=(5, 10))

		self.window.mainloop()

	def settings(self):
		self.container.config(padx=30, pady=5)
		self.container.grid_columnconfigure(1, weight=1)

		# Profile Picture
		tk.Frame(self.container, bg='#454758').grid(row=0, column=0, columnspan=3, sticky='we', pady=20)
		tk.Label(self.container, text='Profile Picture ', font=(FONT, 14), bg=BACKGROUND, fg=FOREGROUND).grid(row=0, column=0, columnspan=3, sticky='w', pady=20)
		
		self.image_default_user_big = ImageTk.PhotoImage(Image.open(self.user_image).resize((100, 100)))
		self.profilepic = tk.Label(self.container, image=self.image_default_user_big, width=100, height=100, bg=BACKGROUND, activebackground=BACKGROUND, bd=0)
		self.profilepic.grid(row=1, column=0, rowspan=2, sticky='w', padx=(0, 25))

		inputframe = tk.Frame(self.container, bg=BACKGROUND_DARK, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		inputframe.grid(column=1, row=1, sticky='we')
		self.directory = tk.Entry(inputframe, insertbackground=FOREGROUND, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 10), bd=0)
		self.directory.pack(expand=True, fill='x', pady=(8, 7), padx=10)
		def askdirectory():
			dir = tk.filedialog.askopenfilename(filetypes=[('All image types', '*.png *.jpg *.jpeg *.jpe *.jfif *.exif *.bmp *.dib *.rle *.tiff *.tif'), ('PNG', '*.png'), ('JPEG', '*.jpg *.jpeg *.jpe *.jfif *.exif'), ('BMP', '*.bmp *.dib *.rle'), ('TIFF', '*.tiff *.tif')], initialdir=os.getcwd())
			if dir:
				self.directory.delete(0, 'end')
				self.directory.insert(0, dir)
		browse = tk.Button(self.container, image=self.images['browse'], bg=ACCENT, activebackground=BACKGROUND_DARK, bd=0, cursor='hand2', command=askdirectory)
		browse.grid(column=2, row=1, ipady=2, ipadx=2)

		tk.Button(self.container, image=self.images['submit'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.update_pfp).grid(column=1, row=2, sticky='w')
		tk.Button(self.container, image=self.images['reset_to_default'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.reset_pfp).grid(column=1, row=2, sticky='w', padx=(142, 0))
		
		# Profile Name
		tk.Frame(self.container, bg='#454758').grid(row=3, column=0, columnspan=3, sticky='we', pady=(20, 10))
		tk.Label(self.container, text='Change Account Details ', font=(FONT, 14), bg=BACKGROUND, fg=FOREGROUND).grid(row=3, column=0, columnspan=3, sticky='w', pady=(20, 10))

		tk.Label(self.container, text='USERNAME ', font=(FONT, 10, 'bold'), bg=BACKGROUND, fg=FOREGROUND).grid(row=4, column=0, columnspan=3, sticky='w', pady=5)
		self.nameinputframe = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		self.nameinputframe.grid(column=0, row=5, sticky='we', columnspan=3)
		self.name = tk.Entry(self.nameinputframe, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.name.insert(0, self.username)
		self.name.pack(expand=True, fill='x')

		# Profile Email
		tk.Label(self.container, text='EMAIL ADDRESS ', font=(FONT, 10, 'bold'), bg=BACKGROUND, fg=FOREGROUND).grid(row=6, column=0, sticky='w', pady=(5,4))
		self.emailinputframe = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		self.emailinputframe.grid(column=0, row=7, sticky='we', columnspan=3)
		self.email = tk.Entry(self.emailinputframe, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.email.insert(0, self.user_email)
		self.email.pack(expand=True, fill='x')
		
		self.email_error = tk.Label(self.container, text='', font=(FONT, 10, 'bold'), bg=BACKGROUND, fg='#A01E37')
		self.email_error.grid(row=6, column=1, columnspan=2, sticky='e', pady=(5,4))

		# Account Management
		tk.Frame(self.container, bg='#454758').grid(row=8, column=0, columnspan=3, sticky='we', pady=20)
		tk.Label(self.container, text='Account Management ', font=(FONT, 14), bg=BACKGROUND, fg=FOREGROUND).grid(row=8, column=0, columnspan=3, sticky='w', pady=20)

		tk.Button(self.container, image=self.images['change_password'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=lambda:self.change_page('change_password')).grid(row=9, column=0, sticky='w', columnspan=3)
		tk.Button(self.container, image=self.images['delete_account'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.delete_account).grid(row=10, column=0, sticky='w', columnspan=3, pady=10)

		# Buttons
		tk.Button(self.container, image=self.images['save'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, cursor='hand2', command=self.save_changes).place(anchor='se', relx=1, rely=1, y=-10, x=10) # save changes

	def save_changes(self):
		self.nameinputframe.config(highlightbackground='grey', highlightcolor='white')
		self.emailinputframe.config(highlightbackground='grey', highlightcolor='white')
		self.email_error['text'] = ''

		self.cursor.execute(f"SELECT email from users WHERE email='{self.email.get()}'")
		result = self.cursor.fetchone()
		if result or not self.email.get(): # already in use or empty
			if result[0] != self.user_email:
				self.emailinputframe.config(highlightbackground='#A01E37', highlightcolor='#A01E37')
				self.email_error['text'] = '* This email is already in use.'
		else:
			self.check_password()

		if self.name.get(): # If username not empty
			self.cursor.execute(f"UPDATE Users SET email = ?, profile_picture = ?, username = ? WHERE oid = ?", (self.user_email, self.user_image, self.name.get(), self.oid))
			self.connection.commit()
			self.master.refresh(self.user_image, self.name.get())
		else:
			self.nameinputframe.config(highlightbackground='#A01E37', highlightcolor='#A01E37')

	def update_pfp(self):
		try:
			if self.directory.get():
				temp = self.directory.get()
			self.image_default_user_big = ImageTk.PhotoImage(Image.open(temp).resize((100, 100)))
			self.profilepic.config(image=self.image_default_user_big)
			self.user_image = self.directory.get()
		except:
			return False # invalid directory
		
	def reset_pfp(self):
		self.directory.delete(0, 'end')
		self.image_default_user_big = ImageTk.PhotoImage(Image.open(os.path.join(DIRECTORY, 'images', 'user_icon.png')).resize((100, 100)))
		self.profilepic.config(image=self.image_default_user_big)
		self.user_image = os.path.join(DIRECTORY, 'images', 'user_icon.png')

	def change_password_page(self):
		self.container.config(padx=48, pady=10)
		self.container.grid_columnconfigure(0, weight=1)
		self.container.grid_rowconfigure(9, weight=1)

		def show_field(widget, button):
			widget['show'] = ''
			button['image'] = self.images['visible']
			button['command'] = lambda:hide_field(widget, button)

		def hide_field(widget, button):
			widget['show'] = '•'
			button['image'] = self.images['invisible']
			button['command'] = lambda:show_field(widget, button)
		
		logo = tk.Label(self.container, image=self.images['blurred_logo'], bg=BACKGROUND)
		logo.grid(column=0, row=0, pady=(30, 20))
		page_title = tk.Label(self.container, text='CHOOSE A NEW PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 16, 'bold'))
		page_title.grid(column=0, row=1, pady=(0, 20))

		# Current
		tk.Label(self.container, text='CURRENT PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=2, sticky='w', padx=30, pady=5)
		current_pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		current_pass_frame.grid(column=0, row=3, padx=20, sticky='we')
		self.current_pass_input = tk.Entry(current_pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.current_pass_input.pack(fill='both', side='left', expand=True)

		toggle_current_password = tk.Button(current_pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:show_field(self.current_pass_input, self.toggle_current_password))
		toggle_current_password.pack(padx=5, side='right')

		# New
		tk.Label(self.container, text='NEW PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=4, sticky='w', padx=30, pady=(15, 5))
		pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		pass_frame.grid(column=0, row=5, padx=20, sticky='we')
		self.pass_input = tk.Entry(pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.pass_input.pack(fill='both', side='left', expand=True)

		toggle_password = tk.Button(pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:show_field(self.pass_input, self.toggle_password))
		toggle_password.pack(padx=5, side='right')

		# Confirm
		tk.Label(self.container, text='CONFIRM PASSWORD', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 11, 'bold')).grid(column=0, row=6, sticky='w', padx=30, pady=(15, 5))
		confirm_pass_frame = tk.Frame(self.container, bg=BACKGROUND_DARK, pady=15, padx=10, highlightbackground='grey', highlightcolor='white', highlightthickness=1)
		confirm_pass_frame.grid(column=0, row=7, padx=20, sticky='we')
		self.confirm_pass_input = tk.Entry(confirm_pass_frame, show='•', bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), insertbackground=FOREGROUND, bd=0)
		self.confirm_pass_input.pack(fill='both', side='left', expand=True)

		toggle_confirm_password = tk.Button(confirm_pass_frame, image=self.images['invisible'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, bd=0, command=lambda:show_field(self.confirm_pass_input, self.toggle_confirm_password))
		toggle_confirm_password.pack(padx=5, side='right')

		reset_password = tk.Button(self.container, image=self.images['reset'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=self.reset_password)
		reset_password.grid(column=0, row=8, padx=20, pady=(40, 0))

		back_button = tk.Button(self.container, text='Go back', bg=BACKGROUND, activebackground=BACKGROUND, fg=FOREGROUND, activeforeground=FOREGROUND, bd=0, font=(FONT, 10), command=lambda:self.change_page('settings'))
		back_button.grid(column=0, row=9, pady=30, sticky='sw')

		self.function_output = tk.Label(self.container, text='', bg=BACKGROUND, fg=ACCENT, font=(FONT, 11, 'bold'))
		self.function_output.grid(column=0, row=9, sticky='e', padx=(0, 30), pady=5)

	def reset_password(self):
		if self.pass_input.get() == self.confirm_pass_input.get():
			self.cursor.execute(f"SELECT password from users WHERE email='{self.user_email}'")
			password = self.cursor.fetchone()[0]
			if not bcrypt.checkpw(self.current_pass_input.get().encode('utf-8'), password.encode('utf-8')):
				self.function_output['text'] = '* Current password incorrect.'
				return False
			if self.current_pass_input.get() == self.pass_input.get():
				self.function_output['text'] = '* New password is same as current.'
				return False
			new_password_hashed = bcrypt.hashpw(self.pass_input.get().encode('utf-8'), bcrypt.gensalt(10))
			self.cursor.execute(f"UPDATE Users SET password = ? WHERE email = ?", (new_password_hashed.decode('utf-8'), self.user_email))
			self.connection.commit()
			self.change_page('settings')
			return True
		self.function_output['text'] = '* Passwords do not match.'
		return False

	def delete_account(self):
		if messagebox.askyesno('Confirm', 'Are you sure you want to delete your account? This cannot be undone'):
			self.cursor.execute(f"SELECT email FROM Users WHERE oid = '{self.oid}'")
			result = self.cursor.fetchone()[0]
			self.cursor.execute(f"DELETE FROM Users WHERE oid = '{self.oid}'")
			self.cursor.execute(f"DELETE FROM Vault WHERE master_email = '{result}'")
			self.connection.commit()
			self.master.logout()
