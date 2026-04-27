import tkinter as tk
from tkinter import ttk
import screeninfo
import subprocess
import threading
from datetime import datetime
import atexit
import traceback
import re,time,sys
import os
import json
import importlib.util
from src.functions import *
from src.config import Config


class MainMenus:
	def __init__(self, root, hidden_frame, kosdwm_ref):
		self.root = root
		self.hidden_frame = hidden_frame
		self.kosdwm = kosdwm_ref
		self.menu_buttons = []
	
	def load_and_create_menus(self):
		"""Load menus from folder structure and create buttons"""
		menus_dir = os.path.expanduser("~/.config/KosDWM/Menus")
		if not os.path.exists(menus_dir):
			return
		
		for item in sorted(os.listdir(menus_dir)):
			item_path = os.path.join(menus_dir, item)
			if os.path.isdir(item_path) and item != '__pycache__':
				self._create_menu_folder(item, item_path)
	
	def _create_menu_folder(self, name, path):
		"""Create a menu button from a folder"""
		menu_btn = tk.Menubutton(self.hidden_frame, text=name, underline=0)
		menu_btn.pack(side=tk.LEFT, padx=(5,0), pady=(2,0))
		
		sub_menu = tk.Menu(menu_btn, tearoff=0)
		menu_btn.config(menu=sub_menu)
		
		menu_btn.bind("<ButtonPress-1>", lambda e: setattr(self.kosdwm, '_any_dropdown_open', True))
		
		self._add_submenu_items(sub_menu, path)
		self.menu_buttons.append(menu_btn)
	
	def _add_submenu_items(self, menu, path):
		"""Add items to a menu from a folder structure"""
		for item in sorted(os.listdir(path)):
			if item == '__pycache__':
				continue
			item_path = os.path.join(path, item)
			if os.path.isdir(item_path):
				config_path = os.path.join(item_path, 'config.json')
				if os.path.exists(config_path):
					menu.add_command(label=item, command=lambda p=item_path: self._show_folder_content(p))
				else:
					sub = tk.Menu(menu, tearoff=0)
					menu.add_cascade(label=item, menu=sub)
					self._add_submenu_items(sub, item_path)
			elif item.endswith('.py') and item != '__init__.py':
				script_name = os.path.splitext(item)[0]
				script_path = os.path.expanduser(item_path)
				menu.add_command(label=script_name, command=lambda p=script_path, n=script_name: self._run_script(p, n))
	
	def _show_folder_content(self, path):
		"""Show window with content from folder's config.json"""
		self.kosdwm._any_dropdown_open = False
		
		config_path = os.path.join(path, 'config.json')
		try:
			with open(config_path, 'r') as f:
				config = json.load(f)
		except:
			return
		
		content_file = os.path.expanduser(os.path.join(path, config.get('windowContent', '')))
		ok_script = os.path.join(path, 'ok.py')
		script_cmd = config.get('windowScript', '')
		loop_interval = config.get('loop', 0)
		looptype = config.get('looptype', 'second')
		enable_scroll = config.get('windowScroll', True)
		
		win = tk.Toplevel(self.root)
		win.title(config.get('title', os.path.basename(path)))
		win.geometry("600x400")
		win.resizable(False, False)
		
		if enable_scroll:
			scroll_frame = tk.Frame(win)
			scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
			
			text_widget = tk.Text(scroll_frame, height=20, width=70, font=('Courier', 9))
			scrollbar = tk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=text_widget.yview)
			text_widget.configure(yscrollcommand=scrollbar.set)
			
			if script_cmd:
				text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
				scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
			else:
				text_widget.pack(fill=tk.BOTH, expand=True)
		else:
			text_widget = tk.Text(win, height=20, width=70, font=('Courier', 9))
			text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		text_widget.tag_configure('center', justify='center')
		text_widget.tag_configure('left', justify='left')
		
		if script_cmd:
			interval_ms = loop_interval * 1000 if looptype == 'second' else loop_interval
			def update_output():
				try:
					result = subprocess.run(script_cmd, shell=True, capture_output=True, text=True, timeout=10)
					text_widget.delete('1.0', tk.END)
					text_widget.insert('1.0', result.stdout if result.stdout else result.stderr, 'left')
				except Exception as e:
					text_widget.delete('1.0', tk.END)
					text_widget.insert('1.0', str(e), 'left')
				if win.winfo_exists():
					win.after(interval_ms, update_output)
			update_output()
		else:
			try:
				with open(content_file, 'r') as f:
					content = f.read().strip()
				text_widget.delete('1.0', tk.END)
				text_widget.insert('1.0', content, 'left')
			except FileNotFoundError:
				text_widget.insert('1.0', "Content not found.", 'center')
		
		btn_frame = tk.Frame(win)
		btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
		
		if os.path.exists(ok_script):
			tk.Button(btn_frame, text="OK", command=lambda: self._run_ok_script(win, ok_script)).pack()
		else:
			tk.Button(btn_frame, text="OK", command=win.destroy).pack()
	
	def _run_ok_script(self, window, script_path):
		"""Run ok.py script and close window"""
		try:
			spec = importlib.util.spec_from_file_location("ok_script", script_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			if hasattr(module, 'run'):
				module.run(window)
			else:
				window.destroy()
		except Exception as e:
			print(f"Error running ok.py: {e}")
			window.destroy()
	
	def _run_script(self, script_path, script_name):
		"""Run a menu script"""
		self.kosdwm._any_dropdown_open = False
		try:
			spec = importlib.util.spec_from_file_location("menu_script", script_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			if hasattr(module, 'run'):
				module.run(self.root)
		except Exception as e:
			print(f"Error running {script_name}: {e}")
			tk.Toplevel(self.root).destroy()


kosdwm  = None
VERSION = "0.1b"
#--
#
#
def cleanup():
	print("cleanup() START")
	global kosdwm
	if kosdwm and hasattr(kosdwm, 'wmctrltray'):
		kosdwm.wmctrltray.on_close()
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
		self.windows      = {} # self.windows[widX] = {id,desktop,pid,fid...}
		self.desktop      = {} # self.desktop[desktop] = ['wid1','wid2'...]
		self.lines        = []
		self.windows_hash = None # used to check if there is any change in output of wmctrl -l... from previous output
		self.stop_thread  = False
		self.root         = root
		self.config       = config
		# Get the primary monitor's dimensions
		self.screen = screeninfo.get_monitors()[0]
		screen_width = self.screen.width
		screen_height = self.screen.height
		# Set the window to span the full width of the screen at the top
		self.bar_height = 33
		self.bar_height_expanded = 83
		# Window stays at top of screen (Y=0)
		self.root.geometry(f"{screen_width}x{self.bar_height}+0+0")
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
		
		self.title_bar = tk.Frame(self.root, bg='gray', height=self.bar_height,relief='raised',bd=1)
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
					#
					self.root.after(0, self.update_window_list)
					#self.root.after(0, self._update_active_desktop_button)
					self.windows_hash = windows_hash
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
			self.desktop = {}
			cnt=0
			#            0-3
			#    ID     DESK PID   LEFT  TOP WIDTH HEIGHT CLASS             HOST      PROG_INFO
			# 0x0080000e  0 4026   468  341  898  446  xterm.UXTerm          kosgen0 t3ch@kosgen2: ~/sdb1/t3ch
			# 0x0140000a  0 11288  280  93   1086 692  geany.Geany           kosgen0 *run.py - /home/t3ch/Working/Hobies/OpenBox/WindowsMenu - Geany
			#
			for line in reversed(self.lines):
				a = line.split(" ",9)
				#print("a: ",a)
				side_number = 1
				if int(a[3])>=self.screen.width:
					side_number = 2
				# desktop_id | side_number .) window_title_name
				windows.append("{}|{} ) {}".format(a[1], side_number, a[9])) # prepare graphics dropdown with names only
				#print("{} debug line: {}".format( self.screen.width, line ))
				fid = shorten_hex(a[0])
				# save object so later is possible to access by selected item id
				crc = crc32b( line )
				wid = "w{}".format(cnt)
				if wid in self.windows:
					#
					self.windows[wid]["id"]      = a[0] # window id ex. 0x0000ad00
					self.windows[wid]["desktop"] = a[1] # desktop 0-3
					self.windows[wid]["fid"]     = fid  # short window id. Ex.: when using xprop -root _NET_ACTIVE_WINDOW # it return short window id
					self.windows[wid]["pid"]     = a[2]
					self.windows[wid]["left"]    = a[3]
					self.windows[wid]["top"]     = a[4]
					self.windows[wid]["class"]   = a[7]
					self.windows[wid]["host"]    = a[8]
					self.windows[wid]["name"]    = a[9]
					self.windows[wid]["hash"]    = crc
				else:
					#
					self.windows[wid] = {"id":a[0],"desktop":a[1],"pid":a[2],"fid":fid,"left":a[3],"top":a[4],"class":a[7],"host":a[8],"name":a[9],}
					# generate window id ex.: wid_left+_+top
					# check class, if xterm.XTerm start script -O dataio.out -T timeio.out
				# Set self.desktop[desktop_id | a[1]] object
				if a[1] not in self.desktop:
					self.desktop[a[1]] = []
				self.desktop[a[1]].append(wid)
				# repeat loop
				cnt+=1
				print("DEBUG self.windows wid: {}, data: {}".format( wid, self.windows[wid] ))
				print("DEBUG self.desktop at {}: {}".format(a[1],self.desktop[a[1]]))
			#
			if self.window_combobox:
				self.window_combobox['values'] = windows
				if windows:
					self.window_combobox.current(0)
					self.combobox_actual_value = windows[0]
				self.window_combobox.set(self.window_combobox.get())
		except subprocess.CalledProcessError as e:
			print(f"Error running wmctrl: {e}")
			if self.window_combobox:
				self.window_combobox['values'] = ["Error getting window list"]
		except FileNotFoundError:
			if self.window_combobox:
				self.window_combobox['values'] = ["wmctrl not found"]
		#
		self._update_desktop_comboboxes()
		self._update_active_desktop_button()
		return True

	def _update_desktop_comboboxes(self):
		"""Update desktop window comboboxes with windows for each desktop"""
		# if not hasattr(self, 'desktop_comboboxes'):
			# return
		# for desktop_id, cb in enumerate(self.desktop_comboboxes):
			# windows_for_desktop = []
			# if desktop_id in self.desktop:
				# for wid in self.desktop[desktop_id]:
					# if wid in self.windows:
						# windows_for_desktop.append(self.windows[wid]["name"])
			# cb['values'] = windows_for_desktop
			# if windows_for_desktop:
				# cb.current(0)
				# cb.actual_value = windows_for_desktop[0]
				# cb.set(windows_for_desktop[0][:3] if len(windows_for_desktop) > 0 else "▼")
			# else:
				# cb.set(cb.actual_value)
		#
		for desktop_id in self.desktop:
			print("DEBUG _update_desktop_comboboxes() desktop_id: {}".format(desktop_id))
			awid                = self.desktop[desktop_id]
			windows_for_desktop = []
			#
			for wid in awid:
				print("DEBUG _update_desktop_comboboxes() wid: {}".format(wid))
				owid = self.windows[wid]
				# ex. owid: self.windows[wid] = {"id":a[0],"desktop":a[1],"pid":a[2],"fid":fid,"left":a[3],"top":a[4],"class":a[7],"host":a[8],"name":a[9],}
				# Calculate side_number based on window position
				side_number = 1
				if int(owid['left']) >= self.screen.width:
					side_number = 2
				# Display: side_number TITLE
				windows_for_desktop.append("{} {}".format(side_number, owid['name']))
			#
			print("DEBUG _update_desktop_comboboxes() appending windows to desktop_comboboxes... {}".format(desktop_id))
			cb = self.desktop_comboboxes[int(desktop_id)]
			cb['values'] = windows_for_desktop
			if windows_for_desktop:
				cb.current(0)
				cb.actual_value = windows_for_desktop[0]
				cb.set(windows_for_desktop[0][:3] if len(windows_for_desktop) > 0 else "▼")
			else:
				cb.set(cb.actual_value)
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
		combobox_ipady = self.config.get("combobox_ipady", 1)
		
		#-- Main WindowFrame START
		self.window_frame = tk.Frame(self.title_bar)
		self.window_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=(0))
		
		# Always visible: Desktop buttons + All windows combobox
		self.desktop_buttons = []
		inactive_bg = self.config.get("inactive_button_bg", "#606060")
		self.desktop_buttons_frame = tk.Frame(self.window_frame)
		self.desktop_buttons_frame.pack(side=tk.LEFT, padx=(0,2))
		for i in range(4):
			btn = tk.Button(
				self.desktop_buttons_frame,
				text=str(i+1),
				width=2,
				height=1,
				bg=inactive_bg,
				fg="white",
				relief="raised",
				bd=1,
				command=lambda n=i: self.switch_desktop(n)
			)
			btn.pack(side=tk.LEFT, padx=(1,0))
			self.desktop_buttons.append(btn)
		self._update_active_desktop_button()
		
		# All windows combobox (always visible)
		self.combobox_expanded_width = 60
		self.combobox_collapsed_width = 2
		self.combobox_actual_value = ""
		self.window_combobox = tk.ttk.Combobox(self.window_frame, state="readonly", width=self.combobox_collapsed_width, justify='center')
		self.window_combobox.pack(fill=tk.X, padx=(0), pady=(0), ipady=combobox_ipady)
		self.window_combobox.set(self.window_combobox.get())
		self.window_combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected)
		self.window_combobox.bind("<ButtonPress-1>", self.on_combobox_click)
		self.combobox_was_expanded = False
		
		# Create hidden frame for 4 desktop comboboxes + red frame + Help menu (shown on hover)
		self.hidden_frame = tk.Frame(self.root)
		
		# Create a frame for the 4 desktop comboboxes (horizontal layout)
		self.combo_row = tk.Frame(self.hidden_frame, bg='gray30')
		self.combo_row.pack(fill=tk.X)
		
		self.desktop_comboboxes = []
		button_width = 3
		for desktop_id in range(4):
			cb = tk.ttk.Combobox(self.combo_row, state="readonly", width=button_width, justify='center')
			cb.pack(side=tk.LEFT, padx=(1,0), pady=(0), ipady=combobox_ipady)
			cb.desktop_id = desktop_id
			cb.collapsed_width = button_width
			cb.expanded_width = 40
			cb.was_expanded = False
			cb.actual_value = ""
			cb.set(cb.actual_value)
			cb.bind("<<ComboboxSelected>>", self.on_desktop_combobox_selected)
			cb.bind("<ButtonPress-1>", self.on_desktop_combobox_click)
			self.desktop_comboboxes.append(cb)
		
		# Red frame below comboboxes
		self.red_frame = tk.Frame(self.hidden_frame, height=2)
		self.red_frame.pack(fill=tk.X, padx=(0,0), pady=(2, 0))
		
		# Use MainMenus class for dynamic menus
		self.main_menus = MainMenus(self.root, self.hidden_frame, self)
		self.main_menus.load_and_create_menus()
		
		# Initially hide the hidden frame
		self.hidden_frame.pack_forget()
		self._hidden_visible = False
		self._hide_timer = None
		self._any_dropdown_open = False
		
		# Bind hover events to show/hide hidden frame
		# Only bind to root, not to hidden_frame to avoid rapid toggling
		self.root.bind("<Enter>", self._on_hidden_show)
		self.root.bind("<Leave>", self._on_hidden_hide)
		
		self.root.bind("<ButtonPress-1>", self.on_root_click)
		self.root.bind("<FocusOut>", self.on_root_focus_out)
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
		if self.window_combobox is None:
			return
		self.combobox_was_expanded = True
		self.window_combobox.configure(width=self.combobox_expanded_width, justify='left')
		self.window_combobox.set(self.combobox_actual_value)

	def on_combobox_selected(self, event):
		"""Handle window selection from dropdown - collapse combobox and switch to selected window"""
		if self.window_combobox is None:
			return
		selected_index = self.window_combobox.current()
		selected_value = self.window_combobox.get()
		self.combobox_actual_value = selected_value
		self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
		self.window_combobox.set(self.window_combobox.get())
		self.combobox_was_expanded = False
		self.on_window_selected_by_index(selected_index, selected_value)
	
	def on_desktop_combobox_click(self, event):
		"""Handle desktop combobox click - expand and show windows for that desktop"""
		cb = event.widget
		cb.was_expanded = True
		cb.configure(width=cb.expanded_width, justify='left')
		cb.set(cb.actual_value if cb.actual_value else "")
		# Mark that a dropdown is open - don't hide frame
		self._any_dropdown_open = True
	
	def _collapse_all_desktop_comboboxes(self):
		"""Collapse all expanded desktop comboboxes"""
		if not hasattr(self, 'desktop_comboboxes'):
			return
		for cb in self.desktop_comboboxes:
			if cb.was_expanded:
				cb.configure(width=cb.collapsed_width, justify='center')
				cb.set(cb.actual_value)
				cb.was_expanded = False
		# Mark that dropdowns are closed
		self._any_dropdown_open = False
	
	def on_desktop_combobox_selected(self, event):
		"""Handle window selection from desktop dropdown"""
		cb = event.widget
		desktop_id = str(cb.desktop_id)
		selected_index = cb.current()
		selected_value = cb.get()
		cb.actual_value = selected_value
		cb.configure(width=cb.collapsed_width, justify='center')
		cb.set(cb.actual_value)
		cb.was_expanded = False
		# Activate the selected window
		wid = self.desktop[desktop_id][selected_index] if desktop_id in self.desktop else None
		if wid and wid in self.windows:
			self.activate_window(self.windows[wid]["id"])

	def on_root_click(self, event):
		"""Collapse combobox when clicking outside its bounds"""
		if self.combobox_was_expanded and self.window_combobox:
			if not self.window_combobox.winfo_exists():
				return
			x = event.x_root - self.window_combobox.winfo_rootx()
			y = event.y_root - self.window_combobox.winfo_rooty()
			if x < 0 or x > self.window_combobox.winfo_width() or y < 0 or y > self.window_combobox.winfo_height():
				self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
				self.window_combobox.set(self.window_combobox.get())
				self.combobox_was_expanded = False
		self._collapse_all_desktop_comboboxes()

	def on_root_focus_out(self, event):
		"""Collapse combobox when root window loses focus"""
		if self.combobox_was_expanded and self.window_combobox:
			self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
			self.window_combobox.set(self.window_combobox.get())
			self.combobox_was_expanded = False
		self._collapse_all_desktop_comboboxes()

	def collapse_combobox(self):
		"""Collapse combobox to collapsed state with triangle icon"""
		if self.combobox_was_expanded:
			self.window_combobox.configure(width=self.combobox_collapsed_width, justify='center')
			self.window_combobox.set(self.window_combobox.get())
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
			self._collapse_all_desktop_comboboxes()
		except subprocess.CalledProcessError as e:
			print(f"Error activating window: {e}")

	def show_about(self):
		"""Show About window with content from ABOUT.md"""
		import os
		about_win = tk.Toplevel(self.root)
		about_win.title("About")
		about_win.geometry("400x150")
		about_win.resizable(False, False)
		
		about_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ABOUT.md")
		try:
			with open(about_file, 'r') as f:
				about_content = f.read().strip()
		except FileNotFoundError:
			about_content = "About file not found."
		
		tk.Label(about_win, text=about_content, pady=20, font=('Arial', 10), wraplength=380).pack()
		tk.Button(about_win, text="OK", command=about_win.destroy).pack()
	
	def _on_help_menu_closed(self):
		"""Called after Help menu action completes"""
		self._any_dropdown_open = False
		self.show_about()
	
	def _on_hidden_show(self, event):
		"""Show hidden frame on root hover - also expand window height"""
		# Cancel any pending hide
		if hasattr(self, '_hide_timer') and self._hide_timer is not None:
			self.root.after_cancel(self._hide_timer)
			self._hide_timer = None
		if not self._hidden_visible:
			self.hidden_frame.pack(fill=tk.X, padx=(0,0), pady=(2,0))
			self._hidden_visible = True
		# Expand window height to show all content (stay at top of screen)
		if self.root.winfo_height() < self.bar_height_expanded:
			self.root.geometry(f"{self.screen.width}x{self.bar_height_expanded}+0+0")
	
	def _on_hidden_hide(self, event):
		"""Hide hidden frame on root leave with delay"""
		if self._hidden_visible:
			# Don't hide if any dropdown is open
			if hasattr(self, '_any_dropdown_open') and self._any_dropdown_open:
				return
			# Longer delay before hiding to allow interaction with menu
			self._hide_timer = self.root.after(500, self._do_hide)
	
	def _do_hide(self):
		"""Actually hide the hidden frame and restore window height"""
		if self._hidden_visible:
			self.hidden_frame.pack_forget()
			self._hidden_visible = False
		# Restore window height (stay at top)
		if self.root.winfo_height() >= self.bar_height_expanded:
			self.root.geometry(f"{self.screen.width}x{self.bar_height}+0+0")
		if hasattr(self, '_hide_timer') and self._hide_timer is not None:
			self._hide_timer = None
	
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
