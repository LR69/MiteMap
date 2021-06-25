import cv2
from math import sqrt
import numpy as np
# 8-05 miteMapv4 : ajout des durée ds zone si mobilité
class Arene():
	""" classe définissant l'arène dans laquelle évolue l'acarien. """
	def __init__(self, cercle):
		((xC, yC), rC) = cercle
		self.centre_arene = (xC, yC) # centre de l'arène
		self.rayon_arene = rC # rayon de l'arène
		self.zone_C = FormeC(self.centre_arene, self.rayon_arene) 
		self.zone_D = FormeD(self.centre_arene, self.rayon_arene) 
		self.zone_I = ZoneImpregnation(self.centre_arene, self.rayon_arene)
		self.tab2D = Tab2D(self.centre_arene, self.rayon_arene)
		self.couleur = (0,0,0)
		
	def tracer(self, img):
		cv2.circle(img,self.centre_arene,self.rayon_arene,self.couleur,1)
		self.zone_C.tracer(img)
		self.zone_D.tracer(img)
		self.zone_I.tracer(img)

class Forme():
	""" zone de traitement """
	def __init__(self, centre_arene, rayon_arene):
		self.acarien_IN = False # l'acarien est dedans
		self.instant_acarien_IN = 0 # temps en dizièmes de secondes où l'acarien a pénétré dans la zone.
		self.duree_acarien_IN = 0 # durée total d'occupation de la zone en dizièmes de secondes
		self.duree_acarien_IN_m = 0 # durée total d'occupation de la zone en dizièmes de secondes pendant laquelle l'acarien est mobile
		self.couleur = (0,255,0)

		
class FormeC(Forme):
	""" zone de traitement de type C (forme de lentille). """
	def __init__(self, centre_arene, rayon_arene):
		Forme.__init__(self, centre_arene, rayon_arene)
		self.centre = (centre_arene[0] - rayon_arene, centre_arene[1] )
		self.rayon = int(26.0714 * rayon_arene / 22.5) # voir fichier aires.xls
		self.distance_parcourue = 0 # distance parcourue
		
	def tracer(self, img):
		cv2.circle(img,self.centre,self.rayon,self.couleur,1)
	
	def update(self, coords, t, pas, immo):
		(x,y) = coords
		r = sqrt((x-self.centre[0])**2 + (y-self.centre[1])**2)
		if r < self.rayon: 
			if self.acarien_IN:
				self.distance_parcourue += pas #distance parcourue par l'acarien dans la zone.
				self.duree_acarien_IN += t - self.instant_acarien_IN #temps total de l'acarien dans la zone
				if not immo:
					self.duree_acarien_IN_m += t - self.instant_acarien_IN #temps total de l'acarien dans la zone pendant lequel il est mobile
			else:
				self.acarien_IN = True
			self.instant_acarien_IN = t
		else:
			self.acarien_IN = False

class FormeD(Forme):
	""" zone de traitement de type D (forme de demi-cercle). """
	def __init__(self, centre_arene, rayon_arene):
		Forme.__init__(self, centre_arene, rayon_arene)
		self.point0 = (centre_arene[0], centre_arene[1] - rayon_arene)
		self.point1 = (centre_arene[0], centre_arene[1] + rayon_arene)
		self.distance_parcourue = 0 # distance parcourue
		
	def tracer(self, img):
		cv2.line(img, self.point0, self.point1, self.couleur, 1)
	
	def update(self, coords, t, pas, immo):
		(x,y) = coords
		if x < self.point0[0]: 
			if self.acarien_IN:
				self.distance_parcourue += pas #distance parcourue par l'acarien dans la zone.
				self.duree_acarien_IN += t - self.instant_acarien_IN #temps total de l'acarien dans la zone
				if not immo:
					self.duree_acarien_IN_m += t - self.instant_acarien_IN #temps total de l'acarien dans la zone pendant lequel il est mobile
			else:
				self.acarien_IN = True
			self.instant_acarien_IN = t
		else:
			self.acarien_IN = False
			

class ZoneImpregnation():
	""" Zone d'imprégnation du produit"""
	def __init__(self, centre_arene, rayon_arene):
		self.couleur = (0,0,255)
		self.rayon = 50 # 4mm * 12.2px/mm environ
		self.centre = (centre_arene[0] - rayon_arene + self.rayon, centre_arene[1])
		
	def tracer(self, img):
		cv2.circle(img,self.centre,self.rayon,self.couleur,1) 

class Tab2D():
	""" Tableau de l'occupation spatiale de l'arène par l'acarien"""
	def __init__(self, centre_arene, rayon_arene):
		self.marge = 5 # pour être sûr de prendre les bords
		self.O = (centre_arene[0] - rayon_arene - self.marge,  centre_arene[1] - rayon_arene - self.marge) # coin supérieur gauche du carré contenant l'arène
		self.cote = 2*(rayon_arene + self.marge) # dimension du côté du carré contenant l'arène
		self.occupation = np.uint16(np.zeros((100,100))) # on travaille en pourcent
		
	def update(self, coords):
		(x,y) = coords
		(xx, yy) = (x - self.O[0] , y - self.O[1])
		(xxx , yyy) = (int(xx*100/self.cote), int(yy*100/self.cote)) 
		#print("(x,y) = ({},{}) ; O = {} ; (xx,yy) = ({},{}) ; cote = {} ; (xxx , yyy) = ({},{})".format(x, y , self.O, xx, yy , self.cote, xxx, yyy)) # pour debug
		if xxx < 100 and yyy < 100 :
			self.occupation[xxx,yyy]+=1
		
