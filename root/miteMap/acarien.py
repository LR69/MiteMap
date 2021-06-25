import numpy as np
import cv2
from collections import deque
from math import sqrt

class Acarien():
	""" classe stockant toutes les informations propres à l'acarien présent dans l'arène. """
	def __init__(self, dim_img):
		self.couleur = (255,0,0) # Pour affichage à l'écran
		self.position = (0,0)
		self.rayon = 1
		# tableau qui permet de stocker la position des acariens sous forme d'entiers de 16 bits
		# chaque ligne est un échantillon : temps en dizièmes de secondes, abscisse x, ordonnée y, flags
		# flag = 0 : mobile ; flag = 1 immobile
		self.tableau_pos = np.uint16(np.zeros((2, 4))) 
		self.derpos = deque([],20) # pour le tracé des dernières positions 
		(w, h) = dim_img
		aire_image = w * h
		aire_image_base = 704 * 528
		rapport = aire_image / aire_image_base
		self.AREA_MAX_ACA = 1500 *rapport  # du 24 janvier au 4 mars : 800
		self.AREA_ADULT_NYMPH = 200 * rapport # du 24 janvier au 4 mars : 90
		self.AREA_NYMPH_ASTIGM = 70 * rapport # du 24 janvier au 4 mars : 25
		self.AREA_MIN_ACA = 10 * rapport  # du 24 janvier au 4 mars : 10
		self.distance_parcourue = 0
		self.pas = 0 # en pixels
		self.vitesse = 0 # en pixels par seconde
		self.vitesse_mini = 0 # valeur à partir de laquelle on considère que l'acarien est en mouvement
		self.immo = 0 # = 0 : acarien immobile ; =1 acarien en mouvement
		self.seuil_immo = 16 # 8 pixels = environ 1mm en résolution de base
		self.duree_immo = 0 # duree d'immobilité de l'acarien en ds
		self.derstat = (0,0) # dernière station immobile de l'acarien

	def calculer_vitesse(self, dt,x,y,x1,y1):
		#calcule le pas et la vitesse de l'acarien
		self.pas = sqrt((x-x1)**2 + (y-y1)**2) # avance de l'acarien en pixels
		if dt>0:
			self.vitesse = self.pas/dt 
		else:
			self.vitesse = 0
		self.distance_parcourue += self.pas
		
	def register_position(self, t, cercle):
		#met à jour la position de l'acarien
		(x,y)=cercle[0]
		self.rayon = int(cercle[1])
		self.position=(int(x),int(y))
		ligne = self.derpos[-1]
		t1=ligne[0,0]
		x1=ligne[0,1]
		y1=ligne[0,2]
		dt=t-t1
		self.calculer_vitesse(dt,x,y,x1,y1) 
		# acarien immobile ou pas ?
		eloignement = sqrt((x-self.derstat[0])**2 + (y-self.derstat[1])**2) # éloignement de l'acarien en pixels
		if eloignement > self.immo:
			self.immo = 0
			f = 0
		else:
			self.immo = 1
			f = 1
			self.duree_immo += dt
		ligne=np.uint16([[ t, x, y, f]])
		self.tableau_pos=np.append(self.tableau_pos,ligne, axis=0)
		self.derpos.append(ligne)

	def register_position_init(self, t, cercle):
		#met à jour la position de l'acarien
		(x,y)=cercle[0]
		self.rayon = cercle[1]
		self.position=(x,y)
		ligne=np.uint16([[ t, x, y, 0]])
		self.tableau_pos=np.append(self.tableau_pos,ligne, axis=0)
		self.derpos.append(ligne)

	def pasbouger(self, t):
		ligne=self.derpos[-1]
		t1=ligne[0,0]
		dt = t - t1
		self.duree_immo += dt
		self.pas = 0
		self.vitesse = 0
		self.immo = 1
		
		ligne[0,0] = t # maj temps
		ligne[0,3]=1 # acarien immobile
		self.tableau_pos=np.append(self.tableau_pos,ligne, axis=0)
		self.derpos.append(ligne)



	def tracer_trajectoire(self, img):
		for i in range(0, len(self.derpos)-1):
			#print("i = {} ; dernière position : {}".format(i, self.derpos)) # ajtp
			pos0 = (self.derpos[i][0][1], self.derpos[i][0][2])
			pos1 = (self.derpos[i+1][0][1], self.derpos[i+1][0][2])
			epaisseur = int(self.rayon*sqrt(i+1)/sqrt(len(self.derpos)))
			cv2.line(img, pos0, pos1, self.couleur, epaisseur)
				
