import tkinter as tk
from tkinter import ttk
import screeninfo
import subprocess
import threading
from datetime import datetime
import atexit
import traceback
import re,time,sys
from src.functions import *
from src.config import Config
#--
#
kosdwm  = None
VERSION = "0.1b"
#--
#
#
def cleanup():
	print("cleanup() START")
	kos.wmctrltray.on_close()
	return True
#
def handle_exception(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		# Let KeyboardInterrupt propagate
		print("Exception: Keyboard Interrupt: {}".format(exc_type),{'verbose':True})
		return
	# Extract traceback info
	tb = traceback.extract_tb(exc_traceback)
	# Get the last frame (most recent error)
	frame = tb[-1]
	filename, line, func, text = frame
	print(f"Exception: {exc_type.__name__}: {exc_value} (line {line} in {filename})",{'verbose':True,})
	# Optionally print full traceback
	traceback.print_exception(exc_type, exc_value, exc_traceback)
#
atexit.register(cleanup)
sys.excepthook = handle_exception
#--
#
class WMCtrlTray:
	def __init__(self, root, config):
		self.windows      = {}
		self.lines        = []
		self.windows_hash = None
		self.stop_thread  = False
		self.root         = root
		self.config       = config
		# Get the primary monitor's dimensions
		self.screen = screeninfo.get_monitors()[0]
		screen_width = self.screen.width
		screen_height = self.screen.height
		# Set the window to span the full width of the screen at the top
		self.root.geometry(f"{screen_width}x25+0+0")
		# Remove the title bar and window decorations
		self.root.overrideredirect(True)
		# Make the window stay on top of other windows
		self.root.attributes("-topmost", True)
		#
		#
		def test_new_file():
			print("test new file!")
		#menu_bar = tk.Menu(self.root,tearoff=0)
		#file_menu = tk.Menu(menu_bar, tearoff=0)
		#file_menu.add_command(label="New", command=test_new_file)
		#menu_bar.add_cascade(label="Test",menu=file_menu)
		#self.root.config(menu=menu_bar)
		
		self.title_bar = tk.Frame(self.root, bg='gray', height=30,relief='raised',bd=1)
		#self.title_bar.pack(fill=tk.X, padx=(20,self.screen.width/2), pady=(0,0), ipady=5, side=tk.TOP)
		self.title_bar.pack(fill=tk.X)
		# Make the window draggable by the title bar
		self.title_bar.bind("<ButtonPress-1>", self.start_move)
		self.title_bar.bind("<B1-Motion>", self.on_motion)
		# Store the position where the mouse was clicked
		self._drag_data = {"x": 0, "y": 0, "drag": False}
		
		# test another window
		def test():
			r1 = tk.Toplevel(self.root)
			r1.title("World")
			r1.geometry("300x200")
			#menu_bar = tk.Menu(r1)
			#file_menu = tk.Menu(r1, tearoff=0)
			#file_menu.add_command(label="New", command=test_new_file)
			#menu_bar.add_cascade(label="Test",menu=file_menu)
			#r1.config(menu=menu_bar)
		#self.root.after_idle(test)
		#
		self.create_widgets()
	#
	def start_observer_thread(self):
		"""Start a thread to observe changes in window list"""
		observer_thread = threading.Thread(target=self.observer_loop)
		observer_thread.daemon = True
		observer_thread.start()
	#
	def observer_loop(self):
		"""Main loop for observing changes in window list"""
		#last_windows = set()
		#
		while not self.stop_thread:
			try:
				self.lines = []
				#
				# xprop -root _NET_ACTIVE_WINDOW | awk '{print $5}'
				r1 = subprocess.run(
					["xprop", "-root", "_NET_ACTIVE_WINDOW"],
					capture_output=True,
					text=True,
					check=True
				)
				current_active = r1.stdout.split(" ")[4]
				if self.last_active_window is not None and self.last_active_window != current_active:
					self.root.after(0, self.collapse_combobox)
				self.last_active_window = current_active
				#    0 - 9
				#    ID       X PROC   TOP  LEFT WIDTH HEIGHT CLASS             HOST      PROG_INFO
				# 0x0080000e  0 4026   468  341  898  446  xterm.UXTerm          kosgen0 t3ch@kosgen2: ~/sdb1/t3ch
				# 0x0140000a  0 11288  280  93   1086 692  geany.Geany           kosgen0 *run.py - /home/t3ch/Working/Hobies/OpenBox/WindowsMenu - Geany
				r2 = subprocess.run(
					["wmctrl", "-lpGuFxS"],
					capture_output=True,
					text=True,
					check=True
				)
				#
				for line in r2.stdout.splitlines():
					line = re.sub(r'\s+',' ',line)
					#print("debug line: ",line)
					self.lines.append(line)
				#
				windows_hash = crc32b( "".join(self.lines) )
				#
				if self.windows_hash!=None and self.windows_hash==windows_hash:
					print("Skipping update windows, windows_hash: {} vs {}".format( self.windows_hash, windows_hash ))
				else:
					print("Updating windows list, windows_hash {} vs {}".format( self.windows_hash, windows_hash ))
					self.root.after(0, self.update_window_list)
					self.windows_hash = windows_hash
				self.root.after(0, self._update_active_desktop_button)
				time.sleep(1)  # Check every second
			except subprocess.CalledProcessError as e:
				print(f"Error running wmctrl: {e}")
				time.sleep(5)  # Wait longer if there's an error
			except Exception as e:
				print(f"Unexpected error: {e}")
				time.sleep(5)  # Wait longer if there's an unexpected error
	#
	def update_window_list(self):
		"""Update the dropdown menu with the current window list"""
		print("update_window_list() START lines.len: {}, hash: {}".format( len(self.lines), self.windows_hash ))
		#
		def shorten_hex(hex_value):
			"""Convert a hexadecimal value to its shortest representation."""
			print(f"shorten_hex called with: {hex_value!r} (type: {type(hex_value)})")  # Debug line
			# Handle string inputs
			if isinstance(hex_value, str):
				# Remove '0x' prefix if present
				if hex_value.startswith('0x'):
					hex_value = hex_value[2:]
				# Convert to integer
				try:
					hex_value = int(hex_value, 16)
				except ValueError:
					raise ValueError(f"Input string '{hex_value}' must be a valid hexadecimal number")
			# Convert to hex string and remove leading zeros
			hex_str = hex(hex_value)
			return '0x' + hex_str[2:].lstrip('0') or '0x0'
		#
		try:
			#
			# self.windows = {} # w0={id=0,name='',host='',hash='crc32b'}
			windows      = []
			lines        = []
			windows_hash = None
			self.windows = {}
			cnt=0
			#    0 - 9
			#    ID       X PID   LEFT  TOP WIDTH HEIGHT CLASS             HOST      PROG_INFO
			# 0x0080000e  0 4026   468  341  898  446  xterm.UXTerm          kosgen0 t3ch@kosgen2: ~/sdb1/t3ch
			# 0x0140000a  0 11288  280  93   1086 692  geany.Geany           kosgen0 *run.py - /home/t3ch/Working/Hobies/OpenBox/WindowsMenu - Geany
			#
			for line in reversed(self.lines):
				a = line.split(" ",9)
				#print("a: ",a)
				side_number = 1
				if int(a[3])>=self.screen.width:
					side_number = 2
				windows.append("{} ) {}".format(side_number, a[9])) # prepare graphics dropdown with names only
				#print("{} debug line: {}".format( self.screen.width, line ))
				fid = shorten_hex(a[0])
				# save object so later is possible to access by selected item id
				crc = crc32b( line )
				wid = "w{}".format(cnt)
				if wid in self.windows:
					#
					self.windows[wid]["id"]    = a[0]
					self.windows[wid]["fid"]   = fid
					self.windows[wid]["pid"]   = a[2]
					self.windows[wid]["left"]  = a[3]
					self.windows[wid]["top"]   = a[4]
					self.windows[wid]["class"] = a[7]
					self.windows[wid]["host"]  = a[8]
					self.windows[wid]["name"]  = a[9]
					self.windows[wid]["hash"]  = crc
				else:
					#
					self.windows[wid] = {"id":a[0],"pid":a[2],"fid":fid,"left":a[3],"top":a[4],"class":a[7],"host":a[8],"name":a[9],}
					# generate window id ex.: wid_left+_+top
					# check class, if xterm.XTerm start script -O dataio.out -T timeio.out
				cnt+=1
				print("wid: {}".format( self.windows[wid] ))
			#
			self.window_combobox['values'] = windows
			if windows:
				self.window_combobox.current(0)
				self.combobox_actual_value = windows[0]
			self.window_combobox.set("▼")
		except subprocess.CalledProcessError as e:
			print(f"Error running wmctrl: {e}")
			self.window_combobox['values'] = ["Error getting window list"]
		except FileNotFoundError:
			self.window_combobox['values'] = ["wmctrl not found"]
		return True
	#
	def start_time_thread(self):
		"""Start a thread to update the time display"""
		time_thread = threading.Thread(target=self.time_update_loop)
		time_thread.daemon = True
		time_thread.start()
	#
	def time_update_loop(self):
		"""Main loop for updating the time display"""
		while not self.stop_thread:
			try:
				# Update the time display on the main thread
				self.root.after(0, self.update_time_display)
				time.sleep(1)  # Update every second
			except Exception as e:
				print(f"Error in time update loop: {e}")
				time.sleep(5)  # Wait longer if there's an error
	#
	def update_time_display(self):
		"""Update the time and date display"""
		now = datetime.now()
		time_str = now.strftime("%H:%M:%S")
		date_str = "{} |".format(now.strftime("%Y-%m-%d"))
		# Update the time label if it exists
		if hasattr(self, 'time_label'):
			self.time_label.config(text=time_str)
		else:
			# Create the time label if it doesn't exist
			self.time_label = tk.Label(
				#self.title_bar,
				self.time_frame,
				text=time_str,
				bg='gray',
				fg='white',
				font=('Arial', 10)
			)
			self.time_label.pack(side=tk.RIGHT, padx=0,pady=0,ipady=0)
 
		# Update the date label if it exists
		if hasattr(self, 'date_label'):
			self.date_label.config(text=date_str)
		else:
			# Create the date label if it doesn't exist
			self.date_label = tk.Label(
				#self.title_bar,
				self.time_frame,
				text=date_str,
				bg='gray',
				fg='white',
				font=('Arial', 10)
			)
			self.date_label.pack(side=tk.RIGHT, padx=0,pady=0,ipady=0)
	#
	def create_widgets(self):
		"""Create the widgets for the window list"""
		#-- Main WindowFrame START
		#self.window_frame = tk.Frame(self.title_bar,width=100)
		self.window_frame = tk.Frame(self.title_bar)
		self.window_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=(0))
		#-- Combobox START
		self.frame1 = tk.Frame(self.window_frame)
		self.frame1.pack(fill=tk.BOTH, side=tk.LEFT, padx=(0))
		#
		self.combobox_expanded_width = 60
		self.combobox_collapsed_width = 2
		self.combobox_actual_value = ""
		self.window_combobox = tk.ttk.Combobox(self.frame1, state="readonly",width=self.combobox_collapsed_width, justify='center')
		self.window_combobox.pack(fill=tk.X, padx=(0), pady=(0), ipady=5)
		#-- Desktop Buttons (1-4) START
		self.frame2 = tk.Frame(self.window_frame)
		self.frame2.pack(fill=tk.BOTH, padx=(0))
		self.desktop_buttons_frame = tk.Frame(self.frame2)
		self.desktop_buttons_frame.pack(side=tk.LEFT, padx=(0,5))
		self.desktop_buttons = []
		inactive_bg = self.config.get("inactive_button_bg", "#606060")
		for i in range(4):
			btn = tk.Button(
				self.desktop_buttons_frame,
				text=str(i+1),
				width=2,
				bg=inactive_bg,
				fg="white",
				relief="raised",
				bd=1,
				command=lambda n=i: self.switch_desktop(n)
			)
			btn.pack(side=tk.LEFT, padx=1)
			self.desktop_buttons.append(btn)
		self._update_active_desktop_button()
		#-- WindowCombobox Continue Settings
		self.window_combobox.set("▼")
		self.window_combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected)
		self.window_combobox.bind("<ButtonPress-1>", self.on_combobox_click)
		self.root.bind("<ButtonPress-1>", self.on_root_click)
		self.root.bind("<FocusOut>", self.on_root_focus_out)
		self.combobox_was_expanded = False
		self.last_active_window = None
		
		# Create a frame for the time/date display on the right side of the title bar
		self.frame3 = tk.Frame(self.title_bar)
		self.frame3.pack(side=tk.RIGHT)
		self.time_frame = tk.Frame(self.frame3)
		self.time_frame.pack(side=tk.RIGHT, padx=1, pady=0)
		#
		self.update_window_list()
		#
		self.start_observer_thread()
		self.start_time_thread()
	#
	def on_combobox_click(self, event):
		"""Handle combobox click - expand and show actual window name"""
		self.combobox_was_expanded = True
		self.window_combobox.configure(width=self.combobox_expanded_width, justify='left')
		self.window_combobox.set(self.combobox_actual_value)

	def on_combobox_selected(self, event):
		"""Handle window selection from dropdown - collapse combobox and switch to selected window"""
		selected_index = self.window_combobox.current()
		selected_value = self.window_combobox.get()
		self.combobox_actual_value = selected_value
		self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
		self.window_combobox.set("▼")
		self.combobox_was_expanded = False
		self.on_window_selected_by_index(selected_index, selected_value)

	def on_root_click(self, event):
		"""Collapse combobox when clicking outside its bounds"""
		if self.combobox_was_expanded:
			if not self.window_combobox.winfo_exists():
				return
			x = event.x_root - self.window_combobox.winfo_rootx()
			y = event.y_root - self.window_combobox.winfo_rooty()
			if x < 0 or x > self.window_combobox.winfo_width() or y < 0 or y > self.window_combobox.winfo_height():
				self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
				self.window_combobox.set("▼")
				self.combobox_was_expanded = False

	def on_root_focus_out(self, event):
		"""Collapse combobox when root window loses focus"""
		if self.combobox_was_expanded:
			self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
			self.window_combobox.set("▼")
			self.combobox_was_expanded = False

	def collapse_combobox(self):
		"""Collapse combobox to collapsed state with triangle icon"""
		if self.combobox_was_expanded:
			self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
			self.window_combobox.set("▼")
			self.combobox_was_expanded = False

	def on_window_selected_by_index(self, selected_index, selected_value):
		"""Activate window by index and save selected value"""
		wid = "w{}".format(selected_index)
		print("Debug windows wid: ", self.windows[wid])
		self.activate_window(self.windows[wid]["id"])

	def on_window_selected(self, event):
		"""Handle window selection from combobox"""
		selected_index = self.window_combobox.current()
		selected_value = self.window_combobox.get()
		self.on_window_selected_by_index(selected_index, selected_value)
	#
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

	def switch_desktop(self, desktop):
		"""Switch to the specified Openbox desktop"""
		try:
			print(f"switch_desktop() {desktop}")
			subprocess.run(
				["wmctrl", "-s", str(desktop)],
				capture_output=True,
				text=True,
				check=True
			)
			print(f"wmctrl -s succeeded, calling _update_active_desktop_button()")
			self.root.after(0, self._update_active_desktop_button)
		except subprocess.CalledProcessError as e:
			print(f"Error switching desktop: {e}")

	def _get_current_desktop(self):
		"""Get the current active desktop number"""
		try:
			result = subprocess.run(
				["wmctrl", "-d"],
				capture_output=True,
				text=True,
				check=True
			)
			# result Ex.:
			# t3ch@kosgen0:~/Working/Hobies/OpenBox/KosDWM$ wmctrl -d
			# 0  * DG: 3286x1080  VP: 0,0  WA: 0,0 3286x1080  Escritorio 1
			# 1  - DG: 3286x1080  VP: 0,0  WA: 0,0 3286x1080  Escritorio 2
			# 2  - DG: 3286x1080  VP: 0,0  WA: 0,0 3286x1080  Escritorio 3
			# 3  - DG: 3286x1080  VP: 0,0  WA: 0,0 3286x1080  Escritorio 4
			#
			for line in result.stdout.splitlines():
				line = re.sub(r'\s+',' ',line)
				#if line.startswith('*'):
				if rmatch(line,r"^\d+\x20\*.*"):
					desktop_num = int(line.split(" ")[0])
					print(f"_get_current_desktop() found: {desktop_num}")
					return desktop_num
			print("_get_current_desktop() no * found, returning 0")
			return 0
		except (subprocess.CalledProcessError, IndexError) as e:
			print(f"Error getting current desktop: {e}")
			return 0
	#
	def _update_active_desktop_button(self):
		"""Update desktop button colors based on current active desktop"""
		current = self._get_current_desktop()
		print(f"_update_active_desktop_button() current={current}, buttons={len(self.desktop_buttons)}")
		active_bg = self.config.get("active_button_bg", "#4a90d9")
		inactive_bg = self.config.get("inactive_button_bg", "#606060")
		for i, btn in enumerate(self.desktop_buttons):
			if i == current:
				btn.configure(bg=active_bg, activebackground=active_bg)
			else:
				btn.configure(bg=inactive_bg, activebackground=inactive_bg)
		self.root.update_idletasks()
	#-- MOVE TO TOP OF Window and stick
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
	#
	def on_close(self):
		"""Clean up when the application is closing"""
		self.stop_thread = True
		self.root.destroy()
#--
#
class KosDWM:
	def __init__(self):
		print("KosDWM().init() STARTED!")
		self.root       = tk.Tk()
		self.config     = Config()
		self.wmctrltray = None
	def Start(self):
		print("KosDWM.Start() STARTED!")
		self.wmctrltray = WMCtrlTray(self.root, self.config)
		self.root.mainloop()
#--
#
if __name__ == "__main__":
	kosdwm = KosDWM()
	kosdwm.Start()
