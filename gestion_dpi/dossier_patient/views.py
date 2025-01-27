# views.py

# Importation des modules nécessaires
from django.shortcuts import render, redirect  # pour gérer les vues et les redirections
from django.contrib import messages  # pour afficher des messages flash
import requests  # pour envoyer des requêtes HTTP
from .models import DossierMedical, Soin ,CompteRendu
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# URL de l'API pour l'accès aux dossiers médicaux
API_BASE_URL = "http://127.0.0.1:8000/dossier_patient/api/dossier-medical/"


def login(request):
    """
    Handles user login by accepting email and password via a POST request, sending 
    the credentials to the API, and storing the authentication token and user details 
    in the session upon successful login.

    Args:
        request (HttpRequest): The incoming request object.

    Returns:
        HttpResponse: Redirects to the dashboard if login is successful, or to the 
        login page if unsuccessful or an error occurs.
    """
    if request.method == "POST":
        # Get the form data (email, password)
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Send the login credentials to the API
        data = {
            "email": email,
            "password": password
        }

        try:
            response = requests.post('http://127.0.0.1:8000/api/login/', json=data)
            response_data = response.json()

            if response.status_code == 200:  # If login is successful
                # Assuming the API sends back a JWT token
                token = response_data.get("token")
                nom = response_data.get("nom")
                prenom = response_data.get("prenom")
                role = response_data.get("role")
                id = response_data.get("id")
                
                if token:
                    # Store the token and other user details in session
                    request.session['auth_token'] = token  # Storing token in session
                    request.session['nom'] = nom  # Store nom in session
                    request.session['prenom'] = prenom  # Store prenom in session
                    request.session['role'] = role  # Store role in session
                    request.session['id'] = id

                    messages.success(request, "Login successful!")
                    return redirect('dashboard')  # Redirect to dashboard
                else:
                    messages.error(request, "Token missing from API response!")
                    return redirect('login')  # Redirect back to login if no token
            else:
                messages.error(request, f"Login failed: {response_data.get('error', 'Unknown error')}")
                return redirect('login')  # Redirect back to login if API returns an error

        except requests.exceptions.RequestException as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')  # Redirect back to login if there is an exception

    # If GET request, render the login form
    return render(request, 'login.html')


def logout(request):
    """
    Logs out the user by clearing the session data and redirecting to the login page.

    Args:
        request (HttpRequest): The incoming request object.

    Returns:
        HttpResponse: Redirects to the login page after logging out.
    """
    request.session.flush()  # Clear all session data
    messages.success(request, "You have logged out successfully.")
    return redirect('login')  # Redirect to the login page



