import sys
import serial
import numpy as np
import matplotlib.pyplot as plt
from numpy import cos, sin, pi
import matplotlib.animation as animation
from matplotlib.widgets import Button
from matplotlib.widgets import Slider
from collections import deque
from matplotlib.backend_bases import MouseEvent
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator, FuncFormatter

ser_port = 'COM10'  # Replace with your serial port
baud_rate = 230400  # Increase the baud rate if possible
timeout = 0.1  # Non-blocking mode

# Create a serial connection
ser = serial.Serial(ser_port, baud_rate, timeout=timeout)

side_lines_color = 'black'#'white'
triangle_color = 'gray'#'orange'
x1_facecolor = '#FBF5F3'#'#FBF5F3' '#FBF5F3'
x2_facecolor = '#FBF5F3'#'#FBF5F3''#154F61'
proy_linesColor = 'gray'#'green'
# Define the circle radius
radius = 1
value1 = 0.0
value2 = 0.0
value3 = 0.0
x_pos = 0.0
y_pos = 0.0

offset1 = 150#-530
offset2 = 50#-570
offset3 = -50#10

# Calculate the side length of the equilateral triangle circumscribed around the circle
side_length = 2 * radius * np.sqrt(3)

# Define the number of data points to display in the real-time plot
max_data_points = 1500#was 1500
spd_idx = 1
paused = False
is_over_plot = False
on_click_flag = False
count_mouse_pos = 0
mouseXpos = 1
xm_val = 0
# Initialize NumPy arrays to store data
full_x_data = np.zeros(max_data_points)  # Dynamically grow as needed
D1_data = np.zeros(max_data_points)  # Dynamically grow as needed
D2_data = np.zeros(max_data_points)  # Dynamically grow as needed
D3_data = np.zeros(max_data_points)  # Dynamically grow as needed

# Initialize a circular buffer for real-time plotting
x_data = np.zeros(max_data_points)
y1_data = np.zeros(max_data_points)
y2_data = np.zeros(max_data_points)
y3_data = np.zeros(max_data_points)
index = 0

# Define the width ratio (left plot is 1.5 times wider than the right plot)
left_width = 1.4
right_width = 1
# Create the figure and subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'width_ratios': [left_width, right_width]})
#fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))

fig.tight_layout()
fig.subplots_adjust(top=0.956, left=0.054)# Remove space between subplots
fig.subplots_adjust(wspace=0.0)# Remove space between subplots
fig.subplots_adjust(bottom=0.15)

line1, = ax1.plot([], [], label="DI", color='black')
line2, = ax1.plot([], [], label="DII", color='black')
line3, = ax1.plot([], [], label="DIII", color='black')
# Set plot labels
ax1.set_title("Leads DI, DII, DIII 5mm 1mV")

# Define the expected X, Y-axis range
y1_min, y1_max = -100, 200
x1_min, x1_max = 0, max_data_points
ax1.set_ylim(y1_min, y1_max)
ax1.set_xlim(x1_min, x1_max)
ax1.set_facecolor(x1_facecolor)
ax1.set_aspect('auto')

crosshair_h = ax1.axhline(color='gray', linestyle='--')  # Horizontal line
crosshair_i = ax1.axhline(color='gray', linestyle='--')  # Horizontal line
crosshair_j = ax1.axhline(color='gray', linestyle='--')  # Horizontal line
crosshair_v = ax1.axvline(color='gray', linestyle='--')  # Vertical line
crosshair_h.set_visible(False)
crosshair_i.set_visible(False)
crosshair_j.set_visible(False)
crosshair_v.set_visible(False)

last_point1, = ax1.plot([], [], 'bo')  # blue dot for DI
actual_point1, = ax1.plot([], [], 'bo')  # blue dot for DI
last_point2, = ax1.plot([], [], 'o', color='orange')  # dot for DII
actual_point2, = ax1.plot([], [], 'o', color='orange')  # dot for DII
last_point3, = ax1.plot([], [], 'go')  #dot for DIII
actual_point3, = ax1.plot([], [], 'go')  #dot for DIII

# Define the vertices of the equilateral triangle
# One side will be horizontal at the top
angles = np.deg2rad([60, 180, 300])  # Vertices of the equilateral triangle
triangle_x = side_length * np.cos(angles) / np.sqrt(3)
triangle_y = side_length * np.sin(angles) / np.sqrt(3)

