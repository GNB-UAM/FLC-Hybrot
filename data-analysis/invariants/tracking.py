
# Python program for Detection of a  
# specific color(blue here) using OpenCV with Python 
import cv2 
import numpy as np

# For tracking the movement
from collections import deque
import imutils
import time

# Array que guarda las posiciones de cada objeto (deque es como un array mas eficiente)
pts_red = deque()
pts_blue= deque()
pts_yellow = deque()
pts_times = deque()


videofile = "cpgbot.mp4"
upper_left = (0, 600)
bottom_right = (1800, 1000)
outfile = "captura_patas.txt"

  
# Lee el video del fichero
cap = cv2.VideoCapture(videofile)  
  
# This drives the program into an infinite loop. 
while(1):
	#time.sleep(1)
	# Captures the live stream frame-by-frame 
	_, frame = cap.read()

	if frame is None:
		print("no frame")
		break

	frame_time = cap.get(cv2.CAP_PROP_POS_MSEC)
	pts_times.append(frame_time)

	region = frame[upper_left[1] : bottom_right[1], upper_left[0] : bottom_right[0]]

	# Hace la imagen mas pequeña para que sea mas manejable y le aplica blur para quitar "impurezas"
	region_resized = region# imutils.resize(region, width=600)
	blurred = cv2.GaussianBlur(region_resized, (11, 11), 0)

	# Converts images from BGR to HSV 
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

	###############################################
	# Crea las mascaras para detectar los colores #
	###############################################


	# 2021y12m1d/02830.MTS
	 
	# Range for upper range
	lower_red = np.array([130,0,210])
	upper_red = np.array([180,255,255])
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
 
	# update the points queue
	pts_red.append(center_red)

	# loop over the set of tracked points
	for i in range(1, len(pts_red)):
		# if either of the tracked points are None, ignore
		# them
		if pts_red[i - 1] is None or pts_red[i] is None:
			continue
 
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		#thickness = int(np.sqrt(1 / float(i + 1)) * 2.5)
		cv2.line(region_resized, pts_red[i - 1], pts_red[i], (0, 0, 255), 3)

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

print(len(pts_times))
print(len(pts_blue))
print(len(pts_yellow))
print(len(pts_red))

if len(pts_blue) == 0:
	pts_blue = np.zeros((len(pts_times), 2))

if len(pts_yellow) == 0:
	pts_yellow = np.zeros((len(pts_times), 2))

if len(pts_red) == 0:
	pts_red = np.zeros((len(pts_times), 2))


print(np.shape(pts_times))
print(np.shape(pts_blue))
print(np.shape(pts_yellow))
print(np.shape(pts_red))


f = open(outfile, "w")
for i in range(len(pts_times)):
	f.write("%f %f %f %f %f %f %f\n"%(pts_times[i], pts_blue[i][0], pts_blue[i][1], 
		pts_yellow[i][0], pts_yellow[i][1], pts_red[i][0], pts_red[i][1]))

f.close()