def dashboard(request):
    """
    Displays the dashboard for different roles (Medecin, Patient, Radiologue, etc.) based 
    on the user's role stored in the session.

    Args:
        request: The HTTP request object containing session data and headers.

    Returns:
        A rendered template for the appropriate dashboard based on the user's role.
    """
    # Retrieve user details from session
    nom = request.session.get('nom')
    prenom = request.session.get('prenom')
    role = request.session.get('role')
    id = request.session.get('id')

    # Check if the user is authenticated (has token in session)
    if not request.session.get('auth_token'):
        return redirect('login')  # Redirect to login if no token is found

    headers = get_auth_headers(request)

    try:
        # Fetch all dossiers from the API
        response = requests.get(API_BASE_URL, headers=headers)
        if response.status_code != 200:
            raise Exception("Error fetching dossiers from the API")

        # Get the data from the API response
        dossiers = response.json()

        # Check the role and render different templates accordingly
        if role == 'Medecin':
            return render(request, 'dashboard_medecin.html', {
                'nom': nom,
                'prenom': prenom,
                'role': role,
                'dossiers': dossiers,
                'id': id,
            })
            
        elif role == 'Patient':
            
            response = requests.get(f"http://127.0.0.1:8000/api/get_nss_by_id/{id}", headers=headers)
            response_nss = response.json() 
            nss=response_nss.get('nss')
            response = requests.get(f"{API_BASE_URL}{nss}/lister_dossier_complet/", headers=headers)
            dossier = response.json() 
            return render(request, 'dashboard_patient.html', {
                'nom': nom,
                'prenom': prenom,
                'role': role,
                'id': id,
                'dossier_data': dossier,  # You can adjust to only show patient-specific dossiers if needed
            })
            
        elif role == 'Radiologue':
            return render(request, 'dashboard_radiologue.html', {
                'nom': nom,
                'prenom': prenom,
                'role': role,
                'id': id,
                'dossiers': dossiers,  # Radiologue might need all dossiers or specific ones
            })
            
        elif role == 'Infirmier':
            return render(request, 'dashboard_infirmier.html', {
                'nom': nom,
                'prenom': prenom,
                'role': role,
                'id': id,
                'dossiers': dossiers,  # Infirmier dashboard with dossiers
            })
        elif role == 'Laborantin':
            # Filter DossierMedical where associated BilanBiologique has no glycimie, cholesteroel, or pression_arterielle
            dossiers_laborantin = DossierMedical.objects.filter(
                bilans__glycimie__isnull=True,
                bilans__cholesteroel__isnull=True,
                bilans__pression_arterielle__isnull=True
            )
            return render(request, 'dashboard_laborantin.html', {
                'nom': nom,
                'prenom': prenom,
                'role': role,
                'id': id,
                'dossiers': dossiers_laborantin,  # Only show dossiers with missing values
            })
        
        else:
            # If no valid role is found
            messages.error(request, "Role non valide.")
            return redirect('login')

    except Exception as e:
        # Handle errors if the API call fails or other issues
        messages.error(request, f"Erreur lors du chargement des dossiers: {str(e)}")
        return redirect('login')


def get_auth_headers(request):
    """
    Retrieves authentication headers from the session for API requests.

    Args:
        request: The HTTP request object containing the session with the JWT token.

    Returns:
        A dictionary containing the Authorization header with the bearer token.

    Raises:
        PermissionError: If the authentication token is missing from the session.
    """
    token = request.session.get('auth_token')
    if not token:
        raise PermissionError("Token manquant. L'utilisateur n'est pas authentifié.")
    return {"Authorization": f"Bearer {token}"}

def create_dpi(request):
    """
    Creates a new Dossier Patient Informatisé (DPI) by sending form data to the API.

    Args:
        request: The HTTP request object containing the form data for creating a DPI.

    Returns:
        A redirect to the created DPI's page if successful, or back to the creation form
        with an error message if the creation fails.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}
        headers = get_auth_headers(request)
        response = requests.post(API_BASE_URL, json=data, headers=headers)
        # Process the response
        # ...
    return render(request, 'create_dpi.html')

def view_dpi(request, nss):
    """
    Displays a specific Dossier Patient Informatisé (DPI) based on the patient's NSS.

    Args:
        request: The HTTP request object.
        nss: The National Social Security number of the patient.

    Returns:
        A rendered template displaying the specific DPI, or an error message if the DPI
        is not found or the user is not authorized.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    try:
        headers = {"Authorization": f"Bearer {request.session.get('auth_token')}"}
        response = requests.get(f"{API_BASE_URL}{nss}/lister_dossier_complet/", headers=headers)
        # Process the response
        # ...
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erreur de communication avec l'API : {str(e)}")
        return redirect('dashboard')