# Adjust to make sure the top side is horizontal
# Rotate -30 degrees to make the top horizontal
rotation_angle = -30  # Degrees to rotate counterclockwise
rotation_matrix = np.array([
    [np.cos(np.deg2rad(rotation_angle)), -np.sin(np.deg2rad(rotation_angle))],
    [np.sin(np.deg2rad(rotation_angle)),  np.cos(np.deg2rad(rotation_angle))]
])
rotated_triangle = np.dot(rotation_matrix, np.vstack((triangle_x, triangle_y)))

# Close the triangle path
triangle_x = np.append(rotated_triangle[0], rotated_triangle[0][0])
triangle_y = np.append(rotated_triangle[1], rotated_triangle[1][0])

# Precompute triangle side vectors and lengths for projection calculations
triangle_vectors = [(triangle_x[j+1] - triangle_x[j], triangle_y[j+1] - triangle_y[j]) for j in range(3)]

# Create a slider for scrolling through the data
ax_slider = plt.axes([0.1, 0.05, 0.8, 0.03])
slider = Slider(ax_slider, '', 0, 1, valinit=0, valstep=4)
slider.set_active(False)  # Slider inactive until paused

x2_min, x2_max = -2.3, 2.2
y2_min, y2_max = -2.5, 2
ax1.set_aspect('equal', adjustable='datalim')  # Keep square aspect ratio
ax2.set_xlim(x2_min, x2_max)
ax2.set_ylim(y2_min, y2_max) 
ax2.set_title("Vector Plot")
ax2.set_anchor('C') 

# Remove y-axis number values but keep grid lines
ax1.tick_params(axis='y', which='both', length=0)  # Remove tick marks
ax1.set_yticklabels([])  # Remove y-axis labels but keep ticks for the grid

# Draw the circle with radius 1
circle = plt.Circle((0, 0), radius, color='lightblue', fill=False, linestyle='dotted')
ax2.add_artist(circle)

#Draw origin circles
circ1 = plt.Circle((0, 1), 0.04, color='black', fill=False)
ax2.add_artist(circ1)
circ2 = plt.Circle((0.866, -0.5), 0.04, color='black', fill=False)
ax2.add_artist(circ2)
circ3 = plt.Circle((-0.866, -0.5), 0.04, color='black', fill=False)
ax2.add_artist(circ3)

# Plot the equilateral triangle with the top side horizontal
ax2.plot(triangle_x, triangle_y, color=triangle_color, lw=1.5)

# Add text labels to the corners of the triangle
ax2.set_facecolor(x2_facecolor)
ax2.set_xticks([])  # Remove x-axis ticks
ax2.set_yticks([])  # Remove y-axis ticks
#for spine in ax2.spines.values():
#Signal rectangles 
rect1 = Rectangle((0.985,  0.666), 0.02, 0.333, transform=ax1.transAxes, edgecolor='black', lw=2, fill=True, facecolor=x1_facecolor)
ax1.add_patch(rect1)
rect2 = Rectangle((0.985, 0.333), 0.02, 0.333, transform=ax1.transAxes, edgecolor='black', lw=2, fill=True, facecolor=x1_facecolor)
ax1.add_patch(rect2)
rect3 = Rectangle((0.985, 0.0), 0.02, 0.333, transform=ax1.transAxes, edgecolor='black', lw=2, fill=True, facecolor=x1_facecolor)
ax1.add_patch(rect3)


# Draw lines from the center of the triangle sides to the perpendicular intersection points
midpoints = [((triangle_x[i] + triangle_x[i + 1]) / 2,
              (triangle_y[i] + triangle_y[i + 1]) / 2) for i in range(3)]

mid_x, mid_y = midpoints[1]
                #proy_lines[j+1].set_data([px-0.4, mid_x-0.562], [py-0.23 , mid_y])
x2_min, x2_max = -2.3, 2.2
new_line_1, = ax2.plot([x2_min, x2_min+0.77], [-0.25, -0.25], color=proy_linesColor, linestyle='--') 
new_line_2, = ax2.plot([x2_min + 0.15, 0.318], [y2_min + 0.15, y2_min + 0.15], color=proy_linesColor, linestyle='--') 

new_point_ax2 = ((y2_max - y2_min)/6)+y2_min
new_line_3, = ax2.plot([x2_min + 0.15, x2_min + 0.15], [y2_min + 0.15, new_point_ax2], color=proy_linesColor, linestyle='--') 
new_line_4, = ax2.plot([x2_min + 0.15, x2_min], [new_point_ax2, new_point_ax2], color=proy_linesColor, linestyle='--') 

