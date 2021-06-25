import datetime
import time
import random
import cv2
import shutil
import os
import re
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
# Ce module comporte tous les outils nécessaires à la gestions des fichiers et de l'interface web
# version mietMapv3 du 3/05/20 : tempo avant archivage zip
# version miteMapv4 du 8/05/20 : ajout durée si immo dans maj_tableau
hostname = os.uname()[1]
nom_fichier_data = hostname + ".zip"
def reinit() :
	""" nettoyage du miteMap"""
	# effacement des données de l'acquisition précédente.
	shutil.rmtree("/var/www/html/images_bugcount")
	os.mkdir("/var/www/html/images_bugcount")
	os.mkdir("/var/www/html/images_bugcount/images_brutes")
	os.mkdir("/var/www/html/images_bugcount/images_traitees")
	os.mkdir("/var/www/html/images_bugcount/live")
	
	shutil.rmtree("/var/www/html/donnees")
	os.mkdir("/var/www/html/donnees")
	
	# initialisation des fichiers d'interface 
	with open("/var/www/html/corps_index.html", 'w') as mon_fichier:
		chaine=""
		mon_fichier.write(chaine)
	
	# RAZ page images
	with open('/var/www/html/pre_index_images.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index_images.html','r') as post:
		postscript=post.read()    
	contenu = preambule + " \n" + postscript
	with open("/var/www/html/index_images.html",'w') as index_html:
			index_html.write(contenu)
	# effacement du fichier interdisant le démarrage avant effacement volontaire et complet
	fichier_flag = "run_en_cours"
	if os.path.exists(fichier_flag):
		os.remove(fichier_flag)
	# effacement des fichiers zip des acquisitions précédentes
	dir_name = "/var/www/html/"
	liste = os.listdir(dir_name)
	for item in liste:
		if item.endswith(".zip"):
			os.remove(os.path.join(dir_name, item))
	
def maj_tableaux(lignes1, lignes2, t_immo, t, num_img, dt_frame_min, dt_frame_ms, dt_frame_max):
	# mise à jour de l'interface html
	# lecture des header et footer
	with open('/var/www/html/pre_index.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index.html','r') as post:
		postscript=post.read() 
	lignes3 = "<h1>Durée d'immobilité de l'acarien</h1>\n"
	lignes3 += " Durée d'immobilité de l'acarien : {}s / {}s".format(t_immo, t)
	lignes4 = "<h1>Fréquence d'acquistion</h1>\n"
	if float(t)>0.001:
		vitesse = num_img / float(t)
	else:
		vitesse = 0
	lignes4 += "<table>" 
	if dt_frame_max < 500 :
		lignes4 += " <tr> <td> Durée d'acquisition </td> <td> mini : {:.1f}  ms </td> <td> actuelle : {:.1f}  ms </td> <td> maxi : {:.1f}  ms  </td> </tr>".format(dt_frame_min, dt_frame_ms, dt_frame_max)
	else :
		lignes4 += " <tr> <td> Durée d'acquisition </td> <td> mini : {:.1f}  ms </td> <td> actuelle : {:.1f} ms </td> <td style=""color:Red;""> maxi : <b> {:.1f}  ms </b> </td> </tr>".format(dt_frame_min, dt_frame_ms, dt_frame_max)
	lignes4 += " <tr> <td colspan=""2"" style=""text-align:right""> Fréquence moyenne d'acquisition et de traitement : </td> <td colspan=""2"" style=""text-align:left""> {:.3f} images / s <td>".format(vitesse)
	lignes4 += "</table>" 
	chaine = preambule + lignes1 + lignes2 + lignes3 + lignes4 + postscript
	with open("/var/www/html/index.html",'w') as index_html:
			index_html.write(chaine)

