<!DOCTYPE html>
<html lang="en">
<head>
	<title>MiteMap</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
<!--===============================================================================================-->	
	<link rel="icon" type="image/png" href="images/icons/mite.ico"/>
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/bootstrap/css/bootstrap.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="fonts/font-awesome-4.7.0/css/font-awesome.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/animate/animate.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/select2/select2.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/perfect-scrollbar/perfect-scrollbar.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="css/util.css">
	<link rel="stylesheet" type="text/css" href="css/main.css">
	<link rel="stylesheet" type="text/css" href="css/menus.css">
<!--===============================================================================================-->

</head>



<body>
	<div id="bloc_page">
		<!--#include file="header.html" -->


<h2>Configuration du miteMap</h2>

<?php
$duration = 20;
$mode = "normal";
$duree_video = "10";
$interval_video = "230";

$file = "miteMap.conf";
$content = file_get_contents($file);
$tableau = explode("\n",$content);

$duration = explode("=",$tableau[0])[1];
//echo "durée=" . $duration . PHP_EOL;
$mode = explode("=",$tableau[1])[1];
//echo "mode=" . $mode . PHP_EOL;

$duree_video = explode("=",$tableau[2])[1];
//echo "mode=" . $duree_video . PHP_EOL;
$interval_video = explode("=",$tableau[3])[1];
//echo "interval_video=" . $interval_video . PHP_EOL;

?>


<form action="/action_page.php" method="get">
  <label for="duration">Durée de l'expérience en minutes (durée maximal autorisée 105 min.):</label><br>
  <input type="text" id="duration" name="duration" value='<?php echo $duration; ?>'><br>
  <input type="radio" id="normal" name="mode" value="normal" <?php echo ($mode== 'normal') ?  "checked" : "" ;  ?> >
  <label for="normal">Normal</label><br>
  <input type="radio" id="video" name="mode" value="video"  <?php echo ($mode== 'video') ?  "checked" : "" ;  ?> >
  <label for="video">Video</label><br>
  <p>Si le mode vidéo est sélectionné, les deux paramètres suivants sont à prendre en compte :</p>
  <label for="duree_video">Durée d'une video en secondes:</label><br>
  <input type="text" id="duree_video" name="duree_video" value='<?php echo $duree_video; ?>'><br>
  <label for="interval_video">Intervalle entre 2 videos, en secondes:</label><br>
  <input type="text" id="interval_video" name="interval_video"  value='<?php echo $interval_video; ?>'><br>
  <input type="submit" value="Submit">
</form> 

<form action="/action_page.php" method="get">

</form> 


</body>
<footer height="200">
<p align="center"> L.Roy <a href="mailto:Lise.ROY@cefe.cnrs.fr">Lise.ROY@cefe.cnrs.fr </a> - CEFE - CNRS - 34090 Montpellier</p>
</html>

