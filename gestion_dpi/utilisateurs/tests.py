from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from .models import Utilisateur,Patient, Ordonnance, Medicament
from rest_framework.test import APIClient

class LoginViewTest(TestCase):
    def setUp(self):
        #Créer un utilisateur pour les tests
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
        self.user.set_password(self.user_data['password']) # Hacher le mot de passe 
        self.user.save()
        # Sauvegarder l'utilisateur avec le mot de passe haché
        self.login_url = reverse('login') # Assure-toi que l'URL est correcte
            
            
    def test_login_success(self):
        # Envoyer une requête POST pour se connecter avec des identifiants valides
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
            })
        # Vérifier si le code de statut est 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #Vérifier que la réponse contient le token
        self.assertIn('token', response.data)
        self.assertIn('id', response.data)
        self.assertIn('nom', response.data)
    def test_login_failure_invalid_credentials(self):
        # Envoyer une requête POST avec des identifiants incorrects
        response = self.client.post(self.login_url, {
            'email': 'wrong.email@example.com',
            'password': 'wrongpassword',
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)