new_point_ax2 = y2_max - ((y2_max - y2_min)/6)
new_line_5, = ax2.plot([x2_min + 0.15, x2_min + 0.15], [y2_max - 0.6, new_point_ax2], color=proy_linesColor, linestyle='--') 
new_line_6, = ax2.plot([x2_min + 0.15, x2_min], [new_point_ax2, new_point_ax2], color=proy_linesColor, linestyle='--') 
#proy_lines[j].set_data([x_pos, y2_min], [py + 0.4, py + 0.4])

#trace, = ax2.plot([], [], '.-', lw=1, ms=2, color='lightblue', zorder=1)
trace, = ax2.plot([], [], '-', lw=1, ms=2, color='gray', zorder=1)
vector, = ax2.plot([], [], 'o-', lw=3, color='#D8711C', zorder=2)
perpendicular_lines = [ax2.plot([], [], color=proy_linesColor, linestyle='--')[0] for _ in range(3)]
proy_lines = [ax2.plot([], [], color=proy_linesColor, linestyle='--')[0] for _ in range(5)]

#connector_lines = [ax2.plot([], [], 'o-', lw=3, color=side_lines_color)[0] for _ in range(3)]

connector_lines = []
for _ in range(3):
    line, = ax2.plot(
        [], [], 
        '-',                       # just a solid line
        lw=2,
        color=side_lines_color,
        marker=(3, 1, 0),          # a 3‑sided marker (triangle), 0° initial
        markevery=[-1],            # only draw that marker at the *last* point
        markersize=10,             # arrow‑head size
        markerfacecolor='white',    # fill color (change as you like)
        markeredgecolor=side_lines_color
    )
    connector_lines.append(line)

time_template = 'time = %.1fs'
time_text = ax2.text(0.05, 0.9, '', transform=ax2.transAxes)

ax_button = plt.axes([0.01, 0.05, 0.05, 0.04])  # Position: [x, y, width, height]
button1 = Button(ax_button, '←→')  # Create button

text_box1 = None
# Variables to store history of points
##history_x = []
#history_y = []
history_x = deque(maxlen=1500)  # Automatically discard older data when full
history_y = deque(maxlen=1500)#was 1500

