# urls.py

# Importation des modules nécessaires
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import DossierMedicalViewSet,OrdonnanceViewSet

# Création d'un routeur pour gérer les routes de l'API
router = DefaultRouter()

# Enregistrement de la route 'dossier-medical' pour l'API
router.register(r'dossier-medical', DossierMedicalViewSet, basename='dossier-medical')
router.register(r'ordonnances', OrdonnanceViewSet, basename='ordonnance')
# Définition des routes classiques et API
urlpatterns = [
    
    
    path('login/', views.login, name='login'),  # This is the route to the login page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    # Route pour créer un DPI
    
    path('', views.create_dpi, name='create_dpi'),
    
    # Route pour afficher un DPI selon le NSS
    path('dpi/<str:nss>/', views.view_dpi, name='view_dpi'),
    
    # Route pour rechercher un DPI
    path('search_dpi/', views.search_dpi, name='search_dpi'),  # <-- This remains as is

    path('ajouter_soin/<str:nss>/<str:nom>/<str:prenom>/', views.ajouter_soin, name='ajouter_soin'),

    path('lister_soins/<str:nss>/', views.lister_soins, name='lister_soins'),

    path('ajouter_compte_rendu/<str:nss>/<str:nom>/<str:prenom>/', views.ajouter_compte_rendu, name='ajouter_compte_rendu'),
    path('lister_comptes_rendus/<str:nss>/', views.lister_compte_rendus, name='lister_compte_rendus'),

    path('rediger_resume/<str:nss>/', views.rediger_resume, name='rediger_resume'),
    path('rediger_bilan/<str:nss>/', views.rediger_bilan, name='rediger_bilan'),
    
    path('remplir_bilan/<int:id_bilan>/<str:nom>/<str:prenom>/', views.remplir_bilan, name='remplir_bilan'),
    # Route pour l'API qui inclut toutes les routes générées automatiquement
    path('api/', include(router.urls)),
]
