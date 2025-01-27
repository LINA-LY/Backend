from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
import os
from .serializers import *
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import AuthenticationFailed
from .models import *
import jwt, datetime
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from django.contrib.auth.hashers import check_password
from dossier_patient.models import DossierMedical
from rest_framework import status

def auth(request):
    """
    Authenticate the user based on the JWT token provided in the request headers.

    Args:
        request (HttpRequest): The incoming request containing the authorization token.

    Returns:
        dict: Decoded payload of the JWT token if authentication is successful.

    Raises:
        AuthenticationFailed: If the token is missing, has an incorrect format, is expired, or is invalid.
    """
    token = request.headers.get('Authorization')
    
    if not token:
        raise AuthenticationFailed("Unauthenticated, missing token")

    if not token.startswith('Bearer '):
        raise AuthenticationFailed("Invalid token format, 'Bearer ' prefix missing")

    token = token.split(' ')[1]

    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise AuthenticationFailed("Server misconfiguration, missing secret key")
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"Decoded payload: {payload}")  # Debugging line
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Unauthenticated, expired token")
    except jwt.DecodeError:
        raise AuthenticationFailed("Unauthenticated, invalid token")

def getUserFromToken(request, type=None):
    """
    Extract the user from the JWT token in the request and return the user object.

    Args:
        request (HttpRequest): The incoming request containing the authorization token.
        type (str, optional): Type of user to fetch based on the decoded token.

    Returns:
        User: A user object based on the decoded token's user type and ID.

    Raises:
        AuthenticationFailed: If the token is invalid or does not contain required fields.
    """
    try:
        print("Inside getUserFromToken function")

        token = request.headers.get('Authorization')
        if not token:
            raise AuthenticationFailed("Unauthenticated, missing token")

        if not token.startswith("Bearer "):
            raise AuthenticationFailed("Invalid token format, 'Bearer ' prefix missing")
        token = token.split(' ')[1]

        secret_key = os.getenv('SECRET_KEY')
        if not secret_key:
            raise AuthenticationFailed("Server misconfiguration, missing secret key")

        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"Decoded token payload: {payload}")

        if 'id' not in payload or 'type' not in payload:
            raise AuthenticationFailed("Token payload is missing required fields ('id' or 'type')")

        user = None
        user_type = payload.get('type')
        user_id = payload.get('id')

        print(f"User ID: {user_id}, User Type: {user_type}")

        if user_type == 'Medecin':
            print("Fetching Medecin object...")
            user = Medecin.objects.filter(id_utilisateur=user_id).first()
        elif user_type == 'Radiologue':
            print("Fetching Radiologue object...")
            user = Radiologue.objects.filter(id_utilisateur=user_id).first()
        elif user_type == 'Infirmier':
            print("Fetching Infirmier object...")
            user = Infirmier.objects.filter(id_utilisateur=user_id).first()
        elif user_type == 'Laborantin':
            print("Fetching Laborantin object...")
            user = Laborantin.objects.filter(id_utilisateur=user_id).first()
        elif user_type == 'Patient':
            print("Fetching Patient object...")
            user = Patient.objects.filter(id_utilisateur=user_id).first()
        elif user_type == 'Utilisateur':
            print("Fetching Utilisateur object...")
            user = Utilisateur.objects.filter(id_utilisateur=user_id).first()

    except Exception as e:
        print(f"Error encountered: {str(e)}")
        raise AuthenticationFailed(f"An error occurred during authentication: {str(e)}")

    return user

class LoginView(APIView):
    """
    View for user login, authenticates the user and generates a JWT token.

    Args:
        request (HttpRequest): The incoming request containing the user's email and password.

    Returns:
        Response: A response containing the JWT token and user details if authentication is successful.

    Raises:
        AuthenticationFailed: If the email or password is incorrect.
    """
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        print(f"Attempting to log in with email: {email}")

        try:
            user = Utilisateur.objects.select_subclasses().filter(email=email).first()
            if user is None:
                raise AuthenticationFailed('User not found')
        except Exception as e:
            print(f"Error fetching user: {e}")
            raise AuthenticationFailed(f"Error fetching user: {e}")

        try:
            if not check_password(password, user.password):
                raise AuthenticationFailed('Incorrect password')
        except Exception as e:
            print(f"Error verifying password: {e}")
            raise AuthenticationFailed(f"Error verifying password: {e}")

        try:
            payload = {
                'id': user.id_utilisateur,
                'type': user.get_user_type(),
                'exp': datetime.utcnow() + timedelta(days=2),
                'iat': datetime.utcnow()
            }

            print(f"Token payload: {payload}")

            token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
            print(f"Generated token: {token}")
        except Exception as e:
            print(f"Error generating token: {e}")
            raise AuthenticationFailed(f"Error generating token: {e}")

        try:
            response = Response()
            response.set_cookie(key='jwt', value=token, httponly=True)
            response.data = {
                "token": token,
                "id": user.id_utilisateur,
                "nom": user.nom,
                "prenom": user.prenom,
                "email": user.email,
                "role": user.get_user_type(),
            }
            return response
        except Exception as e:
            print(f"Error preparing response: {e}")
            raise AuthenticationFailed(f"Error preparing response: {e}")

