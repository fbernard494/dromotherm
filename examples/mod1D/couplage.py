import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from dromosense.tools import *
from dromosense.constantes import rho_eau,Cpf,kelvin
from scipy.integrate import odeint
#from scipy.integrate import solve_ivp
import cmath as math

verbose = False

# débit dans le dromotherme
qdro = 0.035/3600 # m3/s

start = 1483232400
#summerStart = 1496278800
summerStart=1493600400 # 1er mai 
summerEnd = 1506819600 # 30 septembre
#summerEnd=1504141200 # 30 août
step=3600

"""
IMPORTATION DES DONNES METEOS (VARIABLES EN FONCTION DU TEMPS)
0 : temps exprime en heure
1 : temperature d'air (en deg Celsius)
2 : rayonnement global (en W/m2)
3 : rayonnement atmospherique (en W/m2)
4 : vitesse du vent (en m/s)
"""
meteo = np.loadtxt('../../datas/corr1_RT2012_H1c_toute_annee.txt')
meteo=np.concatenate((meteo,meteo))
meteo[8760:meteo.shape[0],0]=meteo[8760:meteo.shape[0],0]+8760
print(meteo.shape)
f2 = 1000.0*1.1*(0.0036*meteo[:,4]+0.00423)
f1 = (1.0-albedo)*meteo[:,2] + meteo[:,3] + f2*(meteo[:,1]+kelvin)

# instanciation d'un dromotherme 1D - input.txt contient les paramètres calant ce modèle sur le modèle 2D
dromo=OneDModel('input.txt',step,meteo.shape[0],4,0.75,qdro)
dromo.f1 = f1
dromo.f2 = f2
dromo.T[0,:,:] = np.ones((dromo.T.shape[1],dromo.T.shape[2]))*10+kelvin
print(dromo.T[0,:,:])

# juste pour voir la différence entre ce modèle couplé et le modèle à température d'injection fixe
T = np.loadtxt('T1d.txt')
print(T.shape)
input("press any key")


def F(y,t):
    """
    y : Tsable = Tstockage

    t : time index

    result : dy/dt = dTsable/dt = dTstockage/dt
    """
    i = int(t/step)
    if verbose:
        print("we have t={} and y={}".format(i,y))

    if i<=i_summerEnd and i>=i_summerStart:
        """
        en été, on récupère de l'énergie et on alimente le stockage
    
        """
        work_dro=1
    else:
        work_dro=0
    dromo.iterate(i,Tinj_dro[i-1]+kelvin)

    Tsor_dro[i]=dromo.T[i,1,-1]-kelvin

    Tsor_sto[i] = ( k * y + B * Tsor_dro[i] ) / ( k + B)

    Tinj_sto[i] = Tsor_sto[i] + coeff * eff * (Tsor_dro[i] - Tsor_sto[i])

    Tinj_dro[i] = Tsor_dro[i] - eff * (Tsor_dro[i] - Tsor_sto[i])
    Tinj_pac[i]=y-C*Pgeo[i]/k
    Tsor_pac[i]=Tinj_pac[i]-Pgeo[i]/(mpac*cpac)

    der = (work_dro*msto * cpsto * (Tinj_sto[i] - Tsor_sto[i])-Pgeo[i] / (m_sable * Cp_sable)) / (m_sable * Cp_sable)
    #else:
       # """
        #en hiver on consomme à hauteur de Pgeo
       # """
       # der = -Pgeo[i] / (m_sable * Cp_sable)

        #Tinj_pac[i]=y-C*Pgeo[i]/k

        #Tsor_pac[i]=Tinj_pac[i]-Pgeo[i]/(mpac*cpac)
        #der = (mpac*cpac*(Tsor_pac[i]-Tinj_pac[i])) / (m_sable * Cp_sable)

    if verbose:
        print("dTsable/dt is {}".format(der))

    return der


