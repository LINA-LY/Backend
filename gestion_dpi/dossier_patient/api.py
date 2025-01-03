from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import DossierMedical
from utilisateurs.models import Patient,Laborantin, Infirmier, Radiologue, Medecin, BilanBiologique, Traitement, Ordonnance
from utilisateurs.views import getUserFromToken
from utilisateurs.serializers import BilanBiologiqueSerializer, OrdonnanceSerializer, TraitementSerializer,ResumeSerializer
from .serializers import DossierMedicalSerializer, PatientSerializer, SoinSerializer, CompteRenduSerializer
from rest_framework.decorators import action
import logging
from rest_framework.exceptions import AuthenticationFailed
import requests



class DossierMedicalViewSet(viewsets.ViewSet):

        
    def list(self, request):
        # Retrieve all DossierMedical records without related 'patient' or 'soins'
        queryset = DossierMedical.objects.all()

        # Serialize the queryset (list of DossierMedical)
        serialized_data = DossierMedicalSerializer(queryset, many=True)

        # Return the serialized data as a JSON response
        return Response(serialized_data.data)

    def create(self, request):
        # Récupérer l'utilisateur connecté à partir du token
        user = getUserFromToken(request)  # Fetch the authenticated user
        if not isinstance(user, Medecin):  # Seul un médecin peut créer un dossier médical
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

        # Vérifier que tous les champs obligatoires sont présents
        required_fields = ['nss', 'nom', 'prenom', 'date_naissance', 'adresse', 'telephone', 'mutuelle', 'personne', 'email']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'error': f"{field} est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Récupérer ou créer le patient
            patient, created = Patient.objects.get_or_create(nss=patient_data['nss'], defaults=patient_data)

            # Associer le médecin traitant connecté au patient
            patient.medecin_traitant = user
            patient.save()  # Sauvegarder la modification du patient

            # Créer le dossier médical pour ce patient
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
        try:
            # Fetch the patient using the NSS (primary key)
            patient = Patient.objects.get(nss=pk)

            # Retrieve the medical record (DossierMedical) associated with the patient
            dossier = DossierMedical.objects.get(patient=patient)

            # Serialize the data and return it
            serialized_data = DossierMedicalSerializer(dossier)
            return Response(serialized_data.data, status=status.HTTP_200_OK)
        
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Medical record not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def lister_dossier_complet(self, request, pk=None):
        try:
            # Fetch the patient using the NSS (primary key)
            patient = Patient.objects.get(nss=pk)
            
            # Fetch the user from the token (Medecin or Patient)
            user = getUserFromToken(request)
            print(f"User type identified: {type(user)}")  # Debugging the type of user object

            # Check if the user is a Medecin
            if isinstance(user, Medecin):
                # Any Medecin can access the patient's dossier
                pass  # No restriction on Medecin

            # Check if the user is a Patient
            elif isinstance(user, Patient):
                # A patient can only access their own dossier
                if user != patient:
                    return Response({'error': 'Seul le patient peut accéder à son dossier médical.'}, status=status.HTTP_403_FORBIDDEN)

            # If the user is neither a Medecin nor a Patient, reject the request
            else:
                return Response({'error': 'Accès non autorisé. Seuls les médecins et les patients peuvent accéder à ce dossier médical.'}, status=status.HTTP_403_FORBIDDEN)

            # Retrieve the medical record (DossierMedical) associated with the patient
            dossier = DossierMedical.objects.get(patient=patient)

            # Retrieve related data (bilans, soins, etc.)
            bilans = dossier.bilans.all()
            soins = dossier.soins.all()
            comptes_rendus = dossier.compte_rendus.all()
            ordonnances = dossier.ordonnances.all()
            resumes = dossier.resumes.all()

            # Serialize the data
            dossier_serializer = DossierMedicalSerializer(dossier)
            bilan_serializer = BilanBiologiqueSerializer(bilans, many=True)
            soins_serializer = SoinSerializer(soins, many=True)
            compte_rendu_serializer = CompteRenduSerializer(comptes_rendus, many=True)
            ordonnance_serializer = OrdonnanceSerializer(ordonnances, many=True)
            resumes_serializer = ResumeSerializer(resumes, many=True)

            # Return all related data along with the dossier data
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
###################################


    @action(detail=True, methods=['post'])
    def ajouter_soin(self, request, pk=None):
        print(request.headers.get('Authorization'))  # Debugging line

        print("Inside ajouter_soin view")

        # Get user from token
        try:
            user = getUserFromToken(request)
        except AuthenticationFailed as e:
            return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)

        if not isinstance(user, Infirmier):
            return Response({'error': 'Only Infirmiers can add soins.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if NSS is provided
        nss = pk
        print(f"NSS: {nss}")  # Debugging line to check the NSS

        if not nss:
            return Response({'error': 'NSS manquant. Veuillez fournir un NSS valide.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if DossierMedical exists for the provided NSS
        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
            print(f"DossierMedical found: {dossier}")  # Debugging line to confirm the found DossierMedical
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable pour le NSS fourni.'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the Soin data
        serializer = SoinSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dossier_medical=dossier , infirmier=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"Serializer errors: {serializer.errors}")  # Debugging line to check why serializer is not valid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def lister_soins(self, request):
        nss = request.query_params.get('nss')  # Retrieve NSS from query params
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
        nss = pk
        if not nss:
            return Response({'error': 'NSS manquant'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find the associated DossierMedical by nss
        try:
            dossier = DossierMedical.objects.get(patient__nss=nss)
        except DossierMedical.DoesNotExist:
            return Response({'error': 'Dossier médical introuvable'}, status=status.HTTP_404_NOT_FOUND)

        # Check if a radiologue is associated with the request (you can adjust user authentication here)
        user = getUserFromToken(request)  # For example, type 2 is for Radiologue
        if not isinstance(user, Radiologue):
            return Response({'error': 'Only Radiologues can add compte rendu.'}, status=status.HTTP_403_FORBIDDEN)

        # Now create the compte rendu using the validated data from the request
        serializer = CompteRenduSerializer(data=request.data)
        if serializer.is_valid():
            # Associate dossier_medical directly from the found dossier
            serializer.save(dossier_medical=dossier, radiologue=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def lister_compte_rendus(self, request):
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
        user = getUserFromToken(request)

        # Check if the user is a Laborantin
        if not isinstance(user, Laborantin):
            return Response({'error': 'Only Laborantin can remplir bilans.'}, status=status.HTTP_403_FORBIDDEN)

        bid = pk
        if not bid:
            return Response({'error': 'Bilan ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bilan = BilanBiologique.objects.get(id_bilan=bid)
        except BilanBiologique.DoesNotExist:
            return Response({'error': 'Bilan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the results are already filled
        if bilan.glycimie or bilan.cholesteroel or bilan.pression_arterielle:
            return Response({'error': 'Results are already filled for this bilan.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the values from the request data
        glycimie_data = request.data.get('glycimie')
        cholesteroel_data = request.data.get('cholesteroel')
        pression_arterielle_data = request.data.get('pression_arterielle')

        # Validate that all fields are provided
        if not glycimie_data or not pression_arterielle_data or not cholesteroel_data:
            return Response({'error': 'All results data are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the BilanBiologique instance with the new values
        bilan.glycimie = glycimie_data
        bilan.cholesteroel = cholesteroel_data
        bilan.pression_arterielle = pression_arterielle_data
        bilan.laborantin = user
        bilan.save()

        # Return the updated bilan information
        return Response({
            "message": "Results updated successfully",
            "bilan_id": bilan.id_bilan,
            "glycimie": glycimie_data,
            "cholesteroel": cholesteroel_data,
            "pression_arterielle": pression_arterielle_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def lister_bilans(self, request):
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
    queryset = Ordonnance.objects.all()
    serializer_class = OrdonnanceSerializer

    @action(detail=False, methods=['get'])
    def lister_ordonnances(self, request):
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
        try:
            # Step 1: Fetch all ordonnances using the existing API endpoint
            response = requests.get("http://localhost:8000/dossier_patient/api/ordonnances/lister_ordonnances")
            if response.status_code != 200:
                    return Response({"error": "Failed to fetch ordonnances from lister_ordonnances API."},status=400)
            ordonnances_data = response.json().get("ordonnances", [])
            # Step 2: Simulate sending data to SGPH ,Simulate SGPH's response with dummy validation
            sgph_response = {"ordonnances": []}
            for ordonnance in ordonnances_data:
                sgph_response["ordonnances"].append({
                    "id_ordonnance": ordonnance["id_ordonnance"],
                    "status": "Validée" if ordonnance["id_ordonnance"] % 2 == 0 else "Rejetée"})
            # Step 3: Update ordonnances' statuses based on simulated SGPH response
            for ordonnance_response in sgph_response["ordonnances"]:
                ordonnance = Ordonnance.objects.get(id_ordonnance=ordonnance_response["id_ordonnance"])
                ordonnance.status = ordonnance_response["status"]
                ordonnance.save()
            return Response({"message": "Ordonnances processed successfully!", "response": sgph_response},status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)