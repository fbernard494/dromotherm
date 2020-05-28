import numpy as np
def rd(k1,k2,h1,h2):
    """
    calcule le coefficient d'échange surfacique entre 2 couches de conductivité k1 et k2 et d'épaisseurs h1 et h2

    W/(m2K)
    """
    return 2*k1*k2/(h1*k2+h2*k1)

def besoin_bat(Tconsigne,Text,Rm,Ri,Rf):
    """
    Calcule les besoins du bâtiment avec le modèle RC

    Tconsigne : température de consigne en °C

    Text : vecteur numpy de la température extérieure

    Rm : Résistance thermique des murs (K/W)

    Ri : Résistance superficielle intérieure (K/W)

    Rf : résistance de fuite (infiltrations+vitre+renouvellement d'air) K/W

    return : vecteur numpy du besoin instantanné de chauffage en W

    Par analogie électrique, on assimile les températures à des tensions et les puissances à des intensités

    en première approximation, on a donc (Tint-Text)/(Rm+Ri) + (Tc-Text)/Rf + C dTint/dt = Qchauffage

    soit C dTint/dt = Qchauffage - (Tint-Text) * (1/(Rm+Ri) + 1/Rf)

    Pour maintenir Tint constante et égale à Tconsigne, on doit donc développer :

    Qchauffage = (Tconsigne-Text) * (1/(Rm+Ri) + 1/Rf)

    """
    return (Tconsigne-Text)*(1/(Rm+Ri)+1/Rf)

def sol_tridiag(A,B,C,D):
    """
    Résout un système matriciel de la forme MX=D avec M une matrice 
    tridiagonale ayant:
    A: vecteur constituant la diagonale principale 
    B: vecteur constituant la diagonale supérieure
    C: le vecteur constituant la diagonale inférieure
    """
    N = A.size
    alpha=np.zeros((N))
    beta=np.zeros((N))
    X=np.zeros((N))
    alpha[0]=A[0]

    beta[0]=D[0]/alpha[0]
    for i in range(0,N-1):
        alpha[i+1]=A[i+1]-(C[i+1]*B[i])/alpha[i]
        beta[i+1]=(D[i+1]-B[i]*beta[i])/alpha[i+1]
    X[N-1]=beta[N-1]
    for i in range(N-2,-1,-1):
        X[i]=beta[i]-(B[i]*X[i+1]/alpha[i])
    return X

def Tsorties_echangeur(Te1,Te2,mf1,mf2,Cp1,Cp2,eff):
    """
    Calcul les températures au niveau des sorties d'un échangeur thermique'

    Parameters
    ----------
    Te1 : Température d'entrée du fluide chaud
        
    Te2 : Température d'entrée du fluide froid
        
    mf1 : Débit massique du fluide chaud
        
    mf2 : Débit massique du fluide froid
        
    Cp1 : Capacité calorifique massique du fluide chaud
        
    Cp2 : Capacité calorifique massique du fluide froid
        
    eff : efficacité de l'échangeur
        

    Returns
    -------
    Ts1 : Température de sortie du fluide chaud
        
    Ts2 : Température de sortie du fluide froid
        

    """
    if (mf1*Cp1)<=(mf2*Cp2):
        Ts1=Te1-eff*(Te1-Te2)
        Ts2=Te2+(mf1*Cp1/(mf2*Cp2))*(Te1-Ts1)
    else:
        Ts2=Te2-eff*(Te1-Te2)
        Ts1=Te1+(mf2*Cp2/(mf1*Cp1))*(Te1-Ts1)
    return Ts1,Ts2