def init():
    line1.set_data([], [])
    line2.set_data([], [])
    line3.set_data([], [])
    ax1.text(-0.07, 0.9, '  DI', style='italic', transform=ax1.transAxes,
             bbox={'facecolor': 'cyan', 'alpha': 0.5, 'pad': 10})
    ax1.text(-0.07, 0.5, ' DII', style='italic', transform=ax1.transAxes,
            bbox={'facecolor': 'cyan', 'alpha': 0.5, 'pad': 10})
    ax1.text(-0.07, 0.1, 'DIII', style='italic', transform=ax1.transAxes,
            bbox={'facecolor': 'cyan', 'alpha': 0.5, 'pad': 10})

    ax1.xaxis.set_major_formatter(FuncFormatter(format_func))
    ax1.set_xlabel('25  /S')

    ax1.xaxis.set_major_locator(MultipleLocator(50))  # Major ticks every 100 points
    ax1.xaxis.set_minor_locator(MultipleLocator(10))   # Minor ticks every 20 points
    ax1.yaxis.set_major_locator(MultipleLocator(50))  # Major ticks every 5 units
    ax1.yaxis.set_minor_locator(MultipleLocator(10))  # Minor ticks every 1 unit

    ax1.grid(which='major', color='#CCCCCC', linestyle='--')
    ax1.grid(which='minor', color='#CCCCCC', linestyle=':')
    ax1.grid(True, which='both')

    xc = float(((triangle_x[0]+triangle_x[1])/2)-0.1)
    yc = float(triangle_y[0])+0.1
    ax2.text(xc, yc, f'DI', fontsize=12, ha='center', color='black')
    #Left corner
    xc = float(triangle_x[0]+0.1)
    ax2.text(xc-0.25, yc, f'+', fontsize=14, ha='center', color='red')#red
    #ax2.text(xc, yc, f'+ LA', fontsize=12, ha='center', color='white')
    ax2.text(xc, yc, 'LA', fontsize=10, style='italic', ha='center', color='white',
         bbox={'facecolor': 'black', 'alpha': 0.5, 'boxstyle': 'circle', 'pad': 0.4})
    xc = float(triangle_x[0]+0.12)
    yc = float(triangle_y[0])-0.15
    ax2.text(xc, yc, f'-', fontsize=24, ha='center', color='black')
    xc = float(triangle_x[1]-0.1)
    yc = float(triangle_y[1])+0.1
    #Right corner
    ax2.text(xc + 0.25, yc, f'-', fontsize=24, ha='center', color='black')
    #ax2.text(xc, yc, f'RA -', fontsize=12, ha='center', color='black')
    ax2.text(xc, yc, 'RA', fontsize=10, style='italic', ha='center', color='black',
         bbox={'facecolor': 'white', 'alpha': 0.5, 'boxstyle': 'circle', 'pad': 0.4})
    yc = float(triangle_y[1])-0.15
    ax2.text(xc, yc, f'-', fontsize=24, ha='center', color='black')

    #ax2.text(xc, yc, f'-', fontsize=14, ha='center', color='black')
    xc = float(triangle_x[1]+0.7)
    yc = float(((triangle_y[1]+triangle_y[2])/2)-0.1)
    ax2.text(xc, yc, f'DII', fontsize=12, ha='center', color='black')
    xc = float(triangle_x[2]+1.2)
    yc = yc + 0.1
    ax2.text(xc, yc, f'DIII', fontsize=12, ha='center', color='black')
    #Low corner
    xc = float(triangle_x[2])
    yc = float(triangle_y[2])-0.15
    #ax2.text(xc, yc, f'+ LL +', fontsize=12, ha='center', color='red')
    ax2.text(xc, yc, 'LL', fontsize=10, style='italic', ha='center', color='black',
         bbox={'facecolor': 'red', 'alpha': 0.5, 'boxstyle': 'circle', 'pad': 0.4})
    ax2.text(xc - 0.22, yc + 0.18, f'+', fontsize=14, ha='center', color='red')
    ax2.text(xc + 0.22, yc + 0.18, f'+', fontsize=14, ha='center', color='red')

    yc = y2_max - 1.5
    ax2.text(x2_min + 0.1, y2_max - 0.2, f'+', fontsize=12, ha='center', color='red')
    ax2.text(x2_min + 0.1, yc, f'-', fontsize=18, ha='center', color='black')
    ax2.text(x2_min + 0.1, yc - 0.2, f'+', fontsize=12, ha='center', color='red')
    ax2.text(x2_min + 0.1, yc - 1.5, f'-', fontsize=18, ha='center', color='black')
    ax2.text(x2_min + 0.1, yc - 1.7, f'+', fontsize=12, ha='center', color='red')#red
    ax2.text(x2_min + 0.1, y2_min + 0.1, f'-', fontsize=18, ha='center', color='black')

    return [line1, line2, line3]

def format_func(value, tick_number):
    return f"{value / 250:.2f}"  # was 160Convert points to seconds

def update_xspeed(event):
    global spd_idx
    spd_idx += 1
    if spd_idx > 5:
        spd_idx = 1

def on_key(event):
    global paused, spd_idx
    if event.key == 'p':
        paused = not paused
        slider.set_active(paused)  # Enable or disable the slider
        if paused:
            ser.write('paus\n'.encode('ascii'))
            update_slider()
            new_val = len(full_x_data) - max_data_points
            slider.set_val(new_val)
            

            scroll_position = int(slider.val)
            start_idx = scroll_position
            end_idx = min(start_idx + max_data_points, len(full_x_data))
            # 1. Slice your individual data channels
            d1_slice = D1_data[start_idx:end_idx]
            d2_slice = D2_data[start_idx:end_idx]
            d3_slice = D3_data[start_idx:end_idx]
            
            d1_slice = d1_slice[:] - 150
            d2_slice = d2_slice[:] - 50
            d3_slice = d3_slice[:] + 50
            d1_slice = d1_slice[:] * 0.02
            d2_slice = d2_slice[:] * 0.02
            d3_slice = d3_slice[:] * 0.02
            
            # 2. Stack them horizontally to get shape (600, 3)
            combined_data = np.column_stack((d1_slice, d2_slice, d3_slice))
            # 3. Verify and Save
            print(combined_data.shape)
            np.save('seem_ath20.npy', combined_data)


        else:
            ser.write('adc0\n'.encode('ascii'))

        ax1.figure.canvas.draw_idle()

    if event.key == 'j':    
        if paused:
            print(combined_data.shape)  # Should show (600, 3)
            #np.save('my_data_3_channels.npy', combined_data)
            combined_data = np.column_stack((d1_slice, d2_slice, d3_slice))
            np.save('seem_ath20.npy', combined_data)


    if event.key == 't':    
        ser.write('tune\n'.encode('ascii'))
        print("tune")
    if event.key == 'z':    
        ser.write('z000\n'.encode('ascii'))
        print("zero")
    if event.key == 'a':    
        ser.write('adc0\n'.encode('ascii'))
        print("adc")
    if event.key == 'r':    
        ser.write('reca\n'.encode('ascii'))
        print("recording")
    if event.key == 'd':    
        ser.write('dumi\n'.encode('ascii'))
        print("Recorded signal")
    if event.key == 'm':    
        spd_idx += 1
        if spd_idx > 5:
            spd_idx = 1
    if event.key == 'right':
        if paused:
            # Move slider to the right
            update_slider()
            new_val = min(slider.val + 8, slider.valmax)
            slider.set_val(new_val)  # Update slider position
    elif event.key == 'left':
        if paused:
            # Move slider to the left
            update_slider()
            new_val = max(slider.val - 8, slider.valmin)
            slider.set_val(new_val)  # Update slider position        

    
