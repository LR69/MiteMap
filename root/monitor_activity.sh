#!/bin/bash

# d'après https://yavin4.ovh/index.php/2014/12/31/raspberry-pi-recuperer-la-temperature-cpu-dans-un-fichier/
# pour automatiser le processus toutes les minutes : 	crontab -e
#									* * * * * bash /root/monitor_activity.sh

# Récupération de la température ; on obtient ici une valeur à 5 chiffres sans virgules (ex: 44123) :
TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)

# Récupération de la charge du processeur : 1 indique qu'un proc est occupé à temps plein. >4 : des processus font la queue
LOAD=$(uptime | grep -e "average......" -o | grep -e "....$" -o)

# On divise alors la valeur obtenue par 1000, pour obtenir un résultat avec deux chiffres seulement (ex: 44) :
let "TEMP = $TEMP / 1000"

# Récupération de la date et l'heure du jour ; on obtient ici une valeur telle que "mercredi 31 décembre 2014, 00:15:01" :
DATE=`date +"%d/%m/%Y %H:%M:%S"`

# Fichier cible (où seront stockées les valeurs). On stocke valeurs  dans un sous-répertoire log (limitation de taille par logrotate):
FICHIER="/var/log/SurveillanceRPi.log"

# Si le fichier temperature.html n'existe pas, on le crée et on y injecte le code html minimum
if [ ! -f "$FICHIER" ];then
  touch "$FICHIER" &&
  echo "date_heure, température, charge CPU" > "$FICHIER"
fi

echo "$DATE, $TEMP, $LOAD" >> "$FICHIER"

exit