@api_view(['POST'])
def rediger_ordonnance(request):
    """
    Create an ordonnance for a patient by a Medecin.

    Args:
        request (HttpRequest): The incoming request containing ordonnance data.

    Returns:
        Response: A response indicating the success or failure of creating the ordonnance.

    Raises:
        AuthenticationFailed: If the user is not a Medecin or if the patient or DPI is missing.
    """
    user = getUserFromToken(request)
    if not isinstance(user, Medecin):
        return Response({'error': 'Only Medecins can add compte rendu.'}, status=status.HTTP_403_FORBIDDEN)

    patient_nss = request.data['nss']
    patient = Patient.objects.filter(nss=patient_nss).first()
    if not patient:
        raise AuthenticationFailed("Patient does not exist, you need to add it first")

    dpi = DossierMedical.objects.filter(patient=patient.id_utilisateur).first()
    if not dpi:
        raise AuthenticationFailed("DPI for this patient does not exist, you need to add it first")

    date = request.data['date']
    medicaments = request.data['medicaments']

    data = {
        "date": date,
        "medecin": user.id_utilisateur,
        "dpi_patient": dpi.id,
        "medicaments": medicaments
    }

    serializer = OrdonnanceSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors)
    serializer.save()

    response = Response()
    response.data = {
        "message": "Ordonnance created successfully",
        "medecin": user.nom,
        "medicaments": medicaments
    }
    response.status_code = 201
    return response

@api_view(['POST'])
def rediger_resume(request):
    """
    Create a resume for a patient by a Medecin.

    Args:
        request (HttpRequest): The incoming request containing resume data.

    Returns:
        Response: A response indicating the success or failure of creating the resume.

    Raises:
        AuthenticationFailed: If the user is not a Medecin or if the patient or DPI is missing.
    """
    user = getUserFromToken(request)
    if not isinstance(user, Medecin):
        return Response({'error': 'Only Medecins can add compte rendu.'}, status=status.HTTP_403_FORBIDDEN)

    patient_nss = request.data['nss']
    patient = Patient.objects.filter(nss=patient_nss).first()
    if not patient:
        raise AuthenticationFailed("Patient does not exist, you need to add it first")

    dpi = DossierMedical.objects.filter(patient=patient.id_utilisateur).first()
    if not dpi:
        raise AuthenticationFailed("DPI for this patient does not exist, you need to add it first")

    data = {
        "date": request.data['date'],
        "observations": request.data['observations'],
        "diagnostic": request.data['diagnostic'],
        "antecedents": request.data['antecedents'],
        "dpi": dpi.id,
        "medecin": user.id_utilisateur
    }
    serializer = ResumeSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        response = Response()

        response.data = {
            "message": "Resume created successfully",
            "medecin": user.nom
        }
        response.status_code = 201
        return response
    return Response(serializer.errors)

@api_view(['POST'])
def rediger_bilan(request):
    """
    Create a bilan for a patient by a Medecin.

    Args:
        request (HttpRequest): The incoming request containing bilan data.

    Returns:
        Response: A response indicating the success or failure of creating the bilan.

    Raises:
        AuthenticationFailed: If the user is not a Medecin or if the patient or DPI is missing.
    """
    user = getUserFromToken(request)
    if not isinstance(user, Medecin):
        return Response({'error': 'Only Medecins can add compte rendu.'}, status=status.HTTP_403_FORBIDDEN)

    patient_nss = request.data['nss']
    patient = Patient.objects.get(nss=patient_nss)
    if not patient:
        raise AuthenticationFailed("Patient does not exist, you need to add it first")

    dpi = DossierMedical.objects.get(patient=patient.id_utilisateur)
    if not dpi:
        raise AuthenticationFailed("DPI for this patient does not exist, you need to add it first")

    data = {
        "date": request.data['date'],
        "description": request.data['description'],
        "dpi": dpi.id,
        "medecin": user.id_utilisateur
    }

    serializer = BilanBiologiqueSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        response = Response()

        response.data = {
            "message": "Bilan created successfully",
            "description": data['description'],
        }
        response.status_code = 201
        return response
    return Response(serializer.errors)


@api_view(['GET'])
def get_nss_by_id(request, patient_id):
    """
    Retrieve the National Social Security (NSS) number of a patient by their ID.

    Args:
        request (HttpRequest): The incoming request to retrieve the patient's NSS.
        patient_id (int): The unique identifier of the patient.

    Returns:
        Response: A Response object containing the patient's NSS number if found, or an error message if not found.
        
        If the patient is found, returns the NSS in the format:
            {"nss": "<NSS number>"}
        
        If the patient is not found, returns:
            {"error": "Patient not found."}
        
        In case of other exceptions, returns:
            {"error": "<exception message>"}

    Raises:
        Patient.DoesNotExist: If no patient with the given ID exists in the database.
        Exception: For any other errors that might occur during the process.
    """
    try:
        patient = Patient.objects.get(id_utilisateur=patient_id)  # Get patient by ID
        return Response({"nss": patient.nss}, status=status.HTTP_200_OK)
    except Patient.DoesNotExist:
        return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
