import numpy as np
import cv2
#from skimage.feature import peak_local_max
#from skimage.morphology import watershed
#from scipy import ndimage
import time
import math

# Ce fichier comporte tous les outils nécessaires à l'analyse d'images
# version miteThruv9b du 19/01/20
# version du 24/01/20 : ajout détection fourmi
# version du 23/04/20 : compatibilité miteMap

substractor = cv2.createBackgroundSubtractorMOG2(history = 100, varThreshold=25, detectShadows=True)


def trouve_cercle(img, dim_img):
	""" fonction permettant de trouver le centre et le rayon du cercle dans la plaque de téflon"""
	cercle = None
	(w, h) = dim_img
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	blur = cv2.GaussianBlur(gray,(81,81),cv2.BORDER_DEFAULT) 
	ret, thresh = cv2.threshold(gray,10,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
	
	trouve = False
	if len(cnts) > 0:
		#c = max(cnts, key=cv2.contourArea)
		for c in cnts:
			((x, y), radius) = cv2.minEnclosingCircle(c)
			#if radius > 10: # pour debug
				#print("centre : ({},{}); rayon = {}".format(x, y, radius)) # pour debug
			if radius > h/3 and radius < h/2:
				#trouve = True
				cercle = ((int(x), int(y)), int(radius))
				break
			
		# only proceed if the radius meets a minimum size
		#if trouve:
			#cv2.circle(img, (int(x), int(y)), int(radius),(0, 255, 0), 2) # pour debug 
			#nom_image="image_cercle.jpg" # pour debug
			#cv2.imwrite(nom_image, img) # pour debug
	return cercle

def bugcount(img,masque, aire_min, aire_max, mode = "hide"):
	fourmi = False
	if mode == "show":
		cv2.imshow('image brute',img) # ajtp
		if masque:
			cv2.imshow('masque',masque) # ajtp
		#key = cv2.waitKey(0)
	# filtrage
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	# effacement de l'arrière plan 
	bkgd_sup = substractor.apply(gray)
	if mode == "show":
		cv2.imshow('suppression arrière plan',bkgd_sup) # ajtp
		#key = cv2.waitKey(0)
	if masque:
		# masquage "doonut"
		masque2 = cv2.bitwise_and(bkgd_sup , masque , mask=None)
	else:
		masque2 =  bkgd_sup
	if mode == "show":
		cv2.imshow('masque',masque2) # ajtp
		#key = cv2.waitKey(0)
		
	# détermination des contours
	_, contours, _ = cv2.findContours(masque2.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	cercles=[]
	for c in contours:
		M = cv2.moments(c)
		aire = (M['m00'])
		if ((aire > aire_min) and (aire <= aire_max )): 
			centre = ((M['m10']/M['m00']), (M['m01']/M['m00']))
			rayon = math.sqrt(aire/math.pi)
			cercle = (centre, rayon)
			cercles.append(cercle)
		if (aire > aire_max):
			fourmi =  True
	if mode == "debug":
		print("[INFO] {} unique segments found".format(len(cercles))) 

	return (cercles, fourmi)

