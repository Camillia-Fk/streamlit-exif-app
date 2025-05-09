# Fichier....... : Streamlit_exif_app.py
# Rôle ......... : Application Streamlit
# Auteur ........: Camillia ALAMI CHENTOUFI
# Version .......: V1.0 du 09/05/2025
# Licence .......: Outils Informatiques Collaboratifs Chap 4.2 
          
import streamlit as st
from PIL import Image as PILImage
from exif import Image as ExifImage
import piexif
import os

# --- Initialisation d'une variable persistante pour stocker les modifications   
# faites sur les metadonnées EXIF dans l'application ---
if "modifications" not in st.session_state:
    st.session_state.modifications = {}  


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


def main():

    # Le titre principal de l'application.
    st.title("Éditeur EXIF Streamlit")

    # Détermine le chemin vers l'image à utiliser.
    path = "paysage.jpg"

    # Charger l'image avec PIL pour l'affichage, et avec ExifImage pour accéder aux métadonnées EXIF.
    exif_img = load_image(path)

    # Vérifier si l'image contient des métadonnées EXIF.
    if exif_img.has_exif:

        # Appel de fonction
        formulaire_affichage(exif_img)

        # Séparation avec un trait
        st.markdown("---")
        formulaire_modification(exif_img)
    else:
        st.warning("Cette image ne contient pas de métadonnées EXIF.")

if __name__ == "__main__":
    main()
