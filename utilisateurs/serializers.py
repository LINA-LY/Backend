from rest_framework import serializers
from .models import *

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id_utilisateur', 'nom', 'prenom', 'password', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # Override the creation method to create a hashed password
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance =self.Meta.model(**validated_data)
        if password is not None:
            # set_password is pre-built function to hash password
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class AdministratifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administratif
        fields = ['id_utilisateur', 'nom', 'prenom', 'password', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # Override the creation method to create a hashed password
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance =self.Meta.model(**validated_data)
        if password is not None:
            # set_password is pre-built function to hash password
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class MedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medecin
        fields = ['nom', 'prenom', 'specialite', 'password', 'email']

    # Override the creation method to create a hashed password
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            # set_password is pre-built function to hash password
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance', 'telephone', 'adresse', 'mutuelle', 'password', 'email']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            # set_password is pre-built function to hash password
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance




class MedicamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicament
        fields = ['id_medicament', 'nom', 'dosage', 'forme']

class TraitementSerializer(serializers.ModelSerializer):
    medicament = MedicamentSerializer()  # Nested serializer for medicament details

    class Meta:
        model = Traitement
        fields = ['id_traitement', 'medicament', 'quantite', 'description', 'duree', 'ordonnance']

    def create(self, validated_data):
        medicament_data = validated_data.pop('medicament')
        medicament, created = Medicament.objects.get_or_create(**medicament_data)
        traitement = Traitement.objects.create(medicament=medicament, **validated_data)
        return traitement

class OrdonnanceSerializer(serializers.ModelSerializer):
    medicaments = TraitementSerializer(many=True)  # Nested serializer for related treatments (medicaments)

    class Meta:
        model = Ordonnance
        fields = ['id_ordonnance', 'date', 'medecin', 'dpi_patient', 'medicaments']

    def create(self, validated_data):
        # Extract nested medicaments data
        medicaments_data = validated_data.pop('medicaments')

        # Create the Ordonnance instance
        ordonnance = Ordonnance.objects.create(**validated_data)

        # Process each medicament in the nested data
        for traitement_data in medicaments_data:
            medicament_data = traitement_data.pop('medicament')  # Extract the nested Medicament data

            # Either retrieve or create the Medicament instance
            medicament, created = Medicament.objects.get_or_create(**medicament_data)

            # Create the Traitement instance and associate it with the ordonnance
            Traitement.objects.create(ordonnance=ordonnance, medicament=medicament, **traitement_data)

        return ordonnance


class BilanBiologiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BilanBiologique
        fields = ['id_bilan', 'date', 'result', 'description', 'dpi', 'laborantin']


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id_resume', 'date', 'description', 'dpi', 'medecin']


class DossierMedicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierMedical
        fields = ['id_dpi', 'patient', 'consultations', 'soins', 'images', 'bilans']