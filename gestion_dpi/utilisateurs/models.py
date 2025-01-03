from django.db import models
from django.contrib.auth.hashers import make_password
from model_utils.managers import InheritanceManager


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
    objects = InheritanceManager()
    def get_user_type(self):
        raise NotImplementedError("Subclasses must implement this method.")

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
    def get_user_type(self):
        """
        Override the method to return 'Medecin' for instances of the Medecin class.
        """
        return 'Medecin'
    def __str__(self):
        return f'Medecin: {self.nom} - {self.prenom}'


class Radiologue(Utilisateur):  # Inherits from Utilisateur
    def get_user_type(self):
        """
        Override the method to return 'Medecin' for instances of the Medecin class.
        """
        return 'Radiologue'
    def __str__(self):
        return f'Radiologue: {self.nom} - {self.prenom}'


class Laborantin(Utilisateur):  # Inherits from Utilisateur
    def get_user_type(self):
        """
        Override the method to return 'Medecin' for instances of the Medecin class.
        """
        return 'Laborantin'
    def __str__(self):
        return f'Laborantin: {self.nom} - {self.prenom}'


class Infirmier(Utilisateur):  # Inherits from Utilisateur
    def get_user_type(self):
        """
        Override the method to return 'Medecin' for instances of the Medecin class.
        """
        return 'Infirmier'
    def __str__(self):
        return f'Infirmier: {self.nom} - {self.prenom}'


class SGPH(Utilisateur):  # Inherits from Utilisateur
    pass  # No additional attributes, extends Utilisateur


class Patient(Utilisateur):
    nss = models.CharField(max_length=50, unique=True)
    date_naissance = models.DateField()
    adresse = models.TextField(default="Adresse inconnue")
    telephone = models.CharField(max_length=15, default="0000000000")
    medecin_traitant = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True)
    # Mutuelle ou assurance, facultatif
    mutuelle = models.CharField(max_length=50, null=True, blank=True)
    personne = models.TextField(default="numero inconnue")
    def get_user_type(self):
        """
        Override the method to return 'Medecin' for instances of the Medecin class.
        """
        return 'Patient'
    def __str__(self):
        return f'Patient: {self.nom} - {self.prenom}'
    




class Resume(models.Model):
    id_resume = models.AutoField(primary_key=True)
    date = models.DateField()  # Date of the resume
    antecedents = models.TextField()  # Summary description
    observations = models.TextField()  # Summary description
    diagnostic = models.TextField()  # Summary description
    dpi = models.ForeignKey(
        'dossier_patient.DossierMedical',
        on_delete=models.CASCADE,
        related_name='resumes',
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
    def __str__(self):
            return f'{self.nom}, {self.dosage}, {self.forme}'

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
        return f'{self.ordonnance.dpi_patient.patient.nom} , {self.medicament.nom}, {self.medicament.dosage}, {self.quantite}'

# Modèle Ordonnance
class Ordonnance(models.Model):
    id_ordonnance = models.AutoField(primary_key=True)  # Identifiant unique pour l'ordonnance
    date = models.DateField()  # Date de l'ordonnance
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE, default=None)  # Relation avec Medecin
    dpi_patient = models.ForeignKey('dossier_patient.DossierMedical', on_delete=models.CASCADE, default=None, related_name='ordonnances')  # Relation avec Patient (Dossier)
    status = models.CharField(max_length=20, default="En attente") #pour la validation de l ordonnance

    def __str__(self):
        return f'Ordonnance {self.dpi_patient.patient} ,{self.medecin} ,{self.date}'


class RapportImagerie(models.Model):
    id_rapport = models.AutoField(primary_key=True)
    description = models.TextField()
    date = models.DateField()
    radiologue = models.ForeignKey(Radiologue, on_delete=models.CASCADE)




class BilanBiologique(models.Model):
    id_bilan = models.AutoField(primary_key=True)
    date = models.DateField()  # Date of the bilan
# Separate fields for glycimie, cholesterol, and pression arterielle
    glycimie = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cholesteroel = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pression_arterielle = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # Optional description
    dpi = models.ForeignKey(
        'dossier_patient.DossierMedical',
        on_delete=models.CASCADE,
        related_name='bilans',
        default=None        # This is done because of modification, should be deleted when first executing the code
    )  # Link to DPI (Dossier Patient Informatisé)
    # Laborantin who worked on this bilan
    laborantin = models.ForeignKey(
        'Laborantin',  # ForeignKey to the Laborantin model
        on_delete=models.SET_NULL,  # If the Laborantin is deleted, set this field to NULL
        null=True,  # The field can be NULL until the Laborantin updates the result
        blank=True,  # Allow blank values when initially created
        related_name='bilans'  # To access the list of bilans filled by this Laborantin
    )
    medecin = models.ForeignKey(
        'Medecin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bilans'
    )  # Laborantin who worked on this bilan    

    def __str__(self):
        return f'Bilan {self.id_bilan} - {self.date}'

