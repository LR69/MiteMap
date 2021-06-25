# MiteMap
MiteMap is a raspberry based system used to track a mite inside an arena. The arena is a 2D disk where the mite is trapped. A repulsive or attractive volatile compound is put at the border of the arena.



![Arena](https://github.com/LR69/MiteMap/blob/master/schematics/arena_smple.png?raw=true)



Video capture of a mite tracking inside the area :

![Animated View of Arena](https://raw.githubusercontent.com/LR69/MiteMap/master/MT01_images_traitees2020_05_09_20h16m57s.gif)  



This MiteMap system uses :

- a raspberry pi 3 model B programmed using [python3](https://docs.python.org/3/) language,
- a native pi camera V2 Night Vision NoIR with a resolution of 8 mega-pixel,
- infrared Leds used to illuminate the mite,
- an electronic board with some push buttons, colored led and power devices to control the system,
- a support for the recording equipment 
- two glass plates (10cmx15cm)
- a PTFE plate (10cmx15cm, 1.5mm thick), with a hole in its center (4cm diameter circle)
- a PTFE plate (10 cm x 15 cm, 5 mm thick), with a hole in the center (circle with a diameter of 4 cm)
- two sheets of absorbent bench/filter paper (10 cm x 15 cm)
  - one blank
  - one locally impregnated, at a well-identified lateral point, with the compound to be tested
    one petri dish containing an infrared LED strip (940 nm).

![Exploded View](https://raw.githubusercontent.com/LR69/MiteMap/master/schematics/exploded_view.png)



# Commissioning

Here is a brief summary. For more detailed explanations see the [operating instructions manual](https://github.com/LR69/MiteMap/blob/master/13_mai_2020_miteMapV4_Mise_en_service.pdf) (in French)

## Connecting the miteMap

The MiteMap uses a board equipped with LEDs and Push Buttons to start, stop and reset acquisitions locally. The board also power the IR LEDs illuminating the mites. All the schematics and Typon of the board can be found in the "[electronic board](https://github.com/LR69/MiteThru/tree/master/electronic%20board)" folder of this repository.

Connect the +5V power supply wires of the raspberry motherboard (brown and white wire), the +12V power supply of the circuit (wires coming from the AC/DC adapter), and the 2 wires of the infrared LEDs to the terminal block of the electronic board, as shown below. Make sure that the AC/DC adapter is not connected to the 230VAC wall socket during the connection operations.

![Wiring the MiteMap](https://raw.githubusercontent.com/LR69/MiteMap/master/images/MT01_images_traitees2020_05_09_20h16m57s.gif)



## Operating the MiteMap

3 push buttons are present on the [electronic board](https://github.com/LR69/MiteThru/tree/master/electronic%20board) :

![MT_Buttons](https://raw.githubusercontent.com/LR69/MiteThru/13ed3ae31b86cde93fee49e4570fd6415c4f30e0/images/MT_Buttons.svg)

## Start Acquisition 
Press the **<a name="start_BP">Start/Stop button</a>** for at least 3 seconds 
	→ The green LED flashes rapidly (several times per second), which means that the acquisition program is running.

<u>Note</u>: if the power supply is interrupted or if the power supply is disconnected while the program was running, it will restart automatically when the power is restored.

## Record Images

Press and hold the **<a name="record_BP"> Record button</a>**	
									→ Image recording starts
									→ Yellow LED lights up

Release of the **<a name="record_BP2"> Record button</a>**					
									→ Yellow LED goes out
									→ Image recording stops

## Stop Acquisition 

Press briefly the **<a name="start_BP2">Start/Stop button</a>** 
	→ The green LED goes out, which means that the acquisition program has stopped.

<u>Note</u>: After the program has been stopped, it can be restarted using the Start/Stop button, without losing the previous data. The new data are then added after the others.

## Reset Acquisition 

The MiteMap must be turned off (green LED off) in order to begin the erasure procedure.

Press and hold the **<a name="reset_BP">Reset button</a>** 
	→ The green LED lights up blinks quickly.
	After about 5 seconds, the green LED lights up steadly 
	Release the **<a name="reset_BP">Reset button</a>** within 2 seconds
		→  The green LED lights up continuously for 2 seconds, then goes out. 

The MiteMap is then cleared.

<u>Note</u>: After a RESET, the html pages of the MiteMap do not automatically update, you must restart the acquisition program so that the "Data" and "Live" tabs update. In the same way, the "Images" tab will only be updated if new images are acquired.

# Monitoring and Data Recovery

The MiteMap embeds an Apache 2 server which provides a Web Interface, written in `html` and `php`. To access the interface, connect the MiteMap using Wifi or with an Ethernet cable. Then open a Browser and type the IP address of the MiteMap. The main page of the MiteMap shows a Heat Map representing the distribution of the mite inside the arena :

![Heat_Map](https://raw.githubusercontent.com/LR69/MiteMap/master/images/MT01_carte_thermique_2020_05_08_19h12m09s.png)




## Tab "images"

When the Push  [Record button](#record_BP)	 has been used to store images, this tab is used to check and download the images. Images are displayed as a link to the raw and processed images (at the bottom of the page). All the images of a record are available at download as a `.zip` file containing images at `.jpg` format. 

- Download the zip of the images by clicking on the links, then unzip the images and check that they are viewable. 
- If needed, jpeg images can be added (using [ffmpeg](https://www.ffmpeg.org/) for instance), to form a video. 

This tab can also be used to trigger automatically video acquisitions, on a certain level of mites being tracked at the same time, or on a periodic basis.

## Tab "Live"

On this page, two images are continuously updated by the program. 

1. The first image is the raw image take by the camera,
    ![image_brute_2020_05_09_20h16m50s.652041.jpg](https://github.com/LR69/MiteMap/blob/master/images/image_brute_2020_05_09_20h16m50s.652041.jpg?raw=true)
2. On the second image, elements related to image processing have been added.
   ![imag_traitée](https://raw.githubusercontent.com/LR69/MiteMap/master/images/image_traitee_2020_05_09_20h16m50s.652041.jpg)

