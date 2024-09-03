import tkinter as tk
import numpy as np
import time
import numpy as np
import random
import time
from numpy.lib import stride_tricks
import matplotlib.pyplot as plt
from matplotlib import cm
import threading

class Fenetre(tk.Tk):
    """La fenêtre qui affichera la forêt simulée."""
    def __init__(self):
        super().__init__()
        #la forêt qui sera simulée.
        self.foret = Foret(75,150)
        #Grille d'affichage correspondant à la grille forêt.
        self.rectGrid = [[(None,None) for i in range(self.foret.nC)] for j in range(self.foret.nL)]
        #taille d'affichage d'un carreau de la grille forêt.
        self.a = 10
        #durée d'un tick (250 ms réelles) dans la simulation (en minutes).
        self.tickDuration = 5
        #temps écoulé dans la simulation (minutes) elle est en chiffre contrairement à timeElapsed qui est le texte affiché.
        self.tElapsed = 0
        #Code couleur pour faire correspondre la simulation à l'affichage.
        self.colorCode = {0:'forest green',1:'red',2:'ivory',3:'gray29',4:'blue'}
        #initialisation
        self.creerWidgets()
        self.playing = False
        self.skip = False
        self.suivant()
    
    def creerWidgets(self):
        """Création et disposition des widgets."""
        self.title("Le Feu")
        #le canvas pour afficher la grille sur l'écran.
        self.canvas = tk.Canvas(self, width=15 * self.a * self.foret.nC + 1, height=self.a * self.foret.nL + 1, highlightthickness=2)
        self.creerGrille()

        #le bouton pour allumer le feu
        fra = tk.Frame(self)
        self.bouText = tk.StringVar()
        #le texte du bouton est dynamique, il change selon si l'on est au
        #début, en pause ou en cours de propagation.
        self.bouText.set("Commencer")
        self.bou1 = tk.Button(fra,textvariable=self.bouText, width=15, command=self.play)
        self.bou1.pack(side='left')
        #le slider qui permet de modifier l'angle du vent
        la = tk.Label(fra,text="Angle du vent (°)")
        la.pack(side='right')
        self.scala2 = tk.Scale(fra, from_=0, to=360, orient=tk.HORIZONTAL)
        self.scala2.set(45)
        self.scala2.pack(side='right')
        #slider pour l'humidité
        la = tk.Label(fra,text="humidité (%)")
        la.pack(side='right')
        self.scala_humid = tk.Scale(fra, from_=5, to=50, orient=tk.HORIZONTAL)
        self.scala_humid.set(int(self.foret.humidite_defaut * 100))
        self.scala_humid.pack(side='right')
        #slider pour la vitesse du vent
        la = tk.Label(fra,text="vitesse du vent (m/s)")
        la.pack(side='right')
        self.scala_vitesse = tk.Scale(fra, from_=0, to=40, orient=tk.HORIZONTAL)
        self.scala_vitesse.set(self.foret.v_vent_defaut)
        self.scala_vitesse.pack(side='right')
        self.timeElapsed = tk.StringVar()
        self.timeElapsed.set("temps écoulé: 0h 00 min")
        self.timeLab = tk.Label(fra,textvariable=self.timeElapsed)
        self.timeLab.pack(side='right')
        fra.pack()
        self.canvas.pack(fill='both')

    def modifierGrille(self):
        """Affichage sur la fenêtre des modifications enregistrées dans la forêt."""
        for x in range(self.foret.nL):
            for y in range(self.foret.nC):
                coul = self.colorCode[self.foret.grille[x,y]]
                recta,coulor = self.rectGrid[x][y]
                #la modification de la grille d'affichage n'a lieu que quand nécessaire afin d'améliorer les performances.
                if coul != coulor:
                    #modification de la couleur du rectangle affiché sur l'écran.
                    self.canvas.itemconfig(recta, fill=coul)
                    #modification du rectangle et de la couleur stockés dans la grille d'affichage.
                    self.rectGrid[x][y] = (recta,coul)
        #l'affichage est directement mis à jour (les couleurs changent sur l'écran).
        self.canvas.update()

    def creerGrille(self):
        """Création et initialisation des carreaux qui constituent la grille de la fenêtre."""
        for x in range(self.foret.nL):
            for y in range(self.foret.nC):
                coul = self.colorCode[self.foret.grille[x,y]]
                recta = self.canvas.create_rectangle((x * self.a, y * self.a, (x + 1) * self.a, (y + 1) * self.a), outline="gray", fill=coul)
                #les rectangles sont affichés puis stockés avec leur couleur dans la grille d'affichage.
                self.rectGrid[x][y] = (recta,coul)

    def play(self):
        self.playing = (not self.playing)
        if self.playing:
            #désactiver les curseurs pour ne pas les bouger pendant que la simulation est en cours.
            self.scala2.config(state='disabled')
            self.scala_humid.config(state='disabled')
            self.scala_vitesse.config(state='disabled')
            self.bouText.set("Pause")
        else:
            #réactiver les curseurs pour autoriser une modification pendant la pause.
            self.scala2.config(state='normal')
            self.scala_humid.config(state='normal')
            self.scala_vitesse.config(state='normal')
            self.bouText.set("Reprendre")
        if self.playing:
            #après avoir repris on enregistre les éventuelles modifications de l'angle du vent.
            self.foret.calculer_modele(self.scala_vitesse.get(),np.pi / 180 * self.scala2.get(),self.scala_humid.get() / 100)

    def suivant(self):
        """Fonction appelée régulièrement pour faire avancer la simulation."""
        #itération suivante appelée au début pour être sûr que l'intervalle soit constant.
        self.after(250,self.suivant)
        #la forêt n'est pas modifiée si on est en pause.
        if self.playing:
            #évolution de la forêt.
            self.foret.evolutionFeu()
            #avancée du temps.
            self.tElapsed += int(self.tickDuration * self.foret.distortion_temps)
            hours = self.tElapsed // 60
            minutes = self.tElapsed % 60
            minutes = str(minutes)
            if len(minutes) == 1:
                minutes = '0' + minutes
            self.timeElapsed.set("temps écoulé: " + str(hours) + "h " + minutes + " min")
            #affichage des modifications de la forêt sur la grille.
            if not self.skip:
                #le skip est utilisé dans le cas où la modification de l'affichage prend plus de 250ms.
                #éviter que l'itération suivante modifie l'affichage tant que cette itération n'a pas fini.
                #les problèmes de performance ne ralentiront donc pas le feu.
                #en revanche, en cas de problème de performance, l'affichage sera mis à jour à des intervalles plus espacés.
                self.skip = True
                self.modifierGrille()
                self.skip = False
                