def maj_tableau(titre, tps_ZT, tps_ZNT, tps_ZT_m, tps_ZNT_m, d_ZT, d_ZNT): 
		lignes = "<h1>{}</h1>\n".format(titre)
		lignes += """		<div class="table100 ver1 m-b-110">  
			<div class="table100-head">  
				<table>  
					<thead>  
						<tr class="row100 head">  
							<th class="cell100 column1"></th>  
							<th class="cell100 column2" >Zone Traitée</th>  
							<th class="cell100 column3" >Zone Non Traitée</th>  
						</tr>  
					</thead>  
				</table>  
			</div>  
			<div class="table100-body">  
				<table>  
					<tbody>  
						<tr class="row100 body">
							<td class="cell100 column1"> temps passé (s) </td> """
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column2"" > {} </td> \n".format(tps_ZT)
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column3"" > {} </td> \n".format(tps_ZNT)
		lignes += """						</tr>
						<tr class="row100 body">
							<td class="cell100 column1"> temps passé (s) si mobile</td> """
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column2"" > {} </td> \n".format(tps_ZT_m)
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column3"" > {} </td> \n".format(tps_ZNT_m)
		lignes += """						</tr>
						<tr class="row100 body">
							<td class="cell100 column1"> distance parcourue (mm) </td> """
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column2"" > {:.1f} </td> \n".format(d_ZT)
		lignes +="\t\t\t\t\t\t\t<td class=""cell100 column3"" > {:.1f} </td> \n".format(d_ZNT)
		lignes +="""						</tr>
					</tbody>
				</table>
			</div>
		</div>"""
		
		return lignes

def package_images(fourmi):
	""" génére une archive .zip contenant les prises de vues en mode Record"""
	if not hasattr(package_images, "lignes"):
		package_images.lignes=[]
		package_images.lignes.append("<tr> </tr> <tr> <td> <hr> </td> <td> <hr>  </td> <td> <hr> </td></tr> <tr>  </tr>\n")
	# archivage d'images
	maintenant = datetime.datetime.now()
	date2 = maintenant.strftime('%Y_%m_%d_')
	heure2 = maintenant.strftime('%Hh%Mm%Ss')
	nom_fichier_brutes = hostname + "_images_brutes_" + date2 + heure2 
	chemin_dest_brutes = "/var/www/html/images_bugcount/"+nom_fichier_brutes
	chemin_image_brutes ="/var/www/html/images_bugcount/images_brutes/"
	shutil.make_archive(chemin_dest_brutes, 'zip', chemin_image_brutes)
	nom_fichier_traitees = hostname + "_images_traitees" + date2 + heure2 
	chemin_dest_traitees = "/var/www/html/images_bugcount/"+nom_fichier_traitees
	chemin_image_traitees ="/var/www/html/images_bugcount/images_traitees/"
	shutil.make_archive(chemin_dest_traitees, 'zip', chemin_image_traitees)
	
	ref1 = "images_bugcount/" + nom_fichier_brutes + ".zip"
	ref2 = "images_bugcount/" + nom_fichier_traitees + ".zip"
	if fourmi: # affichage d'un message d'alerte en cas de présence d'une fourmi
		ligne = "<tr>" + "<td> <font color=#FF3333> ALERTE FOURMI : voir images ci-dessous </font> </td>" + "</tr>"
		package_images.lignes.append(ligne)
	ligne = "<tr>" + \
		"<td> <a href=" + ref1 + ">" + nom_fichier_brutes + ".zip" + "</a></td>" + \
		"<td> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </td>" + \
		"<td> <a href=" + ref2 + ">" + nom_fichier_traitees + ".zip" + "</a></td>" +\
		"</tr>"
	package_images.lignes.append(ligne)

	
	# intercalaire si 3 lignes
	if len(package_images.lignes) % 4 == 0 :
		package_images.lignes.append("<tr> </tr> <tr> <td> <hr> </td> <td> <hr>  </td> <td> <hr> </td></tr> <tr>  </tr>\n")
	
	# lecture des header et footer
	with open('/var/www/html/pre_index_images.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index_images.html','r') as post:
		postscript=post.read()    
	

	
	# mise à jour de l'interface html
	contenu = preambule + " \n".join(package_images.lignes) + postscript #ajtp


	with open("/var/www/html/index_images.html",'w') as index_html:
			index_html.write(contenu)
	# effacement des images ayant servi à construire l'archive
	shutil.rmtree("/var/www/html/images_bugcount/images_brutes")
	shutil.rmtree("/var/www/html/images_bugcount/images_traitees")
	os.mkdir("/var/www/html/images_bugcount/images_brutes")
	os.mkdir("/var/www/html/images_bugcount/images_traitees")

