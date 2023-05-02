import tkinter as tk
from PIL import Image, ImageTk
import clipboard, threading, secrets, os

from support import *

class PasswordGenerator(tk.Toplevel):
	def __init__(self):
		super().__init__()

		# General
		self.title('Password Generator')
		self.iconbitmap(os.path.join(DIRECTORY, 'icon.ico'))
		self.geometry(f'360x480+{int(self.winfo_screenwidth()/2-180)}+{int(self.winfo_screenheight()/2-290)}')
		self.resizable(False, False)

		# Load images
		self.images = import_images(os.path.join(DIRECTORY, 'images', ''))
		for key, value in self.images.items():
			self.images[key] = ImageTk.PhotoImage(Image.open(value))

		self.container = tk.Frame(self, bg=BACKGROUND)
		self.container.pack(expand=True, fill='both')

		self.widgets()

	def widgets(self):
		title = tk.Label(self.container, text='PASSWORD  GENERATOR', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 14, 'bold'))
		title.grid(column=0, columnspan=2, row=0, padx=(27, 28), pady=30, sticky='we')

		output_frame = tk.Frame(self.container, bg=BACKGROUND_DARK)
		output_frame.grid(column=0, columnspan=2, row=1, sticky='we')
		self.output = tk.Entry(output_frame, bg=BACKGROUND_DARK, fg=FOREGROUND, font=(FONT, 12), bd=0, width=29, insertbackground=FOREGROUND)
		self.output.grid(column=0, row=0, padx=(20, 0))

		copy_ = tk.Button(output_frame, image=self.images['copy'], bg=BACKGROUND_DARK, activebackground=BACKGROUND_DARK, 
									font=(FONT, 12), bd=0, command=lambda:threading.Thread(target=lambda:clipboard.copy(self.output.get())).start())
		copy_.grid(column=1, row=0, padx=5, pady=5, sticky='e')

		length_label = tk.Label(self.container, text='Password Length', bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 12))
		length_label.grid(column=0, row=2, sticky='w', padx=30, pady=(30, 20))

		self.password_length = tk.IntVar()
		length_display = tk.Label(self.container, text=20, bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 12))
		length_display.grid(column=1, row=2, sticky='e', padx=30, pady=(30, 20))

		length_slider = tk.Scale(self.container, orient='horizontal', from_=5, to=50, bg=ACCENT, fg=FOREGROUND, resolution=1, 
										variable=self.password_length, showvalue=False, sliderlength=15, highlightthickness=0, bd=0, troughcolor=BACKGROUND_DARK, 
										sliderrelief='flat', command=lambda args:length_display.config(text=length_slider.get()))
		length_slider.set(20)
		length_slider.grid(column=0, columnspan=2, row=3, sticky='we', padx=30)

		re_roll = tk.Button(self.container, image=self.images['generate'], bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=self.generate_password)
		re_roll.grid(column=0, columnspan=2, row=5)

		self.toggles()

	def toggles(self):
		self.toggles_frame = tk.Frame(self.container, bg=BACKGROUND)
		self.toggles_frame.grid(column=0, columnspan=2, row=4, padx=27, pady=40, sticky='we')

		toggle_labels = ['a-z', 'A-Z', '0-9', '!@#']
		for n in range(4):
			tk.Label(self.toggles_frame, text=toggle_labels[n], bg=BACKGROUND, fg=FOREGROUND, font=(FONT, 12)).grid(column=n, row=0, sticky='w')

		def toggle_off(widget):
			widget['image'] = self.images['toggle_off']
			buffer = widget['text']
			widget['command'] = lambda:toggle_on(widget, buffer)
			widget['text'] = ''

		def toggle_on(widget, value):
			widget['text'] = value
			widget['image'] = self.images['toggle_on']
			widget['command'] = lambda:toggle_off(widget)

		toggle_a_z = tk.Button(self.toggles_frame, image=self.images['toggle_on'], text=LOWERCASE, bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:toggle_off(toggle_a_z))
		toggle_a_z.grid(column=0, row=1, padx=(0, 32))
		toggle_A_Z = tk.Button(self.toggles_frame, image=self.images['toggle_on'], text=UPPERCASE, bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:toggle_off(toggle_A_Z))
		toggle_A_Z.grid(column=1, row=1, padx=(0, 33))
		toggle_0_9 = tk.Button(self.toggles_frame, image=self.images['toggle_on'], text=NUMBERS, bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:toggle_off(toggle_0_9))
		toggle_0_9.grid(column=2, row=1, padx=(0, 33))
		toggle_sc = tk.Button(self.toggles_frame, image=self.images['toggle_on'], text=SPECIALCHARS, bg=BACKGROUND, activebackground=BACKGROUND, bd=0, command=lambda:toggle_off(toggle_sc))
		toggle_sc.grid(column=3, row=1)

	def generate_password(self):
		self.alphabet = ''
		for widget in self.toggles_frame.winfo_children()[4:8]:
			self.alphabet += widget['text']
		
		length = self.password_length.get()
		password = ''
		if self.alphabet != '':
			for _ in range(length):
				password += ''.join(secrets.choice(self.alphabet))
			self.output.delete(0, 'end')
			self.output.insert('end', password)
			
if __name__ == '__main__':
	PasswordGenerator().mainloop()