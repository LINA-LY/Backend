from django.db import models
from django.contrib.auth.hashers import make_password
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Utilisateur(models.Model):
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=254, unique=True, default='')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def set_unusable_password(self):
        self.password = ""  # Or use some placeholder if needed


class Administratif(Utilisateur):  # Inherits from Utilisateur + has admin advantages as predefined for django using the following attributes
    is_staff = True  # Grants access to Django admin interface
    is_superuser = False  # Optionally, give superuser privileges

    class Meta:
        verbose_name = "Administratif"
        verbose_name_plural = "Administratifs"

    def has_perm(self, perm, obj=None):
        """
        Define whether the administratif user has a specific permission.
        By default, we'll grant all permissions since they are 'admin' by role.
        """
        return True

    def has_module_perms(self, app_label):
        """
        Define whether the administratif user has permissions to view a specific app.
        By default, they have access to all apps.
        """
        return True

class Medecin(Utilisateur):  # Inherits from Utilisateur
    specialite = models.CharField(max_length=50, default='generaliste')

    def __str__(self):
        return f'Medecin: {self.nom} - {self.prenom}'


class Radiologue(Utilisateur):  # Inherits from Utilisateur
    pass  # No additional attributes, extends Utilisateur


class Laborantin(Utilisateur):  # Inherits from Utilisateur
    pass  # No additional attributes, extends Utilisateur


class Infirmier(Utilisateur):  # Inherits from Utilisateur
    pass  # No additional attributes, extends Utilisateur


class SGPH(Utilisateur):  # Inherits from Utilisateur
    pass  # No additional attributes, extends Utilisateur


class Patient(Utilisateur):
    nss = models.CharField(max_length=50, unique=True)
    date_naissance = models.DateField()
    adresse = models.TextField(default="Adresse inconnue")
    telephone = models.CharField(max_length=15, default="0000000000")
    # medecin_traitant = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True)
    # Mutuelle ou assurance, facultatif
    mutuelle = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f'Patient: {self.nom} - {self.prenom}'


class Resume(models.Model):
    id_resume = models.AutoField(primary_key=True)
    date = models.DateField()  # Date of the resume
    description = models.TextField()  # Summary description
    dpi = models.ForeignKey(
        'DossierMedical',
        on_delete=models.CASCADE,
        related_name='consultations',
        default=None        # This is done because of modification, should be deleted when first executing the code
    )  # Link to DPI (Dossier Patient Informatisé)
    medecin = models.ForeignKey(
        'Medecin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resumes'
    )  # Medecin who wrote this resume

    def __str__(self):
        return f'Resume {self.id_resume} - {self.date}'



"""class Ordonnance(models.Model):
    id_ordonnance = models.AutoField(primary_key=True)
    date = models.DateField()
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    infirmiers = models.ManyToManyField(Infirmier)"""

class Medicament(models.Model):
    id_medicament = models.AutoField(primary_key=True, default=None)   # This is done because of modification, should be deleted when first executing the code
    nom = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)  # Exemple : 500mg, 1000mg
    forme = models.CharField(max_length=100)  # Exemple : Comprimé, Sirop

class Traitement(models.Model):
    id_traitement = models.AutoField(primary_key=True, default=None)  # default=None is done because of modification, should be deleted when first executing the code
    medicament = models.ForeignKey(
        'Medicament',
        on_delete=models.CASCADE,
        default=None         # default=None is done because of modification, should be deleted when first executing the code
    )
    quantite = models.IntegerField()  # Quantité à prendre / jour
    description = models.CharField(max_length=500, default="Après repas")  # Quand prendre les médicaments...
    duree = models.CharField(max_length=100)  # Durée en jours ou mois, peut être changé en IntegerField
    ordonnance = models.ForeignKey(
        'Ordonnance',
        on_delete=models.CASCADE,  # Delete all associated médicaments if ordonnance is deleted
        related_name='medicaments', # Access the médicaments via ordonnance.medicaments
        default=None                # This is done because of modification, should be deleted when first executing the code
    )

    def __str__(self):
        return f'{self.nom} ({self.dosage}, {self.forme})'

# Modèle Ordonnance
class Ordonnance(models.Model):
    id_ordonnance = models.AutoField(primary_key=True)  # Identifiant unique pour l'ordonnance
    date = models.DateField()  # Date de l'ordonnance
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE, default=None)  # Relation avec Medecin
    dpi_patient = models.ForeignKey('DossierMedical', on_delete=models.CASCADE, default=None, related_name='ordonnances')  # Relation avec Patient (Dossier)

    def __str__(self):
        return f'Ordonnance {self.id_ordonnance} - {self.date}'


class RapportImagerie(models.Model):
    id_rapport = models.AutoField(primary_key=True)
    description = models.TextField()
    date = models.DateField()
    radiologue = models.ForeignKey(Radiologue, on_delete=models.CASCADE)


class Soin(models.Model):
    id_soin = models.AutoField(primary_key=True)
    date = models.DateField()
    infirmier = models.ForeignKey(Infirmier, on_delete=models.CASCADE)


class BilanBiologique(models.Model):
    id_bilan = models.AutoField(primary_key=True)
    date = models.DateField()  # Date of the bilan
    result = models.TextField(default='')  # Results of the biological exam
    description = models.TextField(blank=True, null=True)  # Optional description
    dpi = models.ForeignKey(
        'DossierMedical',
        on_delete=models.CASCADE,
        related_name='bilans',
        default=None        # This is done because of modification, should be deleted when first executing the code
    )  # Link to DPI (Dossier Patient Informatisé)
    laborantin = models.ForeignKey(
        'Laborantin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bilans'
    )  # Laborantin who worked on this bilan

    def __str__(self):
        return f'Bilan {self.id_bilan} - {self.date}'



"""class DPI(models.Model):  # Dossier Patient Informatisé
    id_dpi = models.AutoField(primary_key=True)
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    consultations = models.ManyToManyField(Resume, blank=True)
    soins = models.ManyToManyField(Soin, blank=True)
    # ordonnances = models.ManyToManyField(Ordonnance, blank=True)
    images = models.ManyToManyField(RapportImagerie, blank=True)
    bilans = models.ManyToManyField(BilanBiologique, blank=True)"""


# Modèle pour représenter les dossiers médicaux liés à un patient
class DossierMedical(models.Model):
    # Référence au modèle Patient
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="dossier_medical",
        default=1  # ID du patient par défaut
    )

    # Champ pour le QR Code, facultatif
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    # Méthode pour sauvegarder le modèle
    def save(self, *args, **kwargs):
        # Générer un QR Code basé sur le NSS
        qr_img = qrcode.make(self.patient.nss)
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')  # Enregistrer le QR Code au format PNG
        buffer.seek(0)  # Réinitialiser le pointeur du buffer
        self.qr_code.save(f'{self.patient.nss}_qr.png', File(buffer),
                          save=False)  # Associer le fichier au champ qr_code
        super().save(*args, **kwargs)  # Appeler la méthode save() originale

    # Méthode pour afficher le modèle comme une chaîne lisible
    def __str__(self):
        return f"{self.patient.nom} {self.patient.prenom} - {self.patient.nss}"
