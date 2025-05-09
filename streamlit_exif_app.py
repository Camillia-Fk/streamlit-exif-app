# Fichier....... : Streamlit_exif_app.py
# Rôle ......... : Application Streamlit
# Auteur ........: Camillia ALAMI CHENTOUFI
# Version .......: V2.0 du 09/05/2025 
# Licence .......: Outils Informatiques Collaboratifs Chap 4.2 
          
import streamlit as st
from PIL import Image as PILImage
from exif import Image as ExifImage
import folium
from streamlit_folium import st_folium
import os

# --- Initialisation d'une variable persistante pour stocker les modifications   
# faites sur les metadonnées EXIF dans l'application ---
if "modifications" not in st.session_state:
    st.session_state.modifications = {}  # { nom_de_tag: nouvelle_valeur }

# ---  Convertit des coordonnées GPS en DMS (degrés, minutes, secondes) 
# en format décimal, en tenant compte de l'hémisphère (N/S, E/W). ---
def dms_float_to_decimal(dms, ref):

    # Extraction des degrés, minutes et secondes
    deg, minutes, seconds = dms

    # Conversion en format décimal
    # 1 degré = 60 minutes, 1 minute = 60 secondes
    result = deg + minutes / 60 + seconds / 3600

    # Ajustement pour l'hémisphère sud (S) ou ouest (W), qui sont négatifs
    return -result if ref in ['S', 'W'] else result


# --- Charge l'image depuis le chemin donné, l'affiche dans Streamlit,
# et renvoie un objet ExifImage pour lire/écrire les EXIF.---
def load_image(path):

    # Ouverture de l'image avec pil
    pil = PILImage.open(path)

    #Affichage dans l'application streamlit
    st.image(pil, caption=f"Image originale : {path}", use_container_width=True)
    
    #Création d'un objet ExifImage et ouverture en mode binaire afin de lire les métadonnées EXIF 
    with open(path, "rb") as f:

        #exif_img contient les metadonnées EXIF de mon image
        exif_img = ExifImage(f)
    return exif_img

# --- Détecter les balises EXIF modifiables (lecture seule) ---
def get_modifiable_tags(exif_img):
    modifiable = []

    # Parcours toutes les metadonnées EXIF de l'image
    for tag in exif_img.list_all():

        # je test si les métadonnées sont accessible (lecture), 
        # si oui, cela signifie qu'elle est potentiellement modifiable
        try:
            _ = getattr(exif_img, tag)
            modifiable.append(tag)

        # Si une exception est levée (lecture interdite), on ignore cette balise
        except Exception:
            pass
    return modifiable

# --- Formulaire d'affichage (menu déroulant) pour voir toutes les métadonnées y compris celles non modifiable ---
def formulaire_affichage(exif_img):

    # Affiche un sous-titre pour cette section dans l'interface Streamlit
    st.subheader("Afficher une métadonnée EXIF")

    # Récupère toutes les balises EXIF de l'image sous forme de liste
    tags = exif_img.list_all()

     # Crée une liste déroulante (selectbox) pour permettre à l'utilisateur de choisir une balise
    tag = st.selectbox("Balise à afficher", tags)

    # Crée un bouton pour afficher la valeur de la balise sélectionnée
    if st.button("Afficher la valeur"):

        # Récupère la valeur de la balise sélectionnée et l'affiche (en vert) si elle est lisible
        try:
            st.success(f"{tag} : {getattr(exif_img, tag)}")
        
        # Affiche un message d'erreur si la balise n'est pas accessible (en jaune)
        except Exception as e:
            st.warning(f"Impossible de lire '{tag}' ({e})")


# --- Affiche un champ texte pour chaque balise détectée et stocke
# les nouvelles valeurs dans st.session_state. ---
def formulaire_modification(exif_img):

     # Affiche un sous-titre pour cette section dans l'interface Streamlit
    st.subheader("Modifier toutes les métadonnées EXIF")

    # Récupèration une liste de toutes les balises EXIF potentiellement modifiables.
    mod_tags = get_modifiable_tags(exif_img)

    # Vérification si la liste des balises modifiables est vide.
    if not mod_tags:
        st.info("Aucune balise modifiable détectée.")
        return

    # Création du Formulaire de Modification avec l'id form_modif
    with st.form("form_modif"):

        # Initialise un dictionnaire vide pour stocker les nouvelles valeurs des balises.
        new_values = {}

        # Tente de lire la valeur actuelle de chaque balise modifiable.
        for tag in mod_tags:
            try:
                actuel = getattr(exif_img, tag)
            except Exception:
                actuel = ""

            # Affiche un champ texte pour chaque balise avec le nom de la balise, 
            # sa valeur par défaut et une clé unique pour éviter les conflits de nom
            new_values[tag] = st.text_input(f"{tag}", value=str(actuel), key=f"input_{tag}")

        # Bouton de soumission du formulaire
        if st.form_submit_button("Enregistrer les modifications"):

            # Enregistrement des modifications
            for tag, val in new_values.items():
                try:
                    # Vérifier l'ancienne valeur pour éviter d'écraser inutilement une balise avec la même donnée
                    old = getattr(exif_img, tag)
                # En cas d'erreur, défninir l'ancienne valeur comme None pour éviter les exceptions.
                except Exception:
                    old = None
                # Condition d'enregistrement, la nouvelle valeur ne doit pas être vide et doit être différente de l'ancienne
                if val != "" and val != str(old):
                    st.session_state.modifications[tag] = val
            
            # Confirmer l'enregistrement
            st.success("Modifications enregistrées !")


