import tkinter as tk
from tkinter import ttk
import screeninfo
import subprocess
import re,zlib

#--
#
def crc32b(text):
	return "%x"%(zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF)

#--
#
class WindowManager:
	def __init__(self, root):
		self.windows = {} #w0={id=0,name='',host='',hash='crc32b'}
		self.root = root
		#self.root.title("Window Menu")
		#self.root.geometry("400x300")  # Initial size, will be adjusted
		# Get the primary monitor's dimensions
		self.screen = screeninfo.get_monitors()[0]
		screen_width = self.screen.width
		screen_height = self.screen.height
		# Set the window to span the full width of the screen at the top
		self.root.geometry(f"{screen_width}x50+0+0")
		# Remove the title bar and window decorations
		self.root.overrideredirect(True)
		# Make the window stay on top of other windows
		self.root.attributes("-topmost", True)
		# Create a frame to act as the title bar
		self.title_bar = tk.Frame(self.root, bg='gray', relief='raised', bd=1)
		self.title_bar.pack(fill=tk.X)
		# Add a close button to the title bar
		# self.close_button = tk.Button(
			# self.title_bar,
			# text='X',
			# command=self.root.destroy,
			# bg='gray',
			# fg='black',
			# bd=0,
			# relief='flat',
			# padx=(self.screen.width-20,0),
			# pady=(5)
		# )
		# self.close_button.pack(side=tk.RIGHT)
		# Make the window draggable by the title bar
		self.title_bar.bind("<ButtonPress-1>", self.start_move)
		self.title_bar.bind("<B1-Motion>", self.on_motion)
		# Store the position where the mouse was clicked
		self._drag_data = {"x": 0, "y": 0, "drag": False}
		# Rest of your initialization code...
		self.create_widgets()
	#
	def create_widgets(self):
		"""Create the widgets for the window list"""
		# Create a frame for the window list
		self.window_frame = tk.Frame(self.root)
		self.window_frame.pack(fill=tk.BOTH, expand=True)
 
		# Create a label
		#label = tk.Label(self.window_frame, text="Select a window:")
		#label.pack(pady=5)
 
		# Create a Combobox for window selection
		self.window_combobox = tk.ttk.Combobox(self.window_frame, state="readonly")
		#self.window_combobox.pack(fill=tk.X, padx=10, pady=5)
		self.window_combobox.pack(fill=tk.X, padx=(20,self.screen.width/2), pady=(0,20))
 
		# Bind the selection event
		self.window_combobox.bind("<<ComboboxSelected>>", self.on_window_selected)
 
		# Create a button to refresh the window list
		refresh_button = tk.Button(
			self.window_frame,
			text="Refresh",
			command=self.update_window_list
		)
		refresh_button.pack(pady=5)
 
		# Update the window list
		self.update_window_list()
	
	#
	def update_window_list(self):
		"""Update the dropdown menu with the current window list"""
		try:
			#
			# self.windows = {} #w0={id=0,name='',host='',hash='crc32b'}
			windows=[]
			cnt=0
			#
			result = subprocess.run(
				["wmctrl", "-l"],
				capture_output=True,
				text=True,
				check=True
			)
			#
			for line in result.stdout.splitlines():
				print("debug line: ",line)
				a = line.split(" ",4)
				print("a: ",a)
				print("appending: ",a[4])
				windows.append(a[4]) # prepare graphics dropdown with names only
				# save object so later is possible to access by selected item id
				wid="w{}".format(cnt)
				if wid in self.windows:
					#
					self.windows[wid]["id"]   = a[0]
					self.windows[wid]["host"] = a[3]
					self.windows[wid]["name"] = a[4]
				else:
					#
					self.windows[wid] = {"id":a[0],"host":a[3],"name":a[4],}
				cnt+=1
			# Extract just the window names (remove the leading window ID)
			# windows = [line.split(" ", 1)[1].strip() for line in result.stdout.splitlines() if line]
			self.window_combobox['values'] = windows
			if windows:
				self.window_combobox.current(0)
		except subprocess.CalledProcessError as e:
			print(f"Error running wmctrl: {e}")
			self.window_combobox['values'] = ["Error getting window list"]
		except FileNotFoundError:
			self.window_combobox['values'] = ["wmctrl not found"]
		
	def on_window_selected(self, event):
		"""Handle window selection and activate the selected window"""
		selected_index = self.window_combobox.current()  # Get the index of the selected item
		selected_value = self.window_combobox.get()      # Get the value of the selected item
		
		print(f"Selected index: {selected_index}")
		print(f"Selected value: {selected_value}")
		wid="w{}".format(selected_index)
		print("Debug windows wid: ",self.windows[wid])
		# You can use either the index or the value to find and activate the window
		self.activate_window(self.windows[wid]["id"])
		#self.activate_window(selected_index)
		# or
		# self.activate_window_by_value(selected_value)
	
	def activate_window(self, wmctrlId):
		"""Activate the selected window using its index"""
		try:
			print("activate_window() ",wmctrlId)
			result = subprocess.run(
				["wmctrl", "-i", "-a", wmctrlId],
				capture_output=True,
				text=True,
				check=True
			)
		except subprocess.CalledProcessError as e:
			print(f"Error activating window: {e}")
	#
	def start_move(self, event):
		"""Begin the window movement"""
		self._drag_data["x"] = event.x
		self._drag_data["y"] = event.y
		self._drag_data["drag"] = True
 
		# Raise the window to the top
		self.root.attributes("-topmost", True)
	#
	def on_motion(self, event):
		"""Handle the window movement"""
		if self._drag_data["drag"]:
			# Calculate the new position
			x = self.root.winfo_x() + (event.x - self._drag_data["x"])
			y = self.root.winfo_y() + (event.y - self._drag_data["y"])
 
			# Update the window position
			self.root.geometry(f"+{x}+{y}")
	#
	def on_release(self, event):
		"""End the window movement"""
		self._drag_data["drag"] = False
	
if __name__ == "__main__":
	root = tk.Tk()
	app = WindowManager(root)
	root.mainloop()