# température d'entrée et de sortie du fluide dans le stockage
Tinj_sto=np.zeros(meteo.shape[0])
# température de sortie du fluide après transit dans le stockage
Tsor_sto=np.zeros(meteo.shape[0])
# température d'entrée du fluide géothermique dans le stockage (sortie de la PAC)
Tsor_pac=np.zeros(meteo.shape[0])
# température de sortie du fluide géothermique dans le stockage (entrée  de la PAC)
Tinj_pac=np.zeros(meteo.shape[0])
"""
On initialise les températures d'injection et de sortie dans le dromotherme à 10
de fait, quant il n'y aura pas de récupération d'énergie, le bilan énergétique sera nul
"""
# température d'injection du fluide dans le dromotherme
Tinj_dro=10*np.ones(meteo.shape[0])
# température de sortie de fluide après collecte de chaleur dans le dromotherme
Tsor_dro=10*np.ones(meteo.shape[0])


"""
massif de stockage
"""
m_sable=70200.0 # masse de sable en kg
Cp_sable=1470.0 # capacité calorifique massique du sable en J/Kg.K

"""
paramètres définissant le système géothermique équipant le stockage
"""
R1=0.0102 # Rayon intérieur du tube
R2=0.0125 # Rayon extérieur
L_tube=5 # Longueur tube en m
N_tube=16  # Nombre de tubes
# conductivités en W/(K.m)
lambda2=15.8
lambda_tube=1.32
Nu=4.36 # Nombre de Nusselt de l'écoulement du fluide à l'intérieur des tubes
Rcond=np.log(R2/R1)/(2*math.pi*N_tube*L_tube*lambda_tube)
Rconv=1/(math.pi*Nu*N_tube*L_tube*lambda2)
# k exprimé en W/K
k=1/(Rcond+Rconv)

print("le k du système géothermique vaut {} W/K".format(k))

# efficacité de l'échangeur
eff = 0.8
# débit dans la partie de l'échangeur côté "stockage"
qsto = 1.2*qdro
# rho_eau en provenance du fichier constantes est expérimée en kg/m3
# Cpf en provenance du fichier constantes est exprimée en J/(kg.K)
mdro = qdro * rho_eau
msto = qsto * rho_eau
cpdro = Cpf
cpsto = Cpf

coeff = (mdro * cpdro) / (msto * cpsto)

B = (msto * cpsto -k/2) * coeff * eff

print("coeff vaut {} B vaut {} W/K".format(coeff, B))

"""
besoin en chauffage
"""
Tconsigne=19
# toutes les résistances sont exprimées en K/W
Rm=8.24E-02 # Résistance thermique des murs
Ri=1.43E-03 # Résistance superficielle intérieure
Rf=3.4E-02 # Résistance due aux infiltrations+vitre et au renouvellement d'air
# facteur solaire pour des matériaux plein de type murs/toits
FSm=0.0048
"""
hypothèse : la maison fait 4 mètres de large sur 5 mètres de long
vu du ciel c'est donc un rectangle de 20m2 de surface
"""
Scap = 20

"""
PAC
"""
COP=3
mpac=msto
cpac=4180.0
C=1-k/(2*mpac*cpac)

"""
on calcule les index permettant de boucler sur l'été, ainsi que le besoin net du bâtiment et la puissance géothermique à développer
"""
i_summerStart=(summerStart-start)//step
i_summerEnd=i_summerStart+(summerEnd-summerStart)//step
print("nous allons simuler la récolte énergétique entre les heures {} et {}".format(i_summerStart,i_summerEnd))
input("press any key")

apport_solaire = Scap * FSm * meteo[:,2]

besoinBrut = besoin_bat(Tconsigne,meteo[:,1],Rm,Ri,Rf)

besoin = besoinBrut - apport_solaire

besoin[i_summerStart:i_summerEnd] = np.zeros(i_summerEnd-i_summerStart)