def package_data(resolution, tableau_brut, **tableaux_traites):
	""" Permet l'archivage des données en fin d'expérience"""
	maintenant = datetime.datetime.now()
	date2 = maintenant.strftime('%Y_%m_%d_')
	heure2 = maintenant.strftime('%Hh%Mm%Ss')
	dossier ="/var/www/html/donnees/"
	
	# création des .csv à partir des tableaux de données
	tab_float = tableau_brut.astype(float)
	tab_float[:,0] *= 0.1 # temps en secondes
	tab_float[:,1] /= resolution # abscisse en mm
	tab_float[:,2] /= resolution # ordonnée en mm
	nom_fichier = hostname + "_donnees_brutes_" + date2 + heure2 +".csv"
	chemin = dossier + nom_fichier 
	np.savetxt(chemin, tab_float, delimiter='\t', header="t(s) \t x(mm) \t y(mm) \t Immobile (si =1)", fmt='%.1f')
	for nom, tableau_traite in tableaux_traites.items():
		tab_ch = ['{:.1f}'.format(float(num)) for num in tableau_traite]
		tab_ch.insert(0,hostname)
		temps=date2+heure2
		tab_ch.insert(0,temps)
		tab_ch_vert = np.asarray([tab_ch])
		nom_fichier = hostname + "_" + nom + "_" + date2 + heure2 +".csv"
		chemin = dossier + nom_fichier 
		np.savetxt(chemin, tab_ch_vert, delimiter='\t', header="DateHeure \t MiteMap \t Tin(s) \t Tout(s) \t Tin_m(s) \t Tout_m(s) \t Din(mm) \t Dout(mm)", fmt='%s')
		
	# copie de la carte thermique
	nom_fichier = hostname + "_carte_thermique_" + date2 + heure2 + ".png"
	chemin = dossier + nom_fichier 
	shutil.copyfile("/var/www/html/images_bugcount/carte_thermique.png", chemin)
	time.sleep(1) # car pb signalé de carte thermique à 0 octet
	
	# archivage des données
	racine = "/var/www/html/"
	nom_fichier = racine + hostname + date2 + heure2
	shutil.make_archive(nom_fichier, 'zip', dossier)
	
	# mise à jour de l'interface
	lien = hostname + date2 + heure2 + ".zip"
	bouton = "<a href=\"{}\" class=\"button\">Télécharger les données</a>".format(lien)
	with open("/var/www/html/index.html",'r') as fichier:
		index_html = fichier.read()
		index2_html = re.sub('<!--futur bouton-->', bouton, index_html)
	with open("/var/www/html/index.html",'w') as fichier:
		fichier.write(index2_html)

def pas_data():
	""" si aucune donnée n'a été enregistrée """
	with open('/var/www/html/pre_index.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index.html','r') as post:
		postscript=post.read() 
	message = "<font color=#FF3333> PAS DE DONNEES ENREGISTREES ! </font> "
	postscript2 = re.sub('<!--futur bouton-->', message, postscript)
	index_html = preambule + postscript2
	with open("/var/www/html/index.html",'w') as fichier:
		fichier.write(index_html)

def maj_graphique(tab2d,nom_image):
	#print(tab2d.T) #pour debug
	tab2d+= np.uint16(np.ones((100,100))) # car échelle log; bas de l'échelle 10^0
	plt.imshow(tab2d.T, norm=colors.LogNorm(), cmap='magma') # il faut transposer car [ligne, col] != (x, y)
	plt.title("Positionnement de l'acarien dans l'arène")
	plt.colorbar()
	chemin_img = "/var/www/html/images_bugcount/"+nom_image
	plt.savefig(chemin_img)
	plt.close()
	

def maj_live(img, capt):
	# écriture image brute pour affichage
	chemin_image="/var/www/html/images_bugcount/live/image_brute.jpg"
	cv2.imwrite(chemin_image, capt)
	# écriture image traitée pour affichage
	chemin_image="/var/www/html/images_bugcount/live/image_traitee.jpg"
	cv2.imwrite(chemin_image, img)
	time.sleep(1)

def ds2s(tps_ds):
	""" pour faux affichage d'une décimale """
	S = str(tps_ds)
	return S[:len(S)-1] + "." + S[len(S)-1:] 
