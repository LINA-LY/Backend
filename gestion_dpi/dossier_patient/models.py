from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File

class Soin(models.Model):
    """Représente un soin réalisé pour un patient.

    Attributes:
        id (int): Identifiant unique pour chaque soin.
        date (date): Date à laquelle le soin a été effectué.
        medicaments_administres (str): Description des médicaments administrés.
        soins_infirmiers (str): Description des soins infirmiers effectués.
        observations (str): Observations effectuées pendant le soin.
        infirmier (ForeignKey): Référence à l'infirmier ayant effectué le soin.
        dossier_medical (ForeignKey): Référence au dossier médical auquel le soin appartient.
    """
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    medicaments_administres = models.TextField()
    soins_infirmiers = models.TextField()
    observations = models.TextField()
    infirmier = models.ForeignKey(
        'utilisateurs.Infirmier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soins'
    )
    dossier_medical = models.ForeignKey(
        'DossierMedical',
        on_delete=models.CASCADE,
        related_name='soins'
    )

    def __str__(self):
        """Retourne une représentation textuelle du soin."""
        return f"Soin ID: {self.id}, Date: {self.date}, Infirmier: {self.infirmier}"


class CompteRendu(models.Model):
    """Représente un compte rendu médical pour un patient.

    Attributes:
        id (int): Identifiant unique pour chaque compte rendu.
        dossier_medical (ForeignKey): Référence au dossier médical lié au compte rendu.
        date (date): Date du compte rendu.
        radiologue (ForeignKey): Référence au radiologue ayant réalisé le compte rendu.
        description (str): Description du compte rendu.
        image_radio (ImageField): Image associée au compte rendu, comme une radiographie.
    """
    id = models.AutoField(primary_key=True)
    dossier_medical = models.ForeignKey(
        'DossierMedical',
        on_delete=models.CASCADE,
        related_name='compte_rendus'
    )
    date = models.DateField()
    radiologue = models.ForeignKey(
        'utilisateurs.Radiologue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compte_rendus'
    )
    description = models.TextField()
    image_radio = models.ImageField(upload_to='radio_images/', null=True, blank=True)

    def __str__(self):
        """Retourne une représentation textuelle du compte rendu."""
        return f"Compte rendu ID: {self.id}, Date: {self.date}, Radiologue: {self.radiologue}"


class DossierMedical(models.Model):
    """Représente le dossier médical d'un patient.

    Attributes:
        patient (OneToOneField): Référence au patient propriétaire du dossier médical.
        qr_code (ImageField): Image du QR Code associée au patient, générée automatiquement.
    """
    patient = models.OneToOneField(
        "utilisateurs.Patient",
        on_delete=models.CASCADE,
        related_name="dossier_medical",
    )
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        """Génère un QR Code basé sur le NSS du patient avant d'enregistrer l'instance."""
        if self.patient and self.patient.nss:
            qr_img = qrcode.make(self.patient.nss)
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            self.qr_code.save(f'{self.patient.nss}_qr.png', File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        """Retourne une représentation textuelle du dossier médical."""
        return f"{self.patient.nom} {self.patient.prenom} - {self.patient.nss}"
