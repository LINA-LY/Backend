from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import DossierMedical
from utilisateurs.models import Patient, Laborantin, Infirmier, Radiologue, Medecin, BilanBiologique, Traitement, Ordonnance
from utilisateurs.views import getUserFromToken
from utilisateurs.serializers import BilanBiologiqueSerializer, OrdonnanceSerializer, TraitementSerializer, ResumeSerializer
from .serializers import DossierMedicalSerializer, PatientSerializer, SoinSerializer, CompteRenduSerializer
from rest_framework.decorators import action
import logging
from rest_framework.exceptions import AuthenticationFailed
import requests

class DossierMedicalViewSet(viewsets.ViewSet):
    """
    A viewset for managing Dossier Medical records.
    """

    def list(self, request):
        """
        Retrieve all Dossier Medical records.

        Returns:
            Response: A list of serialized Dossier Medical records.
        """
        queryset = DossierMedical.objects.all()
        serialized_data = DossierMedicalSerializer(queryset, many=True)
        return Response(serialized_data.data)

    def create(self, request):
        """
        Create a new Dossier Medical and its associated Patient record.

        Args:
            request: The HTTP request containing patient data.

        Returns:
            Response: The created patient data and QR code, or an error message.
        """
        user = getUserFromToken(request)
        if not isinstance(user, Medecin):
            return Response({'error': 'Seuls les médecins peuvent créer un dossier médical.'}, status=status.HTTP_403_FORBIDDEN)

        patient_data = {
            'nss': request.data.get('nss'),
            'nom': request.data.get('nom'),
            'prenom': request.data.get('prenom'),
            'date_naissance': request.data.get('date_naissance'),
            'adresse': request.data.get('adresse'),
            'email': request.data.get('email'),
            'telephone': request.data.get('telephone'),
            'mutuelle': request.data.get('mutuelle'),
            'personne': request.data.get('personne'),
        }

        required_fields = ['nss', 'nom', 'prenom', 'date_naissance', 'adresse', 'telephone', 'mutuelle', 'personne', 'email']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'error': f"{field} est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient, created = Patient.objects.get_or_create(nss=patient_data['nss'], defaults=patient_data)
            patient.medecin_traitant = user
            patient.save()

            dossier = DossierMedical.objects.create(patient=patient)

            return Response({
                'patient': PatientSerializer(patient).data,
                'qr_code': dossier.qr_code.url if dossier.qr_code else None,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du patient ou du dossier : {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """
        Retrieve a Dossier Medical by the patient's NSS.

        Args:
            request: The HTTP request.
            pk: The NSS of the patient.

        Returns:
            Response: The serialized Dossier Medical or an error message.
        """
        try:
            patient = Patient.objects.get(nss=pk)
            dossier = DossierMedical.objects.get(patient=patient)
            serialized_data = DossierMedicalSerializer(dossier)
            return Response(serialized_data.data, status=status.HTTP_200_OK)
        
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Medical record not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def lister_dossier_complet(self, request, pk=None):
        """
        Retrieve the complete Dossier Medical for a patient, including associated records.

        Args:
            request: The HTTP request.
            pk: The NSS of the patient.

        Returns:
            Response: A dictionary containing the Dossier Medical and related records.
        """
        try:
            patient = Patient.objects.get(nss=pk)
            user = getUserFromToken(request)

            if isinstance(user, Medecin):
                pass
            elif isinstance(user, Patient):
                if user != patient:
                    return Response({'error': 'Seul le patient peut accéder à son dossier médical.'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Accès non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

            dossier = DossierMedical.objects.get(patient=patient)
            bilans = dossier.bilans.all()
            soins = dossier.soins.all()
            comptes_rendus = dossier.compte_rendus.all()
            ordonnances = dossier.ordonnances.all()
            resumes = dossier.resumes.all()

            dossier_serializer = DossierMedicalSerializer(dossier)
            bilan_serializer = BilanBiologiqueSerializer(bilans, many=True)
            soins_serializer = SoinSerializer(soins, many=True)
            compte_rendu_serializer = CompteRenduSerializer(comptes_rendus, many=True)
            ordonnance_serializer = OrdonnanceSerializer(ordonnances, many=True)
            resumes_serializer = ResumeSerializer(resumes, many=True)

            return Response({
                'dossier': dossier_serializer.data,
                'bilans': bilan_serializer.data,
                'soins': soins_serializer.data,
                'resumes': resumes_serializer.data,
                'comptes_rendus': compte_rendu_serializer.data,
                'ordonnances': ordonnance_serializer.data
            }, status=status.HTTP_200_OK)

        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient introuvable'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def ajouter_soin(self, request, pk=None):
        """
        Add a new soin to a patient's Dossier Medical.

        Args:
            request: The HTTP request containing soin data.
            pk: The NSS of the patient.

        Returns:
            Response: The created soin data or an error message.
        """
        try:
            user = getUserFromToken(request)
        except AuthenticationFailed:
            return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)

        if not isinstance(user, Infirmier):
            return Response({'error': 'Only Infirmiers can add soins.'}, status=status.HTTP_403_FORBIDDEN)

        nss = pk
        if not nss:
            return Response({'error': 'NSS manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SoinSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dossier_medical=dossier, infirmier=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def lister_soins(self, request):
        """
        List all soins for a given patient's NSS.

        Args:
            request: The HTTP request containing the NSS as a query parameter.

        Returns:
            Response: A list of soins or an error message.
        """
        nss = request.query_params.get('nss')
        if not nss:
            return Response({'error': 'NSS manquant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
            soins = dossier.soins.all()
            serializer = SoinSerializer(soins, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def ajouter_compte_rendu(self, request, pk=None):
        """
        Add a new compte rendu to a patient's Dossier Medical.

        Args:
            request: The HTTP request containing compte rendu data.
            pk: The NSS of the patient.

        Returns:
            Response: The created compte rendu data or an error message.
        """
        nss = pk
        if not nss:
            return Response({'error': 'NSS manquant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)

        user = getUserFromToken(request)
        if not isinstance(user, Radiologue):
            return Response({'error': 'Only Radiologues can add compte rendu.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompteRenduSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dossier_medical=dossier, radiologue=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def lister_compte_rendus(self, request):
        """
        List all compte rendus for a given patient's NSS.

        Args:
            request: The HTTP request containing the NSS as a query parameter.

        Returns:
            Response: A list of compte rendus or an error message.
        """
        nss = request.query_params.get('nss')
        if not nss:
            return Response({'error': 'NSS manquant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
            comptes_rendus = dossier.compte_rendus.all()
            serializer = CompteRenduSerializer(comptes_rendus, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remplir_resultat_bilan(self, request, pk=None):
        """
        Fill in the results for a specific Bilan Biologique.

        Args:
            request: The HTTP request containing the results data.
            pk: The ID of the Bilan.

        Returns:
            Response: A success message with updated Bilan data or an error message.
        """
        user = getUserFromToken(request)

        if not isinstance(user, Laborantin):
            return Response({'error': 'Only Laborantin can remplir bilans.'}, status=status.HTTP_403_FORBIDDEN)

        bid = pk
        if not bid:
            return Response({'error': 'Bilan ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bilan = BilanBiologique.objects.get(id_bilan=bid)
        except BilanBiologique.DoesNotExist:
            return Response({'error': 'Bilan not found'}, status=status.HTTP_404_NOT_FOUND)

        if bilan.glycimie or bilan.cholesteroel or bilan.pression_arterielle:
            return Response({'error': 'Results are already filled for this bilan.'}, status=status.HTTP_400_BAD_REQUEST)

        glycimie_data = request.data.get('glycimie')
        cholesteroel_data = request.data.get('cholesteroel')
        pression_arterielle_data = request.data.get('pression_arterielle')

        if not glycimie_data or not pression_arterielle_data or not cholesteroel_data:
            return Response({'error': 'All results data are required.'}, status=status.HTTP_400_BAD_REQUEST)

        bilan.glycimie = glycimie_data
        bilan.cholesteroel = cholesteroel_data
        bilan.pression_arterielle = pression_arterielle_data
        bilan.laborantin = user
        bilan.save()

        return Response({
            "message": "Results updated successfully",
            "bilan_id": bilan.id_bilan,
            "glycimie": glycimie_data,
            "cholesteroel": cholesteroel_data,
            "pression_arterielle": pression_arterielle_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def lister_bilans(self, request):
        """
        List all Bilans Biologiques for a given patient's NSS.

        Args:
            request: The HTTP request containing the NSS as a query parameter.

        Returns:
            Response: A list of Bilans Biologiques or an error message.
        """
        nss = request.query_params.get('nss')
        if not nss:
            return Response({'error': 'NSS manquant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
            bilans = dossier.bilans.all()
            serializer = BilanBiologiqueSerializer(bilans, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)

class OrdonnanceViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing Ordonnances.
    """
    queryset = Ordonnance.objects.all()
    serializer_class = OrdonnanceSerializer

    @action(detail=False, methods=['get'])
    def lister_ordonnances(self, request):
        """
        List all Ordonnances along with their associated Traitements.

        Args:
            request: The HTTP request.

        Returns:
            Response: A list of Ordonnances with their associated Traitements or an error message.
        """
        try:
            ordonnances = Ordonnance.objects.all()

            ordonnances_data = []
            for ordonnance in ordonnances:
                traitements = Traitement.objects.filter(ordonnance=ordonnance)
                traitements_data = TraitementSerializer(traitements, many=True).data

                ordonnance_data = {
                    'id_ordonnance': ordonnance.id_ordonnance,
                    'date': ordonnance.date,
                    'medecin': str(ordonnance.medecin),
                    'dpi_patient': str(ordonnance.dpi_patient),
                    'traitements': traitements_data,
                    'status': ordonnance.status
                }

                ordonnances_data.append(ordonnance_data)

            return Response({
                'ordonnances': ordonnances_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def envoyer_a_sgph(self, request):
        """
        Send Ordonnances data to an external SGPH system.

        Args:
            request: The HTTP request.

        Returns:
            Response: The response from the SGPH system or an error message.
        """
        try:
            response = requests.get("http://localhost:8000/dossier_patient/api/ordonnances/lister_ordonnances")
            if response.status_code != 200:
                return Response({"error": "Failed to fetch ordonnances from lister_ordonnances API."}, status=400)

            ordonnances_data = response.json().get("ordonnances", [])

            sgph_response = {"ordonnances": []}
            for ordonnance in ordonnances_data:
                sgph_response["ordonnances"].append({
                    "id_ordonnance": ordonnance["id_ordonnance"],
                    "status": "Validée" if ordonnance["id_ordonnance"] % 2 == 0 else "Rejetée"
                })

            return Response(sgph_response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
