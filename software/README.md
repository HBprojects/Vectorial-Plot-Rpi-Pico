# Real-Time Serial ECG Visualization Software
This software acquires 3-channel ADC signals (Simulated ECG) from a microcontroller over a serial connection, displays them in real time, allows pause/scroll/inspection, computes a heart vector, and saves synchronized data for offline analysis.
Designed for research and laboratory use.
## 1. Quick Start
Requirements
-	Python 3.x
-	NumPy
-	Matplotlib
-	PySerial
-	Microcontroller streaming ADC data via serial
### Run
python python vecto_graph.py
## 2. Critical Configuration (Must Read)
### 2.1 Serial Port
Set the correct serial port before running:
ser_port = 'COM10'  # Change to your port
Examples:
- Windows: COM3
-	Linux: /dev/ttyUSB0
-	macOS: /dev/cu.usbmodemXXXX
### 2.2 Expected ADC Channels (Firmware Match)
Inside read_serial_data() (≈ line 484):
if len(values) == 3:
-	Raspberry Pi Pico firmware → == 3
-	K64F firmware → replace with > 4
This must match the firmware output, or data parsing will fail.
## 3. Keyboard Controls (Core Usage)
| Key | Action | Notes |
|:---:|:-----------|:-----------|
|1| Isolated 5V Lab power supply | Also tested with SWM12-5-N adapter |
|a| Start ADC streaming | Active by default |
|p|	Pause / resume acquisition | Enables scrolling through previously recorded data |
|← / →|	Scroll data | (paused only) |
|j|	Save visible data window | numpy format .npy (paused only) |
|r|	Start recording | Only in K64F firmware, need a MicroSD card |
|d|	Dumie recorded signal | (Not paused) |
|z|	Zero offsets |In K64F firmware only |
|t|	Tune / calibration command | Only in K64F firmware |
|m|	Change actual speed | Fast by default |
## 4. Core Function (Must Understand)
on_key(event)
Handles all user interaction:
-	Controls pause/resume logic
-	Sends commands to the microcontroller
-	Enables data scrolling
-	Extracts, scales, and saves 3-channel data to .npy
This function defines how the user operates the software.
## 5. Typical Workflow
-	Set serial port
-	Connect microcontroller
-	Run the script
- Press p to pause
- Scroll and inspect data
- Press j to save
- Press p to continue in real time mode
- Press d to stream the demo signal (firmware)
## 6. Performance Functions
-	init() – Initializes figures, axes, buffers, and event handlers.
-	format_func() – Formats axis tick labels.
-	update_xspeed() – Changes plot scrolling speed.
-	update_slider() – Syncs slider limits with stored data.
-	onmove() – Tracks mouse movement over the plot.
-	plot_on_click() – Extracts data at a clicked point.
-	handle_resize() – Maintains layout on window resize.
-	calc_heart_vector() – Computes vector representation from 3 channels.
-	calc_per_points() – Computes values at a specific cursor position.
-	update_axs() – Updates plots during animation frames.
## 7. Data Output
Saved File
-	seem_ath20.npy. "seem_ath20" change the name as needed  in program line 352
-	Shape: (1500, 3) by default
- Columns: Channel 1, Channel 2, Channel 3
Saved when pausing (p) then (j).
## 8. Notes
•	Assumes synchronized multi-channel data
•	Timing depends on firmware sampling
•	Intended for experimental and research use
