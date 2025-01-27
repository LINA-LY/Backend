from django.db import models
from django.contrib.auth.hashers import make_password
from model_utils.managers import InheritanceManager

# Create your models here.

class Utilisateur(models.Model):
    """
    Base model for users in the system, with common attributes like name, email, password, and user permissions.

    Attributes:
        id_utilisateur (AutoField): The unique ID for the user.
        nom (CharField): The last name of the user.
        prenom (CharField): The first name of the user.
        password (CharField): The user's password.
        email (EmailField): The email address of the user.
        is_staff (BooleanField): Whether the user has access to the Django admin interface.
        is_superuser (BooleanField): Whether the user has superuser privileges.

    Methods:
        set_password(raw_password): Sets the password for the user.
        set_unusable_password(): Sets the password as unusable.
        get_user_type(): A method to be overridden in subclasses to return the user's type.
    """
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=254, unique=True, default='')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def set_password(self, raw_password):
        """
        Sets the password for the user.

        Args:
            raw_password (str): The raw password to be hashed and set.
        """
        self.password = make_password(raw_password)

    def set_unusable_password(self):
        """
        Sets the password as unusable by setting it to an empty string or placeholder.
        """
        self.password = ""  # Or use some placeholder if needed

    objects = InheritanceManager()

    def get_user_type(self):
        """
        Abstract method to be implemented in subclasses to return the user's type.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class Administratif(Utilisateur):
    """
    Model representing an administrative user, inheriting from Utilisateur with admin privileges.

    Attributes:
        is_staff (BooleanField): Grants access to Django admin interface (True).
        is_superuser (BooleanField): Grants superuser privileges (False).
    
    Methods:
        has_perm(perm, obj=None): Checks if the administrative user has a specific permission.
        has_module_perms(app_label): Checks if the administrative user has access to a specific app.
    """
    is_staff = True
    is_superuser = False

    class Meta:
        verbose_name = "Administratif"
        verbose_name_plural = "Administratifs"

    def has_perm(self, perm, obj=None):
        """
        Checks if the administrative user has a specific permission.
        By default, grants all permissions since they are considered 'admin' by role.

        Args:
            perm (str): The permission to check.
            obj (optional): The object for the permission check.

        Returns:
            bool: True if the user has the permission, otherwise False.
        """
        return True

    def has_module_perms(self, app_label):
        """
        Checks if the administrative user has access to a specific app.
        By default, they have access to all apps.

        Args:
            app_label (str): The label of the app to check.

        Returns:
            bool: True if the user has access to the app, otherwise False.
        """
        return True


class Medecin(Utilisateur):
    """
    Model representing a doctor, inheriting from Utilisateur with additional specialty.

    Attributes:
        specialite (CharField): The specialty of the doctor (default is 'generaliste').

    Methods:
        get_user_type(): Returns the user type as 'Medecin'.
    """
    specialite = models.CharField(max_length=50, default='generaliste')

    def get_user_type(self):
        """
        Returns the user type as 'Medecin'.

        Returns:
            str: The string 'Medecin'.
        """
        return 'Medecin'

    def __str__(self):
        """
        Returns a string representation of the doctor with their name.

        Returns:
            str: The string 'Medecin: {nom} - {prenom}'.
        """
        return f'Medecin: {self.nom} - {self.prenom}'


class Radiologue(Utilisateur):
    """
    Model representing a radiologist, inheriting from Utilisateur.

    Methods:
        get_user_type(): Returns the user type as 'Radiologue'.
    """
    def get_user_type(self):
        """
        Returns the user type as 'Radiologue'.

        Returns:
            str: The string 'Radiologue'.
        """
        return 'Radiologue'

    def __str__(self):
        """
        Returns a string representation of the radiologist with their name.

        Returns:
            str: The string 'Radiologue: {nom} - {prenom}'.
        """
        return f'Radiologue: {self.nom} - {self.prenom}'


class Laborantin(Utilisateur):
    """
    Model representing a lab technician, inheriting from Utilisateur.

    Methods:
        get_user_type(): Returns the user type as 'Laborantin'.
    """
    def get_user_type(self):
        """
        Returns the user type as 'Laborantin'.

        Returns:
            str: The string 'Laborantin'.
        """
        return 'Laborantin'

    def __str__(self):
        """
        Returns a string representation of the lab technician with their name.

        Returns:
            str: The string 'Laborantin: {nom} - {prenom}'.
        """
        return f'Laborantin: {self.nom} - {self.prenom}'


class Infirmier(Utilisateur):
    """
    Model representing a nurse, inheriting from Utilisateur.

    Methods:
        get_user_type(): Returns the user type as 'Infirmier'.
    """
    def get_user_type(self):
        """
        Returns the user type as 'Infirmier'.

        Returns:
            str: The string 'Infirmier'.
        """
        return 'Infirmier'

    def __str__(self):
        """
        Returns a string representation of the nurse with their name.

        Returns:
            str: The string 'Infirmier: {nom} - {prenom}'.
        """
        return f'Infirmier: {self.nom} - {self.prenom}'


class SGPH(Utilisateur):
    """
    Model representing a SGPH user, inheriting from Utilisateur without additional attributes.
    """
    pass


class Patient(Utilisateur):
    """
    Model representing a patient, inheriting from Utilisateur with medical information.

    Attributes:
        nss (CharField): The unique social security number of the patient.
        date_naissance (DateField): The birthdate of the patient.
        adresse (TextField): The address of the patient.
        telephone (CharField): The phone number of the patient.
        medecin_traitant (ForeignKey): The primary doctor of the patient.
        mutuelle (CharField): The patient's health insurance (optional).
        personne (TextField): A contact person for the patient.

    Methods:
        get_user_type(): Returns the user type as 'Patient'.
    """
    nss = models.CharField(max_length=50, unique=True)
    date_naissance = models.DateField()
    adresse = models.TextField(default="Adresse inconnue")
    telephone = models.CharField(max_length=15, default="0000000000")
    medecin_traitant = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True)
    mutuelle = models.CharField(max_length=50, null=True, blank=True)
    personne = models.TextField(default="numero inconnue")

    def get_user_type(self):
        """
        Returns the user type as 'Patient'.

        Returns:
            str: The string 'Patient'.
        """
        return 'Patient'

    def __str__(self):
        """
        Returns a string representation of the patient with their name.

        Returns:
            str: The string 'Patient: {nom} - {prenom}'.
        """
        return f'Patient: {self.nom} - {self.prenom}'


class Resume(models.Model):
    """
    Model representing a summary of a patient's medical history.

    Attributes:
        id_resume (AutoField): The unique ID for the resume.
        date (DateField): The date of the resume.
        antecedents (TextField): Medical history or antecedents of the patient.
        observations (TextField): Observations during the medical consultation.
        diagnostic (TextField): Diagnosis made during the consultation.
        dpi (ForeignKey): Link to the Dossier Medical (DPI).
        medecin (ForeignKey): The doctor who created this resume.

    Methods:
        __str__(): Returns a string representation of the resume with the ID and date.
    """
    id_resume = models.AutoField(primary_key=True)
    date = models.DateField()
    antecedents = models.TextField()
    observations = models.TextField()
    diagnostic = models.TextField()
    dpi = models.ForeignKey(
        'dossier_patient.DossierMedical',
        on_delete=models.CASCADE,
        related_name='resumes',
        default=None
    )
    medecin = models.ForeignKey(
        'Medecin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resumes'
    )

    def __str__(self):
        """
        Returns a string representation of the resume with the ID and date.

        Returns:
            str: The string 'Resume {id_resume} - {date}'.
        """
        return f'Resume {self.id_resume} - {self.date}'


class Medicament(models.Model):
    """
    Model representing a medication prescribed for a treatment.

    Attributes:
        id_medicament (AutoField): The unique ID for the medication.
        nom (CharField): The name of the medication.
        dosage (CharField): The dosage of the medication (e.g., 500mg, 1000mg).
        forme (CharField): The form of the medication (e.g., Tablet, Syrup).

    Methods:
        __str__(): Returns a string representation of the medication with its name, dosage, and form.
    """
    id_medicament = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    forme = models.CharField(max_length=100)

    def __str__(self):
        """
        Returns a string representation of the medication.

        Returns:
            str: The string '{nom}, {dosage}, {forme}'.
        """
        return f'{self.nom}, {self.dosage}, {self.forme}'


class Traitement(models.Model):
    """
    Model representing a treatment prescribed to a patient.

    Attributes:
        id_traitement (AutoField): The unique ID for the treatment.
        medicament (ForeignKey): The medication prescribed in the treatment.
        quantite (IntegerField): The quantity of the medication to take per day.
        description (CharField): The description of when to take the medication.
        duree (CharField): The duration of the treatment.
        ordonnance (ForeignKey): The prescription associated with the treatment.

    Methods:
        __str__(): Returns a string representation of the treatment with medication details.
    """
    id_traitement = models.AutoField(primary_key=True)
    medicament = models.ForeignKey(
        'Medicament',
        on_delete=models.CASCADE,
        default=None
    )
    quantite = models.IntegerField()
    description = models.CharField(max_length=500, default="Après repas")
    duree = models.CharField(max_length=100)
    ordonnance = models.ForeignKey(
        'Ordonnance',
        on_delete=models.CASCADE,
        related_name='medicaments',
        default=None
    )

    def __str__(self):
        """
        Returns a string representation of the treatment with medication details.

        Returns:
            str: The string '{patient.nom}, {medicament.nom}, {medicament.dosage}, {quantite}'.
        """
        return f'{self.ordonnance.dpi_patient.patient.nom} , {self.medicament.nom}, {self.medicament.dosage}, {self.quantite}'


class Ordonnance(models.Model):
    """
    Model representing a prescription given by a doctor.

    Attributes:
        id_ordonnance (AutoField): The unique ID for the prescription.
        date (DateField): The date the prescription was issued.
        medecin (ForeignKey): The doctor who issued the prescription.
        dpi_patient (ForeignKey): The patient's medical record.
        status (CharField): The current status of the prescription.

    Methods:
        __str__(): Returns a string representation of the prescription with patient, doctor, and date details.
    """
    id_ordonnance = models.AutoField(primary_key=True)
    date = models.DateField()
    medecin = models.ForeignKey('Medecin', on_delete=models.CASCADE, default=None)
    dpi_patient = models.ForeignKey('dossier_patient.DossierMedical', on_delete=models.CASCADE, related_name='ordonnances')
    status = models.CharField(max_length=20, default="En attente")

    def __str__(self):
        """
        Returns a string representation of the prescription.

        Returns:
            str: The string 'Ordonnance {dpi_patient.patient}, {medecin}, {date}'.
        """
        return f'Ordonnance {self.dpi_patient.patient} ,{self.medecin} ,{self.date}'


class RapportImagerie(models.Model):
    """
    Model representing an imaging report from a radiologist.

    Attributes:
        id_rapport (AutoField): The unique ID for the imaging report.
        description (TextField): The description of the imaging result.
        date (DateField): The date the imaging report was created.
        radiologue (ForeignKey): The radiologist who issued the report.

    Methods:
        __str__(): Returns a string representation of the imaging report.
    """
    id_rapport = models.AutoField(primary_key=True)
    description = models.TextField()
    date = models.DateField()
    radiologue = models.ForeignKey(Radiologue, on_delete=models.CASCADE)

class BilanBiologique(models.Model):
    """
    Model representing a biological test report for a patient.

    Attributes:
        id_bilan (AutoField): The unique ID for the biological test.
        date (DateField): The date the test was performed.
        description (TextField): The description of the test results.
        medecin (ForeignKey): The doctor who ordered the test.

    Methods:
        __str__(): Returns a string representation of the biological test report.
    """
    id_bilan = models.AutoField(primary_key=True)
    date = models.DateField()
    description = models.TextField()
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    def __str__(self):
        """
        Returns a string representation of the biological test.

        Returns:
            str: The string 'Bilan {id_bilan} - {date}'.
        """
        return f'Bilan {self.id_bilan} - {self.date}'
