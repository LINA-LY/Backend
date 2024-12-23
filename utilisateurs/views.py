from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from .serializers import *
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import AuthenticationFailed
from .models import *
import jwt, datetime
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from django.contrib.auth.hashers import check_password



def auth(request):
    token = request.headers['Authorization']
    if not token:
        raise AuthenticationFailed("Unauthenticated")
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256']) #RS256
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Unauthenticated, expired token")
    except jwt.DecodeError:
        raise AuthenticationFailed("Unauthenticated, invalid token")
    return True
def getUserFromToken(request, type=5):
    token = request.headers['Authorization']
    if not token:
        raise AuthenticationFailed("Unauthenticated")
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256']) #RS256
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Unauthenticated, expired token")
    except jwt.DecodeError:
        raise AuthenticationFailed("Unauthenticated, invalid token")
    match type:
        case 0:
            user = Administratif.objects.get(id_utilisateur=payload['id'])
        case 1:
            user = Medecin.objects.get(id_utilisateur=payload['id'])
        case 2:
            user = Radiologue.objects.get(id_utilisateur=payload['id'])
        case 3:
            user = Laborantin.objects.get(id_utilisateur=payload['id'])
        case 4:
            user = Infirmier.objects.get(id_utilisateur=payload['id'])
        case _:
            user = Utilisateur.objects.get(id_utilisateur=payload['id'])
    return user

# Create your views here.

# To register (add new user) -- classic jwt method
"""class RegisterView(APIView):

    def post(self, request):

        user = getUserFromToken(request)
        if user.is_staff == 0:
            raise AuthenticationFailed("Don't have the rights !!")
        # Verify also that the connected user is an instance from Administrative class using the token

        print("He's an admin")

        # On peut imaginer dans la requête le type de l'utilisateur en question
        # et selon ce type, on instancie la classe correspondante

        email = request.data['email']
        password = request.data['password']
        type = request.data['type']
        # 0: admin / 1: medecin / 2: Radiologue / 3: Laborantin / 4: Infirmier / autre: Erreur

        print(email, password)

        match type:
            case 0:
                user = Administratif.objects.filter(email=email).first()
            case 1:
                user = Medecin.objects.filter(email=email).first()
            case 2:
                user = Radiologue.objects.filter(email=email).first()
            case 3:
                user = Laborantin.objects.filter(email=email).first()
            case 4:
                user = Infirmier.objects.filter(email=email).first()
            case _:
                raise TypeError("Incorrect user type")


        if user is not None:
            raise AuthenticationFailed('User already signed up')
        data = request.data

        match type:
            case 0:
                serializer = AdministratifSerializer(data=data)  # NOTE: AdministratifSerializer
            case 1:
                serializer = MedecinSerializer(data=data)
            case 2:
                serializer = UtilisateurSerializer(data=data)  # NOTE: RadiologueSerializer
            case 3:
                serializer = UtilisateurSerializer(data=data)  # NOTE: LaborantinSerializer
            case 4:
                serializer = UtilisateurSerializer(data=data)  # NOTE: InfirmierSerializer
            case _:
                raise TypeError("Incorrect user type")
        if serializer.is_valid():
            serializer.save()
            # user = serializer.data.copy()

            response = Response()

            response.data = {
                "message": "User created successfully"
            }
            response.status_code = 201
            return response
            #return Response(serializer.data, status=201)
        return Response(serializer.errors)
"""

# To login (sign in) -- classic jwt method
class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        print(email, password)


        user = Utilisateur.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed('User not found')
        if not check_password(password, user.password):
            raise AuthenticationFailed('Incorrect password')

        payload = {
            'id': user.id_utilisateur,
            'exp': datetime.utcnow() + timedelta(days=2),
            'iat': datetime.utcnow()
        }
        key = 'secret'
        token = jwt.encode(payload, 'secret', algorithm='HS256')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            "token": token,
            "id": user.id_utilisateur,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
        }
        return response


@api_view(['POST'])
def rediger_ordonnance(request):

    medecin = getUserFromToken(request, 1)
    if not medecin:
        raise AuthenticationFailed("This Medecin does not exist !!")

    patient_nss = request.data['nss']
    patient = Patient.objects.filter(nss=patient_nss).first()
    if not patient:
        raise AuthenticationFailed("Patient does not exist, you need to add it first")
    # print(patient.__str__())

    dpi = DossierMedical.objects.filter(patient=patient.id_utilisateur).first()
    if not dpi:
        raise AuthenticationFailed("DPI for this patient does not exist, you need to add it first")
    # print(dpi.__str__())

    date = request.data['date']
    medicaments = request.data['medicaments']

    data = {
        "date": date,
        "medecin": medecin.id_utilisateur,
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
        "medecin": medecin.nom,
        "medicaments": medicaments
    }
    response.status_code = 201
    return response
    # return Response(serializer.data, status=201)

@api_view(['POST'])
def rediger_resume(request):
    medecin = getUserFromToken(request, 1)
    if medecin is None:
        raise AuthenticationFailed("This Medecin does not exist !!")

    patient_nss = request.data['nss']
    patient = Patient.objects.filter(nss=patient_nss).first()
    if not patient:
        raise AuthenticationFailed("Patient does not exist, you need to add it first")

    dpi = DossierMedical.objects.filter(patient=patient.id_utilisateur).first()
    if not dpi:
        raise AuthenticationFailed("DPI for this patient does not exist, you need to add it first")

    data = {
        "date": request.data['date'],
        "description": request.data['description'],
        "dpi": dpi.id,
        "medecin": medecin.id_utilisateur
    }
    serializer = ResumeSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        response = Response()

        response.data = {
            "message": "Resume created successfully",
            "medecin": medecin.nom,
            "description": data['description']
        }
        response.status_code = 201
        return response
    return Response(serializer.errors)

@api_view(['POST'])
def rediger_bilan(request):
    medecin = getUserFromToken(request, 1)
    if medecin is None:
        raise AuthenticationFailed("This Medecin does not exist !!")

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
        "medecin": laborantin.id_utilisateur,
        "result": request.data['result'],
    }

    serializer = BilanBiologiqueSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        response = Response()

        response.data = {
            "message": "Bilan created successfully",
            "result": data['result'],
            "description": data['description'],
        }
        response.status_code = 201
        return response
    return Response(serializer.errors)