def rd(k1,k2,h1,h2):
    """
    calcule le coefficient d'échange surfacique entre 2 couches de conductivité k1 et k2 et d'épaisseurs h1 et h2

    W/(m2K)
    """
    return 2*k1*k2/(h1*k2+h2*k1)

def besoin_bat(Tconsigne,Text,Rm,Ri,Rf):
    """
    Calcul les besoins du bâtiment avec le modèle RC

    
    """
    Rthe=1/(1/(Rm+Ri)+1/Rf)# Résistance thermique équivalente 
    return (Tconsigne-Text)/Rthe