# Vue pour rechercher un DPI (Dossier Patient Informatique)
def search_dpi(request):
    """Rechercher un dossier médical basé sur le numéro de sécurité sociale (NSS).

    Args:
        request (HttpRequest): La requête HTTP contenant le NSS du patient.

    Returns:
        HttpResponse: La réponse HTTP affichant le dossier médical ou un message d'erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    nss = request.GET.get('nss')
    if nss:
        headers = get_auth_headers(request)
        response = requests.get(f"{API_BASE_URL}{nss}/lister_dossier_complet/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            nom = request.session.get('nom')
            prenom = request.session.get('prenom')
            return render(request, 'dashboard_medecin.html', {'dossier_data': data, 'nom': nom, 'prenom': prenom})
        else:
            error_message = response.json().get('error', "Dossier médical introuvable.")
            return render(request, 'dashboard_medecin.html', {'error': error_message})

    return render(request, 'dashboard_medecin.html')

# Vue pour ajouter un soin
def ajouter_soin(request, nss, nom, prenom):
    """Ajouter un soin à un dossier médical pour un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP contenant les données du formulaire de soin.
        nss (str): Le numéro de sécurité sociale du patient.
        nom (str): Le nom du patient.
        prenom (str): Le prénom du patient.

    Returns:
        HttpResponse: La réponse HTTP redirigeant vers le tableau de bord après ajout ou affichant une erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    headers = get_auth_headers(request)

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}

        try:
            soin_response = requests.post(f"{API_BASE_URL}{nss}/ajouter_soin/", json=data, headers=headers)

            if soin_response.status_code == 201:
                messages.success(request, "Soin ajouté avec succès !")
                return redirect('dashboard')

            elif soin_response.status_code == 404:
                messages.error(request, "Erreur : Ressource introuvable. Vérifiez le NSS.")
            else:
                error_message = soin_response.json().get('error', "Une erreur s'est produite.")
                messages.error(request, f"Erreur lors de l'ajout du soin : {error_message}")

        except requests.RequestException as e:
            messages.error(request, f"Erreur de connexion à l'API : {str(e)}")

        return redirect('ajouter_soin', nss=nss, nom=nom, prenom=prenom)

    return render(request, "ajouter_soin.html", {'nom': nom, 'prenom': prenom})

# Vue pour lister les soins
def lister_soins(request, nss):
    """Lister tous les soins associés à un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP.
        nss (str): Le numéro de sécurité sociale du patient.

    Returns:
        HttpResponse: La réponse HTTP affichant la liste des soins du patient.
    """
    try:
        dossier = DossierMedical.objects.get(patient__nss=nss)
    except DossierMedical.DoesNotExist:
        raise Http404("Dossier médical introuvable")

    soins = dossier.soins.all()
    return render(request, 'soins.html', {'dossier': dossier, 'soins': soins})

# Vue pour ajouter un compte rendu
def ajouter_compte_rendu(request, nss, nom, prenom):
    """Ajouter un compte rendu à un dossier médical pour un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP contenant les données du formulaire de compte rendu.
        nss (str): Le numéro de sécurité sociale du patient.
        nom (str): Le nom du patient.
        prenom (str): Le prénom du patient.

    Returns:
        HttpResponse: La réponse HTTP redirigeant vers le tableau de bord après ajout ou affichant une erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    headers = get_auth_headers(request)

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}

        try:
            compte_rendu_response = requests.post(f"{API_BASE_URL}{nss}/ajouter_compte_rendu/", json=data, headers=headers)

            if compte_rendu_response.status_code == 201:
                messages.success(request, "Compte rendu ajouté avec succès !")
                return redirect('dashboard')

            elif compte_rendu_response.status_code == 404:
                messages.error(request, "Erreur : Ressource introuvable. Vérifiez le NSS.")
            else:
                error_message = compte_rendu_response.json().get('error', "Une erreur s'est produite.")
                messages.error(request, f"Erreur lors de l'ajout du compte rendu : {error_message}")

        except requests.RequestException as e:
            messages.error(request, f"Erreur de connexion à l'API : {str(e)}")

        return redirect('ajouter_compte_rendu', nss=nss, nom=nom, prenom=prenom)

    return render(request, "ajouter_compte_rendu.html", {'nom': nom, 'prenom': prenom})

# Vue pour lister les comptes rendus
def lister_compte_rendus(request, nss):
    """Lister tous les comptes rendus associés à un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP.
        nss (str): Le numéro de sécurité sociale du patient.

    Returns:
        HttpResponse: La réponse HTTP affichant la liste des comptes rendus du patient.
    """
    try:
        dossier = DossierMedical.objects.get(patient__nss=nss)
    except DossierMedical.DoesNotExist:
        raise Http404("Dossier médical introuvable")

    comptes_rendus = dossier.compte_rendus.all()
    return render(request, 'compte_rendus.html', {'dossier': dossier, 'comptes_rendus': comptes_rendus})

# Vue pour rédiger un résumé
def rediger_resume(request, nss):
    """Permet de rédiger un résumé médical pour un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP contenant les données du résumé.
        nss (str): Le numéro de sécurité sociale du patient.

    Returns:
        HttpResponse: La réponse HTTP redirigeant vers la page de recherche DPI ou affichant une erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}
        if nss:
            data['nss'] = nss
        headers = get_auth_headers(request)
        response = requests.post('http://127.0.0.1:8000/api/resume', json=data, headers=headers)

        if response.status_code == 201:
            messages.success(request, "Résumé rédigé avec succès !")
            return redirect(f'/dossier_patient/search_dpi/?nss={nss}')
        else:
            error_message = response.json().get('error', "Une erreur s'est produite.")
            messages.error(request, f"Erreur lors de la rédaction : {error_message}")
            return redirect('rediger_resume')

    return render(request, 'rediger_resume.html')

