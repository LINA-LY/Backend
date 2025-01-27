from rest_framework import serializers
from .models import *

class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer for the Utilisateur model."""
    
    class Meta:
        model = Utilisateur
        fields = ['id_utilisateur', 'nom', 'prenom', 'password', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create a new Utilisateur instance with a hashed password."""
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class AdministratifSerializer(serializers.ModelSerializer):
    """Serializer for the Administratif model."""
    
    class Meta:
        model = Administratif
        fields = ['id_utilisateur', 'nom', 'prenom', 'password', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create a new Administratif instance with a hashed password."""
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class MedecinSerializer(serializers.ModelSerializer):
    """Serializer for the Medecin model."""
    
    class Meta:
        model = Medecin
        fields = ['nom', 'prenom', 'specialite', 'password', 'email']

    def create(self, validated_data):
        """Create a new Medecin instance with a hashed password."""
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        else:
            instance.set_unusable_password()
        instance.save()
        return instance

class PatientSerializer(serializers.ModelSerializer):
    """Serializer for the Patient model."""
    
    medecin_traitant = MedecinSerializer()

    class Meta:
        model = Patient
        fields = ['nss', 'nom', 'prenom', 'date_naissance', 'telephone', 'adresse', 'mutuelle', 'password', 'email', 'medecin_traitant', 'personne']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create a new Patient instance and handle nested Medecin instance."""
        password = validated_data.pop('password', None)
        medecin_traitant_data = validated_data.pop('medecin_traitant', None)
        
        patient = self.Meta.model(**validated_data)

        if medecin_traitant_data:
            medecin_traitant = Medecin.objects.create(**medecin_traitant_data)
            patient.medecin_traitant = medecin_traitant

        patient.save()
        return patient

class MedicamentSerializer(serializers.ModelSerializer):
    """Serializer for the Medicament model."""
    
    class Meta:
        model = Medicament
        fields = ['id_medicament', 'nom', 'dosage', 'forme']

class TraitementSerializer(serializers.ModelSerializer):
    """Serializer for the Traitement model, which includes nested Medicament details."""
    
    medicament = MedicamentSerializer()

    class Meta:
        model = Traitement
        fields = ['id_traitement', 'medicament', 'quantite', 'description', 'duree', 'ordonnance']

    def create(self, validated_data):
        """Create a new Traitement instance, handling nested Medicament data."""
        medicament_data = validated_data.pop('medicament')
        medicament, created = Medicament.objects.get_or_create(**medicament_data)
        traitement = Traitement.objects.create(medicament=medicament, **validated_data)
        return traitement

class OrdonnanceSerializer(serializers.ModelSerializer):
    """Serializer for the Ordonnance model, which includes nested Traitement data."""
    
    medicaments = TraitementSerializer(many=True)

    class Meta:
        model = Ordonnance
        fields = ['id_ordonnance', 'date', 'medecin', 'dpi_patient', 'medicaments', 'status']

    def create(self, validated_data):
        """Create a new Ordonnance instance, processing nested Medicament and Traitement data."""
        medicaments_data = validated_data.pop('medicaments')
        ordonnance = Ordonnance.objects.create(**validated_data)

        for traitement_data in medicaments_data:
            medicament_data = traitement_data.pop('medicament')
            medicament, created = Medicament.objects.get_or_create(**medicament_data)
            Traitement.objects.create(ordonnance=ordonnance, medicament=medicament, **traitement_data)

        return ordonnance

class BilanBiologiqueSerializer(serializers.ModelSerializer):
    """Serializer for the BilanBiologique model."""
    
    class Meta:
        model = BilanBiologique
        fields = ['id_bilan', 'date', 'glycimie', 'cholesteroel', 'pression_arterielle', 'description', 'dpi', 'laborantin', 'medecin']

class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for the Resume model."""
    
    class Meta:
        model = Resume
        fields = ['id_resume', 'date', 'antecedents', 'observations', 'diagnostic', 'dpi', 'medecin']
