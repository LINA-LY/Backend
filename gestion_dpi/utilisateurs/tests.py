from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from .models import Utilisateur, Patient, Ordonnance, Medicament, Medecin
from dossier_patient.models import DossierMedical
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
import jwt, datetime
from datetime import datetime, timedelta


class OrdonnanceCreateTestCase(APITestCase):
    """
    Test case for creating an ordonnance (prescription).
    
    This test case checks various scenarios for creating an ordonnance, including success,
    unauthorized access, and handling invalid user roles (non-medical users).
    """

    def setUp(self):
        """
        Set up test data for the ordonnance creation tests.

        Creates a Medecin (authenticated user), a Patient, and a DossierMedical (patient's record). 
        A JWT token for the Medecin is also generated for authentication in requests.
        """
        self.medecin = Medecin.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="medecin@example.com",
            password="securepassword123"
        )
        self.medecin.set_password("securepassword123")
        self.medecin.save()

        payload = {
            'id': self.medecin.id_utilisateur,
            'exp': datetime.utcnow() + timedelta(days=2),
            'iat': datetime.utcnow()
        }
        key = 'secret'
        self.medecin_token = jwt.encode(payload, key, algorithm='HS256')

        self.patient = Patient.objects.create(
            nom="Smith",
            prenom="Alice",
            email="alice.smith@example.com",
            password="HelloHello",
            date_naissance="2024-12-31",
            nss=20250104
        )
        self.patient.save()

        self.dpi = DossierMedical.objects.create(qr_code=None, patient_id=self.patient.id_utilisateur)
        self.dpi.save()

        self.create_ordonnance_url = reverse('create_ordonnance')

        self.ordonnance_data = {
            'date': datetime.today().date().__str__(),
            "nom_patient": self.patient.nom,
            "prenom_patient": self.patient.prenom,
            "nss": self.patient.nss,
            "medicaments": [
                {
                    "quantite": 3,
                    "description": "Après repas",
                    "duree": "5 jours",
                    "medicament": {
                        "nom": "doliprane",
                        "dosage": "1000mg",
                        "forme": "comprimé"
                    }
                },
            ],
        }

    def test_create_ordonnance_success(self):
        """
        Test successful creation of an ordonnance by an authenticated Medecin.

        The test ensures that the ordonnance is created correctly in the database
        and that a success message is returned.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'{self.medecin_token}')
        response = self.client.post(self.create_ordonnance_url, self.ordonnance_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Ordonnance created successfully")
        self.assertTrue(Ordonnance.objects.filter(
            dpi_patient=self.dpi.id,
            medecin=self.medecin.id_utilisateur
        ).exists())

    def test_create_ordonnance_not_medecin(self):
        """
        Test ordonnance creation by a non-Medecin user.

        This test simulates an attempt to create an ordonnance by a user who is not a Medecin 
        and ensures that a 403 FORBIDDEN status is returned.
        """
        utilisateur = Utilisateur.objects.create(
            nom="NonMedecin",
            prenom="Paul",
            email="nonmedecin@example.com",
            password="password123"
        )
        utilisateur.set_password("password123")
        utilisateur.save()

        payload = {
            'id': utilisateur.id_utilisateur,
            'exp': datetime.utcnow() + timedelta(days=2),
            'iat': datetime.utcnow()
        }
        key = 'secret'
        token = jwt.encode(payload, key, algorithm='HS256')

        self.client.credentials(HTTP_AUTHORIZATION=f'{token}')
        response = self.client.post(self.create_ordonnance_url, self.ordonnance_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_ordonnance_unauthenticated(self):
        """
        Test ordonnance creation without authentication.

        This test ensures that a 403 FORBIDDEN status is returned when no JWT token 
        is provided for authentication.
        """
        response = self.client.post(self.create_ordonnance_url, self.ordonnance_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], "Unauthenticated")


class LoginViewTest(TestCase):
    """
    Test case for user login functionality.
    
    This test case checks successful login with valid credentials and failure with invalid credentials.
    """

    def setUp(self):
        """
        Set up test data for login functionality.

        Creates a user with email and password for login testing.
        """
        self.client = APIClient()
        self.user_data = {
            'nom': 'John',
            'prenom': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'securepassword123',
        }
        self.user = Utilisateur.objects.create(
            email=self.user_data['email'],
            nom=self.user_data['nom'],
            prenom=self.user_data['prenom']
        )
        self.user.set_password(self.user_data['password'])
        self.user.save()
        self.login_url = reverse('login')

    def test_login_success(self):
        """
        Test login with valid credentials.

        This test ensures that the user can log in with valid credentials and receives 
        a token in the response.
        """
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('id', response.data)
        self.assertIn('nom', response.data)

    def test_login_failure_invalid_credentials(self):
        """
        Test login with invalid credentials.

        This test ensures that an incorrect email or password results in a 403 FORBIDDEN 
        status code.
        """
        response = self.client.post(self.login_url, {
            'email': 'wrong.email@example.com',
            'password': 'wrongpassword',
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