def update_slider():
        # Update the slider range dynamically
        if len(full_x_data) > max_data_points:
            slider.valmax = len(full_x_data) - max_data_points
            slider.ax.set_xlim(0, slider.valmax)
            print(len(full_x_data))
        else:
            slider.valmax = 1
            slider.ax.set_xlim(0, 1)

def onmove(event):
    global is_over_plot, count_mouse_pos, mouseXpos, xm_val
    x_value = event.xdata
    if paused:#
        if event.inaxes == ax1:
            is_over_plot = True
            
            x_value = int(event.xdata)# - count_mouse_pos
            xm_val = x_value
            slide_idx = int(slider.valmax)
            #print(f"raw X: {x_value}")
            #print(f"count X: {count_mouse_pos}")
            #print(f"Full data : {len(full_x_data)}")
            xmouse_idx = count_mouse_pos - max_data_points - slide_idx
            if x_value is not None:
                # Calculate the local index in the visible data
                mouseXpos = x_value - xmouse_idx
                #print(f"calc X: {mouseXpos}")
                #print(f"len data=:{len(D1_data)}")
                
            crosshair_h.set_visible(True)
            crosshair_i.set_visible(True)
            crosshair_j.set_visible(True)
            crosshair_v.set_visible(True)
            

        else:
            is_over_plot = False

