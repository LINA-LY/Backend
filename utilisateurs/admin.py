from django.contrib import admin
from .models import Administratif, Medecin, Radiologue, Laborantin, Infirmier, SGPH, Patient
from django.contrib.auth.hashers import make_password

# Base Admin class for Utilisateur-based models
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email')  # Common fields for all user types
    search_fields = ('nom', 'prenom', 'email')
    exclude = ('is_staff', 'is_superuser')

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not change:
            # Hash the password when creating a new user
            obj.password = make_password(form.cleaned_data['password'])
        elif change and 'password' in form.changed_data:
            # Ensure the password is hashed if updated in the admin interface
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

# Admin for Administratif (is not necessary because we use the predefined admins)
"""@admin.register(Administratif)
class AdministratifAdmin(UtilisateurAdmin):
    def save_model(self, request, obj, form, change):
        # Set default values before saving
        if not obj.pk:  # If this is a new object
            obj.is_staff = True
            obj.is_superuser = False
        if form.cleaned_data.get('password') and not change:
            # Hash the password when creating a new user
            obj.password = make_password(form.cleaned_data['password'])
        elif change and 'password' in form.changed_data:
            # Ensure the password is hashed if updated in the admin interface
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)"""

# Admin for Medecin
@admin.register(Medecin)
class MedecinAdmin(UtilisateurAdmin):
    list_display = UtilisateurAdmin.list_display + ('specialite',)  # Add specialite to display
    list_filter = UtilisateurAdmin.list_filter + ('specialite',)

# Admin for Radiologue
@admin.register(Radiologue)
class RadiologueAdmin(UtilisateurAdmin):
    list_display = UtilisateurAdmin.list_display
    search_fields = UtilisateurAdmin.search_fields
    list_filter = UtilisateurAdmin.list_filter

# Admin for Laborantin
@admin.register(Laborantin)
class LaborantinAdmin(UtilisateurAdmin):
    list_display = UtilisateurAdmin.list_display
    search_fields = UtilisateurAdmin.search_fields
    list_filter = UtilisateurAdmin.list_filter

# Admin for Infirmier
@admin.register(Infirmier)
class InfirmierAdmin(UtilisateurAdmin):
    list_display = UtilisateurAdmin.list_display
    search_fields = UtilisateurAdmin.search_fields
    list_filter = UtilisateurAdmin.list_filter

# Admin for SGPH
@admin.register(SGPH)
class SGPHAdmin(UtilisateurAdmin):
    pass

# Admin for Patient
@admin.register(Patient)
class PatientAdmin(UtilisateurAdmin):
    list_display = UtilisateurAdmin.list_display + ('nss', 'date_naissance', 'telephone', 'mutuelle', 'adresse')
    search_fields = UtilisateurAdmin.search_fields + ('nss',)
    list_filter = UtilisateurAdmin.list_filter + ('mutuelle',)
