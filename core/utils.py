def get_currency_by_country(country):
    """
    Renvoie la devise correspondant au pays donné.

    Args:
        country (str): Le nom du pays.

    Returns:
        str: La devise (XAF, XOF ou USD).
    """
    # Liste des pays utilisant XOF
    local_countries_xof = [
        'BURKINA FASO', 
        'COTE D\'IVOIRE', 
        'MALI', 
        'SENEGAL', 
        'BENIN', 
        'TOGO'
    ]
    
    # Normaliser le nom du pays en majuscules
    country_upper = country.upper()

    if country_upper == "CAMEROON":
        return "XAF"
    elif country_upper in local_countries_xof:
        return "XOF"
    else:
        return "USD"

# Exemple d'utilisation
""" pays = "Cameroon"
devise = get_currency_by_country(pays)
print(f"La devise pour {pays} est {devise}.") """
