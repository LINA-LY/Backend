from rest_framework import serializers
from .models import DossierMedical, Soin, CompteRendu
from utilisateurs.serializers import PatientSerializer, UtilisateurSerializer  # Import du serializer Patient


class SoinSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Soin.

    Attributes:
        infirmier (UtilisateurSerializer): Infirmier associé au soin, en lecture seule.
        Meta (class): Classe contenant les métadonnées du serializer, comme le modèle et les champs.
    """

    infirmier = UtilisateurSerializer(read_only=True)

    class Meta:
        """Métadonnées pour le serializer Soin."""
        model = Soin
        fields = ['id', 'date', 'medicaments_administres', 'soins_infirmiers', 'observations', 'infirmier']

    def create(self, validated_data):
        """Crée une instance de Soin.

        Args:
            validated_data (dict): Données validées pour la création du soin.

        Returns:
            Soin: Instance créée du modèle Soin.
        """
        soin = Soin.objects.create(**validated_data)
        return soin


class CompteRenduSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle CompteRendu.

    Attributes:
        radiologue (UtilisateurSerializer): Radiologue associé au compte rendu, en lecture seule.
        Meta (class): Classe contenant les métadonnées du serializer, comme le modèle et les champs.
    """

    radiologue = UtilisateurSerializer(read_only=True)

    class Meta:
        """Métadonnées pour le serializer CompteRendu."""
        model = CompteRendu
        fields = ['id', 'date', 'radiologue', 'description', 'image_radio']

    def create(self, validated_data):
        """Crée une instance de CompteRendu.

        Args:
            validated_data (dict): Données validées pour la création du compte rendu.

        Returns:
            CompteRendu: Instance créée du modèle CompteRendu.
        """
        compteRendu = CompteRendu.objects.create(**validated_data)
        return compteRendu


class DossierMedicalSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle DossierMedical.

    Attributes:
        patient (PatientSerializer): Serializer pour le patient associé au dossier médical.
        Meta (class): Classe contenant les métadonnées du serializer, comme le modèle et les champs.
    """

    patient = PatientSerializer()

    class Meta:
        """Métadonnées pour le serializer DossierMedical."""
        model = DossierMedical
        fields = ['patient', 'qr_code']