dt_old_val = 0.0
def plot_on_click (event):
    global on_click_flag, text_box1, dt_old_val
    if event.inaxes == ax1:  # If the mouse is within the plot area
        on_click_flag = True
        if event.ydata > 0:
            point = D1_data[mouseXpos]
        if event.ydata <= 0:
            point = D3_data[mouseXpos]
        print(f"Mouse clicked at: (x={mouseXpos}, y={point}), button={event.button}")


        if event.ydata > 100:
            point = D1_data[mouseXpos] - offset1
            txt_str = " DI  Δy = "
        elif event.ydata <= 0:
            point = D3_data[mouseXpos] - offset3
            txt_str = "DIII Δy = "
        else:
            point = D2_data[mouseXpos] - offset2
            txt_str = "DII  Δy = "
        point = point/50

        dt_val = (mouseXpos - dt_old_val)/940 #was 800
        dt_old_val = mouseXpos
        textBX_str = f"Δt = {dt_val:.3f} S {txt_str}{point:.3f} mV"  # Format text
        
        if text_box1 is None:
            text_box1 = fig.text(0.7, 0.1, textBX_str,
                                    fontsize=12, bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
        else:
            text_box1.set_text(textBX_str)  # 🔥 Only update the text, NOT redraw the box
                                    
        #fig.canvas.draw_idle()
        plt.pause(0.01)


def handle_resize(event):
    ax1.set_xlim(x1_min, x1_max)
    ax1.set_ylim(y1_min, y1_max)
    ax1.grid(which='both')
    ax2.set_xlim(x2_min, x2_max)
    ax2.set_ylim(y2_min, y2_max)
    ax2.set_anchor('C')

# Function to read serial data
def read_serial_data():
    global value1, value2, value3, x_pos, y_pos, full_x_data, D1_data, D2_data, D3_data, y1_data, y2_data, y3_data, index, count_mouse_pos
    read_count = 0  # Limit the number of reads per frame
    idx = 0   
    while ser.in_waiting and read_count < 40:#enable for not delaya real time plot in fast serial baud rate
        raw_data = ser.readline()
        #data = data[11:]#to remove bad first character
        data = raw_data.decode('utf-8', errors='ignore').strip()
        idx += 1
        try:
            values = data.split(',')
            if len(values) == 3: #> 4:#4 for k64f
                value1 = float(values[0])
                value2 = float(values[1])
                value3 = float(values[2])
                #print(f"data: {value1} , {value2}, {value3}")
                #print(value1 + value2 + value3)
                '''
                value1 = value1 + 78
                value2 = value2 -30 #invert
                value3 = value3 - 48
                '''
                value1 = (value1 / 3) #+ 0.001
                value2 = (value2 / 3) #- 0.001
                value3 = (value3 / 3) #- 0.001
            if idx >= spd_idx:
            
                radius, angle = calc_heart_vector(value1, value2, value3)
                
                value1 = (value1 * 9) + offset1#+ 150
                value2 = (value2 * -9) + offset2
                value3 = (value3 * 9) + offset3

                if radius is None or angle is None:
                    return []  # No valid data received

                # Calculate the current x, y position
                x_pos = radius * np.cos(angle)
                y_pos = radius * np.sin(angle)
                
                # Update history
                history_x.append(x_pos)
                history_y.append(y_pos)
            
                new_x_value = full_x_data[index - 1] + 1 if index > 0 else 0
                # Update full_x_data and D1_data
                if index < len(full_x_data):
                    full_x_data[index] = new_x_value
                    D1_data[index] = value1
                    D2_data[index] = value2
                    D3_data[index] = value3
                else:
                    full_x_data = np.append(full_x_data, new_x_value)
                    D1_data = np.append(D1_data, value1)
                    D2_data = np.append(D2_data, value2)
                    D3_data = np.append(D3_data, value3)

                y1_data[index % max_data_points] = value1
                y2_data[index % max_data_points] = value2
                y3_data[index % max_data_points] = value3
                index += 1
                count_mouse_pos += 1
                idx = 0
        except ValueError:
            print(f"Ignored invalid data: {data}")
        read_count += 1

def calc_heart_vector(ch1, ch2, ch3):
    # Define the vectors based on input values
    #print(f"data: {ch1} , {ch2}, {ch3}")
    #print(ch2-ch1-ch3)
    #original ch1 y ch3
    v1_magnitude = ch1/3
    v1_theta = np.radians(0)  # theta for lead I
    v1_x = v1_magnitude * np.cos(v1_theta)
    v1_y = v1_magnitude * np.sin(v1_theta)
    
    v3_magnitude = ch3/3

    # Heart vector calculations #np.sqrt(3) = 1.732050807568877
    vh_x = v1_magnitude + 0.00001
    vh_y = (-vh_x / 1.732050807568877) - (2 * v3_magnitude / 1.732050807568877)
    vh_magnitude = vh_x / np.cos(np.arctan(vh_y / vh_x))

    # Calculate angle between heart vector and lead I vector
    angle = np.degrees(np.arctan2(vh_y, vh_x) - np.arctan2(v1_y, v1_x))
    angle = angle + 360 if angle < 0 else angle  # Normalize angle to [0, 360]
    
    #angle = angle - 120 #- 120 ch3 & ch2 + 120 ch2 & ch1 0 ch1 & ch3
    angle_rad = np.deg2rad(angle)  # Convert angle to radians

    return vh_magnitude, angle_rad

def calc_per_points (x_pos, y_pos):
    # Calculate and update perpendicular lines
    perpendicular_points = []
    T_lengths = [dx * dx + dy * dy for dx, dy in triangle_vectors]
    # Compute projection and closest points
    for j, ((dx, dy), T_lengths) in enumerate(zip(triangle_vectors, T_lengths)):
        x1, y1 = triangle_x[j], triangle_y[j]

        # Projection of point (x_pos, y_pos) onto the line defined by (x1, y1) to (x2, y2)
        t = ((x_pos - x1) * dx + (y_pos - y1) * dy) / T_lengths
        t = np.clip(t, 0, 1)  # Clamping t to be within the line segment (faster with NumPy)

        # Finding the closest point
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        perpendicular_points.append((closest_x, closest_y))
    for j, (perp_line, (px, py)) in enumerate(zip(perpendicular_lines, perpendicular_points)):
        if j == 0:
            perp_line.set_data([x_pos, px], [y_pos, py + 0.4])
            proy_lines[j].set_data([x_pos, x2_min + 0.15], [py + 0.4, py + 0.4])
        elif j == 1:
            perp_line.set_data([x_pos, px], [y_pos, py])
            proy_lines[j].set_data([px, px - 0.39], [py, py - 0.225])
            mid_x, mid_y = midpoints[j]
            proy_lines[j+1].set_data([px - 0.4, x2_min+0.77], [py - 0.23, -0.25])
        else:
            perp_line.set_data([x_pos, px], [y_pos, py])
            proy_lines[3].set_data([px, px + 0.39], [py, py - 0.225])
            x1, y1 = triangle_x[j], triangle_y[j]
            proy_lines[4].set_data([px + 0.39, x1 + 0.318], [py - 0.225, y1 - 0.35])

        # Connect midpoints of the triangle to the intersection points

        mid_x, mid_y = midpoints[j] #original line
        connector_lines[j].set_data([mid_x, px], [mid_y, py]) #original line
        
        tx = px - mid_x
        ty = py - mid_y
        if  j == 0:
            if tx < 0:
                connector_lines[j].set_color('#424553')
                connector_lines[j].set_marker((3, 0, 90))
            else:
                connector_lines[j].set_color('#EF5350')
                connector_lines[j].set_marker((3, 0, -90))
        else:
            if ty > 0:
                connector_lines[j].set_color('#424553')
                connector_lines[j].set_marker((3, 0, 30))
            else:
                connector_lines[j].set_color('#EF5350')
                connector_lines[j].set_marker((3, 0, -30))
        if  j == 2:
            if ty > 0:
                connector_lines[j].set_marker((3, 0, -30))
            else:
                connector_lines[j].set_marker((3, 0, 30))
        

x_vals =[]
y1_vals =[]
# Function to update the plot
old_scroll_val = 0
def update_axs(frame):
    global snap_cursor, x_pos, y_pos, full_x_data, D1_data, D2_data, \
         D3_data, y1_data, y2_data, y3_data, index, old_scroll_val, on_click_flag

    if not paused:
        read_serial_data()
        data_count = min(index, max_data_points)# Determine the number of data points collected so far

        # Update and trace
        trace.set_data(history_x, history_y)
        vector.set_data([0, x_pos], [0, y_pos])
        #time_text.set_text(time_template % (i * dt))

        # Calculate and update perpendicular lines
        calc_per_points (x_pos, y_pos)



        if index > max_data_points:
            x_vals = np.arange(index - max_data_points, index)
            line1.set_data(x_vals, y1_data)
            line2.set_data(x_vals, y2_data)
            line3.set_data(x_vals, y3_data)
            ax1.set_xlim(index - max_data_points, index)
            
            
            # Here, we need to find the most recent point from the read_serial_data
            # The actual point corresponds to the last index read
            last_index = max_data_points - ((index - 1) % max_data_points)# Last data point index in the buffer
            actual_index = (index - 1) % max_data_points
            
            last_point1.set_data([index-last_index], [y1_data[actual_index]])  # Latest point for DI
            last_point2.set_data([index-last_index], [y2_data[actual_index]])  # Latest point for DII
            last_point3.set_data([index-last_index], [y3_data[actual_index]])  # Latest point for DII
            actual_point1.set_data([index-12], [y1_data[actual_index]])
            actual_point2.set_data([index-12], [y2_data[actual_index]])
            actual_point3.set_data([index-12], [y3_data[actual_index]])  # Latest point for DIII
            
        else:
            line1.set_data(np.arange(data_count), y1_data[:data_count])
            line2.set_data(np.arange(data_count), y2_data[:data_count])
            line3.set_data(np.arange(data_count), y3_data[:data_count])
            ax1.set_xlim(0, data_count - 1)

            # Here, we need to find the most recent point from the read_serial_data
            last_point1.set_data([data_count - 1], [y1_data[data_count - 1]])  # Latest point for DI
            last_point2.set_data([data_count - 1], [y2_data[data_count - 1]])  # Latest point for DII
            last_point3.set_data([data_count - 1], [y3_data[data_count - 1]])
            actual_point1.set_data([data_count - 1], [y1_data[data_count - 1]])
            actual_point2.set_data([data_count - 1], [y2_data[data_count - 1]])
            actual_point3.set_data([data_count - 1], [y3_data[data_count - 1]])
        
        if len(full_x_data) > 10 * max_data_points:
            full_x_data = full_x_data[-8 * max_data_points:]  # Keep the last x*max_data_points
            D1_data = D1_data[-8 * max_data_points:]
            D2_data = D2_data[-8 * max_data_points:]
            D3_data = D3_data[-8 * max_data_points:]
            index = len(D3_data)
            print(index)

        return [line1, line2, line3, vector, trace, last_point1, last_point2, last_point3,
             actual_point1, actual_point2, actual_point3] + perpendicular_lines + connector_lines + proy_lines
    else:
        scroll_position = int(slider.val)
        start_idx = scroll_position
        end_idx = min(start_idx + max_data_points, len(full_x_data))

        # Set the x and y data for the plot
        x_data = full_x_data[start_idx:end_idx]

        #y_data = D1_data[start_idx:end_idx]

        if len(x_data) > 1:
            
            line1.set_data(x_data, D1_data[start_idx:end_idx])
            line2.set_data(x_data, D2_data[start_idx:end_idx])
            line3.set_data(x_data, D3_data[start_idx:end_idx])

            if x_data[0] == x_data[-1]:
                ax1.set_xlim(x_data[0] - 1, x_data[-1] + 1)
            else:
                ax1.set_xlim(x_data[0], x_data[-1])
                
            if scroll_position != old_scroll_val:
                for i in range(len(line1.get_xdata())):  # Loop through the points in line1, line2, and line3
                    point1 = line1.get_ydata()[i]
                    point2 = line2.get_ydata()[i]
                    point3 = line3.get_ydata()[i]

                    point1 = (point1 - offset1) / 9
                    point2 = (point2 - offset2) / 9#point2 = (point2 - offset3) / 12
                    point3 = (point3 - offset3) / 9
                    '''
                    value1 = (value1 * 12) + 130#+ 150
                    value2 = (value2 * -12) + 50
                    value3 = (value3 * 12) - 50
                    '''
                    radius, angle = calc_heart_vector(point1, point2, point3)
                    
                    x_pos = radius * np.cos(angle)
                    y_pos = radius * np.sin(angle)

                    history_x.append(x_pos)
                    history_y.append(y_pos)
                trace.set_data(history_x, history_y)
                old_scroll_val = scroll_position
                
            if is_over_plot:
                if len(D1_data) >= mouseXpos > 0:
                    point1 = D1_data[mouseXpos]
                    point2 = D2_data[mouseXpos]
                    point3 = D3_data[mouseXpos]
                    
                    crosshair_h.set_ydata([point1, point1])  # Horizontal crosshair at y_value
                    crosshair_i.set_ydata([point2, point2])  # Horizontal crosshair at y_value
                    crosshair_j.set_ydata([point3, point3])  # Horizontal crosshair at y_value
                    crosshair_v.set_xdata([xm_val])  # Vertical crosshair at x_value
                    
                    if on_click_flag:
                        last_point1.set_data([xm_val], [point1])  # Latest point for DI
                        last_point2.set_data([xm_val], [point2])  # Latest point for DII
                        last_point3.set_data([xm_val], [point3])  # Latest point for DIII
                        on_click_flag = False
                    ''''
                    point1 = (point1 - 150)/12
                    point2 = (point2 - 50 )/12
                    point3 = (point3 + 50)/12 
                    '''
                    point1 = (point1 - offset1) / 9
                    point2 = (point2 - offset2) / 9
                    point3 = (point3 - offset3) / 9
                    
                    radius, angle = calc_heart_vector(point1, point2, point3)
                    
                    ang = np.degrees(angle)
                    ang = 360 - ang
                    if radius < 0:
                        ang = ang - 180
                    print(f"angle ={ang}")
                    x_pos = radius * np.cos(angle)
                    y_pos = radius * np.sin(angle)
                    vector.set_data([0, x_pos], [0, y_pos])
                    calc_per_points (x_pos, y_pos)


        else:
            ax1.set_xlim(0, max_data_points)
        #return line1, line2, line3
        return [line1, line2, line3, vector, trace, crosshair_h, crosshair_i, crosshair_j, crosshair_v,
             last_point1, last_point2, last_point3] + perpendicular_lines + connector_lines + proy_lines

# Create the animation
#ani = animation.FuncAnimation(fig, animate, cache_frame_data=False, blit=True, interval=20)
fig.canvas.mpl_connect('key_press_event', on_key)
fig.canvas.mpl_connect('resize_event', handle_resize)
fig.canvas.mpl_connect('motion_notify_event', onmove)
fig.canvas.mpl_connect('button_press_event', plot_on_click)  # Capture mouse click

button1.on_clicked(update_xspeed)  # Connect button to function

#ani_ax1 = animation.FuncAnimation(fig, update, cache_frame_data=False, blit=True, interval=2)
ani = animation.FuncAnimation(
    fig, update_axs, cache_frame_data=False, init_func=init, blit=True, interval=3)

# Show the plot
if __name__ == "__main__":
    plt.show()
# Don't forget to close the serial connection after use

ser.close()