class Foret(object):
    """La simulation de la forêt qui sera affichée."""
    def __init__(self,nC,nL):
        #taille de la forêt.
        self.nC = nC
        self.nL = nL
        #paramètre (coeff de l'humidité utilisé à deux endroits).
        self.a = 2.10
        #probabilités de base.
        self.pNonArbre = 0.25
        #coefficient d'extinction
        self.coeffExtinction = 0.05
        #point d'eau
        self.caseEau=(int(3*nL/4),int(1*nC/4))
        #probabilité d'extinction des cases à l'intérieur du périmètre du feu
        #(pas de végétal adjacent).
        self.coeffExtinction_interieur = 0.2
        #valeurs par défaut des paramètres.
        self.distortion_temps = 1
        self.v_vent_defaut = 3
        self.humidite_defaut = 0.2
        #initialisation
        self.grille = self.initialiserForet()
        self.calculer_modele(self.v_vent_defaut,np.pi / 4, self.humidite_defaut)
        
    def initialiserForet(self):
        """Initialisation de la forêt."""
        # creation de la grille.
        etat = np.zeros((self.nL,self.nC))
        #initialisation de la grille.
        for i in range(self.nL):
            for j in range(self.nC):
                if (random.random() < self.pNonArbre) or (i == (self.nL - 1)) or (i == 0) or j == (self.nC - 1) or (j == 0):
                    etat[i,j] = 2
        # choix du départ du feu.
        etat[self.nL // 2,self.nC // 2] = 1
        if not self.caseEau is None:
            etat[self.caseEau[0],self.caseEau[1]]=4
            etat[self.caseEau[0]+1,self.caseEau[1]]=4
            etat[self.caseEau[0],self.caseEau[1]+1]=4
            etat[self.caseEau[0]-1,self.caseEau[1]]=4
            etat[self.caseEau[0],self.caseEau[1]-1]=4

        return etat

    def evolutionFeu(self):
        """Evolution du feu: calcul des probabilités et tirage."""

        #tous ces calculs sont fait via numpy sans boucle for.
        #numpy lance les calculs directement en C ce qui permet une exécution
        #plus rapide.

        #voisinages
        #on copie la grille pour s'assurer que les calculs soient effectués
        #avant les modifications.
        grille1 = self.grille.copy()
        #les strides sont habituellement utilisées pour du traitement d'image
        #par exemple pour flouter une image en remplaçant un point par la
        #moyenne de ses voisins.
        #Le principe est d'augmenter le nombre de dimensions ici en passant de
        #deux à 4 dimensions.
        #on transforme un tableau de nombres en un tableau de matrices 3x3
        #la matrice 3x3 qui remplacent le nombre contient le nombre lui-même et
        #ses 8 voisins.
        #les strides manipulent directement la représentation binaire du
        #tableau dans la mémoire.
        #bien que risquée et à manipuler avec extrême précaution, cette méthode
        #offre un GIGANTESQUE gain de performance.
        #plus d'info ici:
        #https://realpython.com/numpy-array-programming/#image-feature-extraction
        shape = (grille1.shape[0] - 2, grille1.shape[1] - 2, 3, 3)
        patches = stride_tricks.as_strided(grille1, shape=shape, strides=(2 * grille1.strides))

        #allumage
        #on coupe les bords car les cases sans voisins n'ont pas été stridées.
        #la multiplication termes à termes annulera les coefficients de
        #vitesses pour les cases éteintes.
        allumage = (patches == 1) * self.mesh_v[1:(self.nL - 1),1:(self.nC - 1)]
        #on somme ensuite les matrices de vitesse avant de les diviser par le
        #total pour obtenir les probabilités.
        allumage = (allumage.sum(axis=(-1, -2)) / (self.mesh_v[1:(self.nL - 1),1:(self.nC - 1)]).sum(axis=(-1, -2)))*(self.mesh_h[1:(self.nL - 1),1:(self.nC - 1)])
        #on tire un tableau de nombre aléatoires (un nombre par case)
        rdms = np.random.rand(self.nL - 2,self.nC - 2)#tirage
        grille2 = self.grille[1:(self.nL - 1),1:(self.nC - 1)]
        #on compare ces nombres avec les probabilités d'allumage et on allume
        #si le nombre est en-dessous de la probabilité.
        grille2[(rdms < allumage) & (grille2 == 0)] = 1

        #extinction
        #cases n'ayant pas de végétation adjacentes sont considérées comme
        #ayant plus de chances de s'éteindre.
        #le front de flamme étant déjà passé aux autres cases, le peu de feu
        #qui reste s'éteint plus facilement.
        #On considère ces cases comme "finies".
        extinction = (patches == 0)#cases de végétal
        extinction[extinction == True] = 1
        extinction = extinction.sum(axis=(-1, -2))
        #le tableau contient maintenant le nombre de cases de végétal
        #adjacentes pour chaque case.
        rdms = np.random.rand(self.nL - 2,self.nC - 2)#tirage
        pcs_interieur = 1 - np.exp(-self.coeffExtinction_interieur * self.distortion_temps)
        grille2[(extinction == 0) & (grille2 == 1) & (rdms < pcs_interieur)] = 3
        #la probabilité d'extinction étant adjacente à des cases de végétal.
        pcons_perimetre = 1 - np.exp(-self.coeffExtinction * self.distortion_temps)
        grille2[(extinction != 0) & (rdms < pcons_perimetre) & (grille2 == 1)] = 3

        #update
        self.grille[1:(self.nL - 1),1:(self.nC - 1)] = grille2.copy()

    def champ_humidite(self,x,y):
        if self.caseEau is None:
            return 0
        d=((x-self.caseEau[0])**2+(y-self.caseEau[1])**2)**(1/2)
        if d<=2:
            return 5
        if d<=5:
            return 2 #valeur arbitraire/esthétique.
        return 0

### modèle physique
    def calculer_modele(self,un,alpha,humidite):
        """Calcul des tableaux de vitesses et de la distortion temporelle en fonction des nouvelles valeurs des paramètres."""
        #calcul de la matrice de vitesse
        mat_direction = self.calculerMatriceDirectionVent(alpha)
        vit = self.r(un,humidite) * mat_direction + np.ones((3,3))
        #à chaque point on associe sa matrice de vitesse 3x3
        print(vit)
        arr = np.ones((self.nL,self.nC,3,3))
        arr_h=np.ones((self.nL,self.nC))
        for i in range(self.nL):
            for j in range(self.nC):
                vit = (self.r(un,humidite+self.champ_humidite(i,j)) * mat_direction) + np.ones((3,3))
                arr[i,j] = vit
                #étang
                arr_h[i,j]=(1+self.a*humidite)/(1+self.a*(self.champ_humidite(i,j)+humidite))
        self.mesh_v = arr
        self.mesh_h= arr_h
        #selon les rapports de vitesse, le temps est accéléré ou décéléré
        self.distortion_temps = ((1 + self.a * humidite) / (1 + self.a * self.humidite_defaut)) * (self.r(self.v_vent_defaut,self.humidite_defaut) / (self.r(un,humidite)))


    def calculerMatriceDirectionVent(self,alpha):
        """Calcule la matrice de direction du vent."""
        vitesse_vent = np.zeros((3,3))
        for i in range(8):
            #on fait tourner un angle par les 8 directions.
            beta = i * np.pi / 4
            #voir diapo pour les justification des calculs
            value = np.cos(beta - alpha)
            #10^(-10) au lieu de 0 pour les erreurs de calcul de flottant sur les sin et cos.
            #seules les valeurs strictements positives doivent être prises en compte.
            #dans le cas contraire, on est contre le vent et la propagation sera prise comme sans vent.
            if value > 1e-10:
                #modification de la case correspondante dans la matrice du vent.
                vitesse_vent[1 + Foret.sgn(np.cos(beta)),1 + Foret.sgn(np.sin(beta))] = value
        #on utilise flip car l'axe des y de la grille est inversé.
        return np.flip(vitesse_vent,0)

    def sgn(x):
        #1 si x>0, 0 si x=0, -1 si x<0.
        #on utilise 10^(-10) au lieu de 0 pour prendre en compte les erreurs de
        #flottant.
        if abs(x) <= 1e-10:
            return 0
        return int(x / abs(x))

    def r(self,un,humidite):
        """Fonction clé du modèle physique, renvoie le rapport entre la vitesse sans vent, et la vitesse avec le vent donné."""
        A0 = 5.73
        b0 = 0.23
        rac = 1 + ((b0 * un - 1) / ((b0 * un) ** 2 + 1) ** (1 / 2))
        A = (A0 / ((1 + self.a * humidite) ** 3)) * rac
        A13 = A ** (1 / 3)
        B = A ** 2 + 9 * A + 3 * ((A + 81 / 4) ** (1 / 2)) + 27 / 2
        num = B ** (2 / 3) + A13 * (A + 6)
        den = B ** (1 / 3)
        r = 1 + (A13 / 3) * ((num / den) + A13 ** 2)
        return r
        
fenetre=Fenetre()
#on agrandit la fenêtre.
fenetre.state('zoomed')
fenetre.mainloop()