#Affiche sur une carte Folium la position GPS extraite des métadonnées EXIF 
#   d'une image, si les données GPS sont présentes.
def afficher_carte_position(exif_img):
    try:
        # Récupère les coordonnées GPS sous forme de tuples (degrés, minutes, secondes)
        lat = exif_img.gps_latitude
        lon = exif_img.gps_longitude

        # Récupère les références de direction (N/S pour la latitude, E/W pour la longitude)
        lat_ref = exif_img.gps_latitude_ref
        lon_ref = exif_img.gps_longitude_ref

        # Vérifie que les coordonnées sont au format attendu (tuple de 3 valeurs)
        if isinstance(lat, tuple) and all(isinstance(x, float) for x in lat):
            # Conversion en décimal
            lat = dms_float_to_decimal(lat, lat_ref)
        else:
            raise ValueError(f"Latitude inattendue : {lat}")

        if isinstance(lon, tuple) and all(isinstance(x, float) for x in lon):
            # Conversion en décimal
            lon = dms_float_to_decimal(lon, lon_ref)
        else:
            raise ValueError(f"Longitude inattendue : {lon}")

        # Création de la carte centrée sur les coordonnées GPS extraites
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Ajout d'un marqueur à l'emplacement des coordonnées GPS
        folium.Marker([lat, lon], tooltip="Position extraite des EXIF").add_to(m)

        # Affichage de la carte dans Streamlit
        st.subheader("📍 Position GPS issue de l'image")
        st_folium(m, width=700, height=450)

    # Gestion des erreurs, comme l'absence de données GPS ou un format incorrect
    except Exception as e:
        st.warning(f"Erreur lors de la lecture des coordonnées GPS : {e}")

# --- Affiche une carte interactive avec des marqueurs pour chaque lieu visité 
# et relie ces lieux avec une ligne pour représenter les trajets. ---
def afficher_carte_voyages():

    # Affiche un sous-titre pour la section des voyages
    st.subheader("Carte des lieux visités")

     # Liste des lieux visités avec leurs coordonnées GPS (latitude, longitude) et leur nom
    lieux = [
        [20.2513, -10.5786, "Mauritanie"],
        [31.7917, -7.0926, "Maroc"],
        [14.4974, -14.4524, "Sénégal"],
        [-18.7669, 46.8691, "Madagascar"],
        [56.1304, -106.3468, "Canada"],
        [46.6034, 1.8883, "France"],
        [40.4637, -3.7492, "Espagne"],
        [38.9637, 35.2433, "Turquie"],
        [39.0742, 21.8243, "Grèce"],
        [-0.8037, 11.6094, "Gabon"]
    ]

    # Création d'une carte centrée sur un point "moyen" pour englober tous les lieux
    # Le point (20, 0) est choisi pour être à peu près au centre des lieux listés
    # Créer la carte centrée sur un point central
    m = folium.Map(location=[20, 0], zoom_start=2)

    # Liste pour stocker les points pour tracer la ligne entre les lieux
    points = []

    # Boucle sur chaque lieu pour ajouter les marqueurs sur la carte
    for lat, lon, nom in lieux:

        # Ajout d'un marqueur pour chaque lieu avec un tooltip (nom affiché au survol) et un popup (nom affiché au clic)
        folium.Marker([lat, lon], tooltip=nom, popup=nom).add_to(m)

        # Stocke les coordonnées pour tracer une ligne entre les lieux
        points.append([lat, lon])
    
    # Création d'une ligne reliant tous les lieux visités
    folium.PolyLine(points, color="blue", weight=2.5, opacity=0.7).add_to(m)

    # Affichage de la carte dans l'application Streamlit
    st_folium(m, width=700, height=450)



# --- 7. Main ---
def main():
    st.title("Éditeur EXIF avec cartes de voyage")
    path = "paysage.jpg"
    img = load_image(path)
    if img.has_exif:
        st.markdown("---")
        formulaire_affichage(img)
        st.markdown("---")
        formulaire_modification(img)
        st.markdown("---")
        afficher_carte_position(img)
        st.markdown("---")
        afficher_carte_voyages()
    else:
        st.warning("Pas de métadonnées EXIF ici.")

if __name__ == "__main__":
    main()