# Vue pour rédiger un bilan
def rediger_bilan(request, nss):
    """Permet de rédiger un bilan médical pour un patient spécifique.

    Args:
        request (HttpRequest): La requête HTTP contenant les données du bilan.
        nss (str): Le numéro de sécurité sociale du patient.

    Returns:
        HttpResponse: La réponse HTTP redirigeant vers la page de recherche DPI ou affichant une erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}
        if nss:
            data['nss'] = nss
        headers = get_auth_headers(request)
        response = requests.post('http://127.0.0.1:8000/api/bilan', json=data, headers=headers)

        if response.status_code == 201:
            messages.success(request, "Bilan rédigé avec succès !")
            return redirect(f'/dossier_patient/search_dpi/?nss={nss}')
        else:
            error_message = response.json().get('error', "Une erreur s'est produite.")
            messages.error(request, f"Erreur lors de la rédaction du bilan : {error_message}")
            return redirect('rediger_bilan')

    return render(request, 'rediger_bilan.html')

# Vue pour remplir un bilan
def remplir_bilan(request, id_bilan, nom, prenom):
    """Permet de remplir un bilan médical avec des résultats.

    Args:
        request (HttpRequest): La requête HTTP contenant les données du formulaire.
        id_bilan (str): L'identifiant du bilan à remplir.
        nom (str): Le nom du patient.
        prenom (str): Le prénom du patient.

    Returns:
        HttpResponse: La réponse HTTP redirigeant vers le tableau de bord après avoir rempli le bilan ou affichant une erreur.
    """
    if not request.session.get('auth_token'):
        return redirect('login')

    if request.method == "POST":
        form_data = request.POST
        data = {key: value for key, value in form_data.items()}

        headers = get_auth_headers(request)
        try:
            response = requests.post(f"{API_BASE_URL}{id_bilan}/remplir_resultat_bilan/", json=data, headers=headers)

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    messages.success(request, "Bilan rempli avec succès !")
                    return redirect('dashboard')
                except ValueError:
                    messages.error(request, "Erreur : La réponse n'est pas au format JSON.")
                    return redirect('remplir_bilan', id_bilan=id_bilan, nom=nom, prenom=prenom)
            else:
                error_message = response.text
                messages.error(request, f"Erreur lors de la remplir du bilan : {error_message}")
                return redirect('remplir_bilan', id_bilan=id_bilan, nom=nom, prenom=prenom)

        except Exception as e:
            messages.error(request, f"Erreur lors de la requête : {str(e)}")
            return redirect('remplir_bilan', id_bilan=id_bilan)

    return render(request, 'remplir_bilan.html', {'id_bilan': id_bilan, 'nom': nom, 'prenom': prenom})

