from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import math
from random import randint
import cv2
import RPi.GPIO as GPIO
import time
import os
import shutil
import datetime
import sys
import copy
import multiprocessing as mp #MP

import bugcount_utils
import img_count_utils as imcount
import acarien 
import arene

# version du 2 juin 2020 : 	- ajout d'un mode de forçage du fonctionnement sans BP (debug9)
#							- bridage du fonctionnement à 8 acquisitions par seconde (en commentaire par défaut)
#							- ajout des valeurs min. et max. du cycle d'acquisition dans l'interface
mode = sys.argv[1] # "normal" ou "calib" ou "debugI"
# niveau de verbosité (debug1 : peu verbeux à debug8 très verbeux)
# debug = 9 : forçage du démarrage
# version miteMapv6 du 16/05/22 : correction de coordonnées du fichier de données brutes. Origine = centre de l'arène.
debug=0
if len(mode) == 6:
	if mode[:5] == "debug":
		debug = int(mode[-1])

fin = sys.argv[2] # durée programmée de l'acquisition en minutes
shutil.copyfile("/var/www/html/pre_index_images_ini.html", "/var/www/html/pre_index_images.html")
if (mode == "video"):
	duree_video = int(sys.argv[3]) # duree de l'acquisition vidéo (en secondes)
	intervalle_min_video = int(sys.argv[4]) # intervalle minimum entre deux acquisitions videos (en secondes)
	with open('/var/www/html/pre_index_images.html','a') as preamb:
		texte="<h1>Conditions expérimentales</h1>\n <ul>\n"
		texte+="<li>mode : {}</li>\n".format(mode)
		texte+="<li>durée de l'expérience (en min.) : {}</li>\n".format(fin)
		texte+="<li>duree de l'acquisition vidéo (en secondes) : {}</li>\n".format(duree_video)
		texte+="<li>intervalle minimum entre deux acquisitions videos (en secondes):{}</li>\n</ul>\n".format(intervalle_min_video)
		texte+="<h1>Images mémorisées </h1>\n"
		texte+="\t<div align=center>\n"
		texte+="\t\t<table>\n"
		preamb.write(texte)
else:
	seuil_video = 9999
	duree_video = 1
	intervalle_min_video = 99999
	with open('/var/www/html/pre_index_images.html','a') as preamb:
		texte="<h1>Conditions expérimentales</h1>\n <ul> \n"
		texte+="<li>mode : {}</li>\n".format(mode)
		texte+="<li>durée de l'expérience (en min.) : {}</li>\n</ul>\n".format(fin)
		texte+="<h1>Images mémorisées </h1>\n"
		texte+="\t<div align=center>\n"
		texte+="\t\t<table>\n"
		preamb.write(texte)


# initialisation des pins du rpi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# entrées
BPrecord = 16 # Bouton enregistrement : pin 36
GPIO.setup(BPrecord, GPIO.IN,pull_up_down=GPIO.PUD_UP) 
BPma = 20  # bouton marche arrêt : pin 38
GPIO.setup(BPma, GPIO.IN,pull_up_down=GPIO.PUD_UP)  
BPreset = 21 # bouton de reset : pin 40
GPIO.setup(BPreset, GPIO.IN,pull_up_down=GPIO.PUD_UP)  

# sorties
PWR_LED = 25 # pin 22 
GPIO.setup(PWR_LED, GPIO.OUT) # commande des leds de puissance (via transistor)
LED_V = 8 # pin 24
GPIO.setup(LED_V, GPIO.OUT) # commande de led verte fonctionnement normal et effacement
LED_J = 7 # pin 26
GPIO.setup(LED_J, GPIO.OUT) # commande de led jaune enregistrement


# initialisation de la caméra
camera = PiCamera()
camera.resolution = (704, 528) #(704, 528), (1024,768) ou (3200, 2404)
camera.framerate = 24
camera.brightness = 70
camera.contrast = 50
rawCapture = PiRGBArray(camera, size=(704, 528)) # à changer aussi !
GPIO.output(PWR_LED,True) # On allume les LEDS de puissance
time.sleep(2)
(w, h) = camera.resolution


# On détermine automatiquement le centre et le rayon de l'évidement circulaire dans la plaque de téflon
camera.capture(rawCapture, format="bgr")
capt = rawCapture.array
C = imcount.trouve_cercle(capt, (w,h))
GPIO.output(PWR_LED,False) # On éteint les LEDS de puissance
rawCapture.truncate(0) # on flush le buffer pour acquisitions suivantes

if C == None:
	C = ((int(w/2), int(h/2)), int(h/2.1)) # par défaut
	if (debug >= 1 or mode == "calib"):
		print("pas de détection automatique de l'arène")