besoin[i_summerStart+8760:i_summerEnd+8760]=np.zeros(i_summerEnd-i_summerStart)
Pgeo=(COP-1)*besoin/COP

besoin_surfacique=besoin/Scap

"""
SOLVEUR
Tsable : Température du stockage/sable
"""
#simEnd=i_summerEnd+2000
simEnd=i_summerStart+365*24
Tsable = odeint(F,10,meteo[i_summerStart:simEnd,0]*3600)

"""
BILAN ENERGETIQUE
"""
Surface_dro=4
# d et f : index de début et de fin sur lesquels on va réaliser le bilan
# dr et fr : index de début et de fin de la récupération/collecte énergétique
d = i_summerStart
f = simEnd
dr = i_summerStart
fr = i_summerEnd
Pdro=mdro*cpdro*(Tsor_dro[d:f]-Tinj_dro[d:f])/Surface_dro # en W/m^2
# toutes valeurs en kWh/m^2
Edro=(np.sum(Pdro))*step/(3600*1000)
Esolaire=(np.sum(meteo[dr:fr,2]))*step/(3600*1000)
conso_bat=(np.sum(besoin_surfacique[d:f]))*step/(3600*1000)
Eelec=conso_bat/COP
Eprimaire=2.58*Eelec
# taux de récupération en %
Taux=Edro*100/Esolaire

"""
affichages énergétiques
"""
from datetime import datetime
from dateutil import tz
CET=tz.gettz('Europe/Paris')
_s=datetime.fromtimestamp(summerStart,CET).strftime('%Y-%m-%d %H:%M:%S')
_e=datetime.fromtimestamp(summerStart+(simEnd-i_summerStart),CET).strftime('%Y-%m-%d %H:%M:%S')
print("Bilan énergétique sur la période : {} à {}".format(_s,_e))
print('Energie récupérée par le dromotherm : {} kWh/m2'.format(Edro))
print('Energie solaire recue : {} kWh/m2'.format(Esolaire))
print('Taux de récupération : {} %'.format(Taux))
print('Consommation du bâtiment : {} kWh/m2'.format(conso_bat))
print('Energie électrique consommée par la PAC : {} kWh/m2'.format(Eelec))
print('Energie primaire consommée par la PAC : {} kWh/m2'.format(Eprimaire))

"""
courbes et graphiques
"""
figure = plt.figure(figsize = (10, 10))
matplotlib.rc('font', size=8)

ax1 = plt.subplot(411)
l1="couplage dromotherme/échangeur de séparation de réseau/stockage/PAC et simulation été/hiver"
l2="température de consigne dans le bâtiment : {} °C".format(Tconsigne)
plt.title("{}\n{}\n".format(l1,l2))
plt.ylabel('dromotherme °C')
#ax1.plot(T[:,1],label="avec Tinj constante", color="orange")
ax1.plot(Tsor_dro,label="Tsor_dro",color="red")
ax1.plot(Tinj_dro,label="Tinj_dro",color="purple")
ax1.legend()

ax2 = plt.subplot(412, sharex=ax1)
plt.ylabel('stockage °C')
ax2.plot(Tinj_sto,label="Tinj_sto",color="orange")
ax2.plot(meteo[i_summerStart:simEnd,0],Tsable,label="Tsable",color="red")
ax2.plot(Tsor_sto,label="Tsor_sto",color="blue")
ax2.legend()

ax3 = plt.subplot(413, sharex=ax1)
plt.ylabel('PAC °C')
ax3.plot(Tinj_pac,label="Tinj_pac",color="k")
ax3.plot(Tsor_pac,label="Tsor_pac",color="#7cb0ff")
ax3.legend()

ax4 = plt.subplot(414, sharex=ax1)
plt.ylabel('Bâtiment W')
plt.xlabel("Temps - 1 unité = {} s".format(step))
ax4.plot(besoin,label="besoin net W",color="orange")
ax4.legend()

plt.show()



