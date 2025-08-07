
# Python program for Detection of a  
# specific color(blue here) using OpenCV with Python 
import cv2 
import numpy as np

# For tracking the movement
from collections import deque
import imutils
import time
from pathlib import Path
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('video', type=str, help='path to video file. Videos located in ../data/videos/')
args = parser.parse_args()

# Array que guarda las posiciones de cada objeto (deque es como un array mas eficiente)
pts_red = deque()
pts_blue= deque()
pts_yellow = deque()
pts_body = deque()
pts_times = deque()




videofile = args.video
video_path = videofile.replace(".mp4", "")
exp_name = Path(video_path).stem
script_dir = Path(__file__).parent
project_root = script_dir.parent
outfile = project_root / "data" / "legs_tracking" / f"{exp_name}.txt"
print(project_root)
print(outfile)
lower_red = np.array([130,0,210])
upper_red = np.array([180,255,255])

alpha = 2
beta = 40

white_thresh = 50

  
# Lee el video del fichero
cap = cv2.VideoCapture(videofile)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

upper_left = (0, 600)
bottom_right = (width, 1500)


# Calcula la media de todos los frames para obtener el fondo
print("Getting background...")
ret, old_frame = cap.read()
region = old_frame[upper_left[1] : bottom_right[1], upper_left[0] : bottom_right[0]]
norm = cv2.convertScaleAbs(region, alpha=alpha, beta=beta)
old_gray = cv2.cvtColor(norm, cv2.COLOR_BGR2GRAY)

background_frame = np.zeros_like(old_gray, dtype=np.int64)
n_frames = 0
while(1):
	ret, frame = cap.read()
	if not ret:
		print('No frames grabbed!')
		break

	region = frame[upper_left[1] : bottom_right[1], upper_left[0] : bottom_right[0]]
	norm = cv2.convertScaleAbs(region, alpha=alpha, beta=beta)

	frame_gray = cv2.cvtColor(norm, cv2.COLOR_BGR2GRAY)
	background_frame += frame_gray
	n_frames += 1


background_frame = np.floor_divide(background_frame, n_frames)
background_frame = background_frame.astype(np.uint8)
print("Background obtained!\n")


# Lee el video de nuevo
cap = cv2.VideoCapture(videofile)
  
# This drives the program into an infinite loop. 
while(1):
	#time.sleep(1)
	# Captures the live stream frame-by-frame 
	_, frame = cap.read()

	if frame is None:
		print("no frame")
		break

	### Tracking de la pata roja

	frame_time = cap.get(cv2.CAP_PROP_POS_MSEC)
	#pts_times.append(frame_time)

	region = frame[upper_left[1] : bottom_right[1], upper_left[0] : bottom_right[0]]

	# Hace la imagen mas pequeña para que sea mas manejable y le aplica blur para quitar "impurezas"
	region_resized = region# imutils.resize(region, width=600)
	blurred = cv2.GaussianBlur(region_resized, (11, 11), 0)

	# Converts images from BGR to HSV 
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)


	 
	# Range for upper range
	mask2 = cv2.inRange(hsv,lower_red,upper_red)
	 
	# Generating the final mask to detect red color
	mask_red = mask2

	# Junta las mascaras y les aplica un par de filtros para quitar "impurezas"
	mask_total = mask_red
	mask_total = cv2.erode(mask_total, None, iterations=2)
	mask_total = cv2.dilate(mask_total, None, iterations=2)


	####################################################
	# Encontrar el contorno de los colores y el centro #
	####################################################

	######
	# Red
	cnts_red = cv2.findContours(mask_red.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts_red = imutils.grab_contours(cnts_red)
	center_red = None

	# only proceed if at least one contour was found
	if len(cnts_red) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts_red, key=cv2.contourArea)
		cv2.drawContours(region_resized, [c], 0, (0,0,255), 3)
		
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)

		try:
			center_red = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		except:
			pass

 
		# only proceed if the radius meets a minimum size
		#if radius > 10:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			#cv2.circle(region_resized, (int(x), int(y)), int(radius),(0, 255, 255), 2)
			#cv2.circle(region_resized, center_red, 5, (0, 0, 255), -1)
 
	



	### Tracking del cuerpo del robot
	norm = cv2.convertScaleAbs(region, alpha=alpha, beta=beta)
	frame_gray = cv2.cvtColor(norm, cv2.COLOR_BGR2GRAY)


	frameDelta = cv2.absdiff(background_frame, frame_gray)
	thresh = cv2.threshold(frameDelta, white_thresh, 255, cv2.THRESH_BINARY)[1]

	center_body = np.median(np.argwhere(thresh), axis=0)

	



	# update the points queue
	if center_red:
		pts_times.append(frame_time)
		pts_red.append(center_red)
		pts_body.append((int(center_body[1]), int(center_body[0])))


	# loop over the set of tracked points
	for i in range(1, len(pts_red)):
		# if either opts_timesf the tracked points are None, ignore
		# them
		if pts_red[i - 1] is None or pts_red[i] is None:
			continue
 
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		#thickness = int(np.sqrt(1 / float(i + 1)) * 2.5)
		cv2.line(region_resized, pts_red[i - 1], pts_red[i], (0, 0, 255), 3)

	region_resized = cv2.circle(region_resized, (int(center_body[1]), int(center_body[0])), 15, [255, 0, 0], -1)


	
	

	####################################################
	# Mostrar el video con los cambios hechos #
	####################################################

	# The bitwise and of the frame and mask is done so  
	# that only the blue coloured objects are highlighted  
	# and stored in res 
	res = cv2.bitwise_and(blurred,blurred, mask= mask_total)
	cv2.imshow('frame',region_resized) 
	#cv2.imshow('mask',mask) 
	#cv2.imshow('res',res) 
	  
	# This displays the frame, mask  
	# and res which we created in 3 separate windows. 
	k = cv2.waitKey(5) & 0xFF
	if k == 27: 
		break
  
# Destroys all of the HighGUI windows. 
cv2.destroyAllWindows() 
  
# release the captured frame 
cap.release()



pts_blue = np.array(pts_blue)
pts_yellow = np.array(pts_yellow)
pts_red = np.array(pts_red)
pts_body = np.array(pts_body)

print(len(pts_times))
print(len(pts_blue))
print(len(pts_yellow))
print(pts_red)

if len(pts_blue) == 0:
	pts_blue = np.zeros((len(pts_times), 2))

if len(pts_yellow) == 0:
	pts_yellow = np.zeros((len(pts_times), 2))

if len(pts_red) == 0:
	pts_red = np.zeros((len(pts_times), 2))

if len(pts_body) == 0:
	pts_body = np.zeros((len(pts_times), 2))


print(np.shape(pts_times))
print(np.shape(pts_blue))
print(np.shape(pts_yellow))
print(np.shape(pts_red))
print(np.shape(pts_body))


f = open(outfile, "w")
for i in range(len(pts_times)):
	f.write("%f %f %f %f %f\n"%(pts_times[i], pts_red[i][0], pts_red[i][1], pts_body[i][0], pts_body[i][1]))

f.close()