elif ((debug >= 1) or (mode == "calib")):
	((x,y), radius) = C
	print("Détection automatique de l'arène : centre de l'arène : ({},{}); rayon de l'arène = {}".format(x, y, radius)) 
	
arena = arene.Arene(C)

resolution = C[1] / 20.0 # résolution en pixels par mm car le diamètre de l'arène est percé précisément à 40 mm

# dimension du cercle frontière (version commune)
if (debug >= 2):
	print("centre de l'arène : {}".format(arena.centre_arene))
	print("diamètre de l'arène: {}".format(arena.rayon_arene))

#initialisation mite tracker


IMGcount = 0 # compteur d'images 
BPcount = 0 # comptage d'appui sur BP
jobs=[] #MP
dt_frame_ms = 0 # temps d'acquisition et de traitement d'une image
dt_frame_min = 500 # valeur mini de dt_frame_ms observée
dt_frame_max = 0 # valeur maxi de dt_frame_ms observée
flag = 0 # drapeau seconde paire ou impaire
while(True): 
	maintenant = datetime.datetime.now()
	date = maintenant.strftime('%Y-%m-%d')
	heure = maintenant.strftime('%H:%M:%S')
	if (GPIO.input(BPreset) == 0)and (GPIO.input(BPma) == 1) or debug == 9: # on APPUIE sur le BP de reset
		BPcount += 1
		GPIO.output(LED_V,True)
		print("appui sur BPreset n=",BPcount)
		if ((BPcount > 20) and (BPcount<40)): # on est resté appuyé pendant 2s
			if debug == 9:
				debug = 10
			if (BPcount%2) == 0 :
				GPIO.output(LED_V,True) 
			else:
				GPIO.output(LED_V,False)
		if (BPcount >= 40): # on est resté appuyé trop longtemps
			GPIO.output(LED_V,False)
	if (GPIO.input(BPreset) == 1) and (GPIO.input(BPma) == 1) and debug != 9 and debug != 11: # on N'APPUIE PAS sur le BP de reset
		if ((BPcount > 20) and (BPcount<40)): # on a relâché pendant le clignotement
			if debug == 10:
				debug = 11
			# initialisation des fichiers : A RENDRE CONDITIONNEL PAR APPUI GPIO
			print("{} {} : EFFACEMENT DONNEES".format(date,heure))
			GPIO.output(LED_V,True)
			bugcount_utils.reinit()
			IMGcount = 0
			time.sleep(1)
		BPcount =0 
		# Extinction LEDs
		GPIO.output(LED_V,False)
		GPIO.output(PWR_LED,False) 

	# gestion du redémarrage après coupure de courant
	if os.path.exists("run_en_cours"):
		run_en_cours = True
	else:
		run_en_cours = False
			
	
	if (((GPIO.input(BPma) == 0) and (GPIO.input(BPreset) == 1) or debug == 11 ) and not run_en_cours): # on APPUIE sur le BP de marche et pas sur Reset, et effacement préalablement effectué
		print("appui sur BPmarche n=",BPcount)
		BPcount += 1
		if (BPcount>10): #on lance le démarrage du programme
			with open("run_en_cours",'w') as mon_fichier:
				mon_fichier.write("démarré le {} à {}".format(date, heure))
			print("{} {} : On lance le programme principal de vision".format(date,heure))
			GPIO.output(PWR_LED,True) # On allume les LEDS de puissance
			temps_init = datetime.datetime.now() # origine des temps
			REC = False
			debut_video = temps_init
			stop_video = temps_init
			while (GPIO.input(BPma) == 0) :
				time.sleep(0.1)# on attend le relâchement du bouton
			num_img = 0
			aca = acarien.Acarien((w, h))
			for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
				# horodatage des données
				maintenant = datetime.datetime.now()
				date = maintenant.strftime('%Y-%m-%d')
				heure = maintenant.strftime('%H:%M:%S')
				if num_img<=20:
					temps_init = maintenant
				delta_t = maintenant - temps_init
				temps_ds = int(10*round(delta_t.seconds + (delta_t.microseconds/1e6),1)) #intervalle de temps en dizième de s
				# suivi des temps d'acquisition
				if dt_frame_ms < dt_frame_min and dt_frame_ms > 0:
					dt_frame_min = dt_frame_ms
				if dt_frame_ms > dt_frame_max:
					dt_frame_max = dt_frame_ms
				GPIO.output(LED_V,True)
				#acquisition image
				capt = frame.array
				img=capt.copy()
				GPIO.output(LED_V,False) # on a pris une image
				# creation du masque
				# mask = np.zeros((h,w),np.uint8)
				# cv2.circle(mask,center,int(rayon),(255,255,255),trackW)
				mask = None #pas de masque dans miteMap dans un premier temps
				
				# traitement 
				cercles, fourmi = imcount.bugcount(img, mask, aca.AREA_MIN_ACA, aca.AREA_MAX_ACA, mode)
				if (debug >= 2):
					print("num_img = {} ; cercles trouvés : \n {}".format(num_img, cercles)) #pour debug
				if num_img < 20 :
					#on ne prend pas en compte les 20 premières acquisitions
					cercles=[]
				
				if (num_img==20):
					if len(cercles)==1:
						aca.register_position_init(temps_ds, cercles[0]) # il faut une position antérieure pour calculer la vitesse
					else:
						num_img -= 1 #il faut commencer réellement quand on visualise pour la première fois l'acarien sinon aca.derpos vaut []
				
				# si on  2 détections ou plus on passe à la capture suivante. 
				if ((len(cercles)<2) and (num_img>=20)):
					if (debug >= 2):
						print("num_img = {} ; dernières positions: \n {}".format(num_img, aca.derpos)) #pour debug
					# si on ne détecte rien, on garde l'acquisition précédente
					if len(cercles)==0:
						aca.pasbouger(temps_ds)
					else:
						aca.register_position(temps_ds, cercles[0])
						
						
					#on dessine l'acarien
					if (debug >= 2):
						print("position de l'acarien à dessiner : {} ; rayon :{} couleur : {}".format(aca.position, aca.rayon, aca.couleur))
					cv2.circle(img, aca.position, aca.rayon, aca.couleur, -1)
					# on trace la trajectoire récente 
					aca.tracer_trajectoire(img)
					
					
					#tracé de l'arène
					arena.tracer(img)
					
					# affichage du temps passé dans la zone traitée C
					arena.zone_C.update(aca.position, temps_ds, aca.pas, aca.immo)
					# affichage du temps passé dans la zone traitée D
					arena.zone_D.update(aca.position, temps_ds, aca.pas, aca.immo)
					
					if (debug >= 1):
						print("delta_t = {} ; position = {} ; immobile = {}".format(delta_t, aca.position, aca.immo))
						print("delta_t = {} ; temps passé en zone C = {} ds; temps passé en zone D = {} ds".format(bugcount_utils.ds2s(temps_ds), bugcount_utils.ds2s(arena.zone_C.duree_acarien_IN), bugcount_utils.ds2s(arena.zone_D.duree_acarien_IN)))
					
					# écriture dans tableaux data et sizes
					arena.tab2D.update(aca.position)
					
					if (debug >= 2):
						print("tableau d'occupation de l'arène par l'acarien :\n {}".format(arena.tab2D.occupation))
						
					
					# distances parcourues
					dist_parcourue_zC_mm = arena.zone_C.distance_parcourue/resolution # distance parcourue en zone C en mm
					dist_parcourue_zD_mm = arena.zone_D.distance_parcourue/resolution # distance parcourue en zone D en mm
					distance_parcourue_mm = aca.distance_parcourue/resolution # distance parcourue par l'acarien en mm
					
					
					if num_img == 20:# On fait une première acquisition
						
						tab1 = bugcount_utils.maj_tableau("Zone traitée type C","0.0" ,"0.0" , "0.0" ,"0.0", dist_parcourue_zC_mm, distance_parcourue_mm - dist_parcourue_zC_mm)
						tab2 = bugcount_utils.maj_tableau("Zone traitée type D", "0.0", "0.0", "0.0", "0.0", dist_parcourue_zD_mm, distance_parcourue_mm - dist_parcourue_zD_mm)
						
						# mise à jour du tableau de l'interface web
						p1 = mp.Process(target=bugcount_utils.maj_tableaux, args=(tab1, tab2, bugcount_utils.ds2s(aca.duree_immo), bugcount_utils.ds2s(temps_ds), num_img, 0, 0, 0))  #MP
						p1.start()  #MP
						
						# mise à jour de la carte thermique 
						p2 = mp.Process(target=bugcount_utils.maj_graphique, args=(arena.tab2D.occupation, "carte_thermique.png", ))  #MP
						p2.start()  #MP
						
						# mise à jour de l'onglet live
						p3 = mp.Process(target=bugcount_utils.maj_live, args=(img, capt, ))  #MP
						p3.start()  #MP
					
					# comptage du nombre de process actifs
					jobs_temp = jobs.copy() #MP
					if debug >= 2 :
						print("NB process = {} ".format(len(jobs)))
					for job in jobs_temp: #MP
						if not job.is_alive(): #MP
							jobs.remove(job) #MP
					
					if (maintenant.second % 2 == 0) and (flag == 0) and (len(jobs) <= 2) : # secondes paires : mise à jour tableaux
						flag = 1
						#tps_ZT, tps_ZNT, d_ZT, d_ZNT
						tps_ZT_C = bugcount_utils.ds2s(arena.zone_C.duree_acarien_IN)
						tps_ZNT_C = bugcount_utils.ds2s(temps_ds - arena.zone_C.duree_acarien_IN)
						tps_ZT_C_m = bugcount_utils.ds2s(arena.zone_C.duree_acarien_IN_m)
						tps_ZNT_C_m = bugcount_utils.ds2s(temps_ds - aca.duree_immo - arena.zone_C.duree_acarien_IN_m)
						if (debug >= 1):
							print("Zone C : tps_ZT={}, tps_ZNT={}, d_ZT={}, d_ZNT={}".format(tps_ZT_C, tps_ZNT_C, dist_parcourue_zC_mm, distance_parcourue_mm - dist_parcourue_zC_mm))
							print("Zone C : tps_ZT_m={}, tps_ZNT_m={}, d_ZT={}, d_ZNT={}".format(tps_ZT_C_m, tps_ZNT_C_m, dist_parcourue_zC_mm, distance_parcourue_mm - dist_parcourue_zC_mm))
						tab1 = bugcount_utils.maj_tableau("Zone traitée type C",tps_ZT_C ,tps_ZNT_C , tps_ZT_C_m ,tps_ZNT_C_m ,dist_parcourue_zC_mm, distance_parcourue_mm - dist_parcourue_zC_mm)
						
						tps_ZT_D = bugcount_utils.ds2s(arena.zone_D.duree_acarien_IN)
						tps_ZNT_D = bugcount_utils.ds2s(temps_ds - arena.zone_D.duree_acarien_IN)
						tps_ZT_D_m = bugcount_utils.ds2s(arena.zone_D.duree_acarien_IN_m)
						tps_ZNT_D_m = bugcount_utils.ds2s(temps_ds - aca.duree_immo - arena.zone_D.duree_acarien_IN_m)
						if (debug >= 1):
							print("Zone D : tps_ZT={}, tps_ZNT={}, d_ZT={}, d_ZNT={}".format(tps_ZT_D, tps_ZNT_D, dist_parcourue_zD_mm, distance_parcourue_mm - dist_parcourue_zD_mm))
							print("Zone D : tps_ZT_m={}, tps_ZNT_m={}, d_ZT={}, d_ZNT={}".format(tps_ZT_D_m, tps_ZNT_D_m, dist_parcourue_zD_mm, distance_parcourue_mm - dist_parcourue_zD_mm))
						tab2 = bugcount_utils.maj_tableau("Zone traitée type D", tps_ZT_D, tps_ZNT_D, tps_ZT_D_m, tps_ZNT_D_m, dist_parcourue_zD_mm, distance_parcourue_mm - dist_parcourue_zD_mm)
						
						t_immo = bugcount_utils.ds2s(aca.duree_immo)
						t = bugcount_utils.ds2s(temps_ds)
						if (debug >= 1):
							print(" Durée d'immobilité de l'acarien : {}s / {}s".format(t_immo, t))
						# mise à jour du tableau de l'interface web
						p1 = mp.Process(target=bugcount_utils.maj_tableaux, args=(tab1, tab2, t_immo, t, num_img, dt_frame_min, dt_frame_ms, dt_frame_max))  #MP
						p1.start()  #MP
						jobs.append(p1) #MP
					if (maintenant.second % 2 == 1) and (flag == 1) and (len(jobs) <= 2) : # secondes impaires : mise à jour graphique
						flag = 0
						# mise à jour de la carte thermique 
						p2 = mp.Process(target=bugcount_utils.maj_graphique, args=(arena.tab2D.occupation, "carte_thermique.png", ))  #MP
						p2.start()  #MP
						jobs.append(p2) #MP
					
					# mise à jour de l'onglet live
					if (len(jobs) <= 2) :
						p3 = mp.Process(target=bugcount_utils.maj_live, args=(img, capt, ))  #MP
						p3.start()  #MP
						jobs.append(p3)
					
					
					# écritures des images dans le serveur 
					delta_tv = maintenant - stop_video
					if (((fourmi or delta_tv.total_seconds()>intervalle_min_video) and mode == "video" and not REC) or (GPIO.input(BPrecord) == 0)): 
						# seuil vidéo ou fourmi détectée ou APPUI sur le BP d'enregistrement
						if (debug >= 1) and not REC:
							print("########################## LANCEMENT ACQUISITION VIDEO #########################") #AJTP
						debut_video = maintenant
						REC = True
						fourmi_mem = fourmi
					if  (REC and (IMGcount < 1000)):
						# On enregistre deux images sur le serveur
						# écriture image brute dans le serveur
						GPIO.output(LED_J,True)
						date2 = maintenant.strftime('%Y_%m_%d_')
						heure2 = maintenant.strftime('%Hh%Mm%Ss.%f')
						nom_image_brute = "image_brute_" + date2 + heure2 
						chemin_image="/var/www/html/images_bugcount/images_brutes/"+nom_image_brute + ".jpg"
						cv2.imwrite(chemin_image, capt)
						GPIO.output(LED_J,False)
						#écriture image traitée dans le serveur
						nom_image_traitee = "image_traitee_" + date2 + heure2
						chemin_image="/var/www/html/images_bugcount/images_traitees/"+nom_image_traitee  + ".jpg"
						cv2.imwrite(chemin_image,img)
						IMGcount += 1
					delta_tv2 = maintenant - debut_video 
					if ((((GPIO.input(BPrecord) == 1) and mode != "video") or ((delta_tv2.total_seconds() > duree_video) and mode == "video")) and (IMGcount > 0)): # on a appuyé sur le BP d'enregistrement, mais maintenant il est relâché
						REC = False
						bugcount_utils.package_images(fourmi_mem)
						fourmi_mem = 0
						IMGcount = 0
						stop_video = maintenant
						if (debug >= 1):
							print("########################## ARRET ACQUISITION VIDEO #########################") #AJTP
				# clear the stream in preparation for the next frame
				rawCapture.truncate(0)
				if (GPIO.input(BPma) == 0) or (delta_t.seconds > int(fin)*60): #on appuie sur le bouton marche ou le temps d'expérimentation est terminé
					BPcount = 0
					print("appui sur BPmarche pour sortie de boucle n=",BPcount)
					
					with open("run_en_cours",'a') as mon_fichier:
						mon_fichier.write("programme arrété le {} à {}".format(date,heure))
					break # on sort de l'acquisition continue
				else:
					num_img += 1 # image suivante
					dt_frame = datetime.datetime.now() - maintenant	 
					dt_frame_ms = round(dt_frame.seconds*1000 + (dt_frame.microseconds/1e3),1) #intervalle de temps en millième de s
					temps_cycle = 125 # bridage à 8 acquisitions par seconde
					if (dt_frame_ms <  temps_cycle ): # bridage à 8 acquisitions par seconde
						tempo = (temps_cycle - dt_frame_ms )/1e3 # bridage à 8 acquisitions par seconde
						time.sleep(tempo) # bridage à 8 acquisitions par seconde
						dt_frame = datetime.datetime.now() - maintenant	 # bridage à 8 acquisitions par seconde
						dt_frame_ms = round(dt_frame.seconds*1000 + (dt_frame.microseconds/1e3),1) # bridage à 8 acquisitions par seconde
					if debug >= 2 :
						print("Durée d'acquisition : min :{} ms ; actu : {} ms ;  max :{} ms".format(dt_frame_min, dt_frame_ms, dt_frame_max))

			print("{} {} : Sortie de la boucle principale de vision".format(date,heure))
			while (GPIO.input(BPma) == 0):
				print("on attend le relâchement du bouton marche")
				time.sleep(0.1)# on attend le relâchement du bouton
			print("Bouton marche relâché")
			# attente de finalisation des processus
			p1.join()
			p2.join()
			p3.join()
			GPIO.output(PWR_LED,False) # On éteint les leds de puissance
			#archivage des données
			if 'tps_ZT_C' in locals(): # des données ont été analysées
				tabC = [tps_ZT_C, tps_ZNT_C, tps_ZT_C_m, tps_ZNT_C_m, dist_parcourue_zC_mm, distance_parcourue_mm - dist_parcourue_zC_mm]
				tabD = [tps_ZT_D, tps_ZNT_D, tps_ZT_D_m, tps_ZNT_D_m, dist_parcourue_zD_mm, distance_parcourue_mm - dist_parcourue_zD_mm]
				bugcount_utils.package_data(arena.centre_arene, resolution, aca.tableau_pos, Donnees_traitees_formeC=tabC, Donnees_traitees_formeD=tabD )
				print("données archivées")
			else: # pas de données
				bugcount_utils.pas_data()
	time.sleep(0.1) #indispensable pour le respect des temps des boutons
GPIO.cleanup() # indispensable ?? try / Finally ?
