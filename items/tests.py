import io
from datetime import date, timedelta
from PIL import Image as PILImage

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Item, RecoveryRequest, ItemReport
from .forms import ItemForm, UserRegisterForm
from .matching import calculate_match_score, find_possible_matches, extract_keywords


def generate_test_image(filename="test.png", size=(100, 100), color="blue", format="PNG"):
    """Helper to generate a valid in-memory test image."""
    file_obj = io.BytesIO()
    img = PILImage.new("RGB", size=size, color=color)
    img.save(file_obj, format=format)
    file_obj.seek(0)
    return SimpleUploadedFile(filename, file_obj.read(), content_type=f"image/{format.lower()}")


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'student123',
            'first_name': 'Alex',
            'last_name': 'Morgan',
            'email': 'alex@campus.edu',
            'password1': 'CampusSecurePass123!',
            'password2': 'CampusSecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='student123').exists())
        user = User.objects.get(username='student123')
        self.assertEqual(user.email, 'alex@campus.edu')

    def test_user_registration_duplicate_email(self):
        User.objects.create_user(username='existing', email='duplicate@campus.edu', password='password123')
        form = UserRegisterForm(data={
            'username': 'newuser',
            'first_name': 'Sam',
            'last_name': 'Wilson',
            'email': 'duplicate@campus.edu',
            'password1': 'StrongPassWord123#',
            'password2': 'StrongPassWord123#',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_login_and_logout(self):
        user = User.objects.create_user(username='john_doe', password='SecretPassword123!')
        login_success = self.client.login(username='john_doe', password='SecretPassword123!')
        self.assertTrue(login_success)

        # Access dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class ItemManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='alice', password='Password123!')
        self.other_user = User.objects.create_user(username='bob', password='Password123!')

    def test_create_lost_item(self):
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(reverse('report_lost'), {
            'title': 'Lost Casio fx-991EX Calculator',
            'category': 'BOOKS',
            'campus_location': 'Computer Science Lab - Room 204',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Left on desk 14 near the whiteboard. Has a silver barcode sticker.',
        })
        self.assertEqual(response.status_code, 302)
        item = Item.objects.filter(title__contains='Casio').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.report_type, 'LOST')
        self.assertEqual(item.status, 'OPEN')
        self.assertEqual(item.created_by, self.owner)

    def test_create_found_item(self):
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(reverse('report_found'), {
            'title': 'Found Black Hydro Flask Water Bottle',
            'category': 'BOTTLES',
            'campus_location': 'Sports Complex & Ground',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Found near the bleachers after the basketball match.',
        })
        self.assertEqual(response.status_code, 302)
        item = Item.objects.filter(title__contains='Hydro Flask').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.report_type, 'FOUND')

    def test_required_field_validation(self):
        # Empty title and location should fail
        form = ItemForm(data={
            'title': '',
            'category': 'ELECTRONICS',
            'report_type': 'LOST',
            'campus_location': '',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Some description',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('campus_location', form.errors)

    def test_valid_image_upload(self):
        test_img = generate_test_image("item.jpg", format="JPEG")
        form = ItemForm(data={
            'title': 'Keys with Blue Lanyard',
            'category': 'KEYS',
            'report_type': 'FOUND',
            'campus_location': 'Central Library',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Has two keys and a college crest tag.',
        }, files={'image': test_img})
        self.assertTrue(form.is_valid())

    def test_disallowed_image_format_rejected(self):
        fake_file = SimpleUploadedFile("bad.txt", b"plain text content", content_type="text/plain")
        form = ItemForm(data={
            'title': 'Test Item',
            'category': 'OTHER',
            'report_type': 'LOST',
            'campus_location': 'Canteen',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Test details',
        }, files={'image': fake_file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_listing_ownership_permission_for_edit(self):
        # Item owned by Alice
        item = Item.objects.create(
            title="Alice's Lost Earphones",
            category="ELECTRONICS",
            report_type="LOST",
            campus_location="Library",
            date_lost_or_found=date.today(),
            description="White wireless earbuds",
            created_by=self.owner
        )

        # Bob logs in and tries to edit Alice's item
        self.client.login(username='bob', password='Password123!')
        response = self.client.post(reverse('edit_item', kwargs={'pk': item.pk}), {
            'title': 'Malicious Edit by Bob',
            'category': 'ELECTRONICS',
            'report_type': 'LOST',
            'campus_location': 'Library',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'Hacked description',
        })
        # Should redirect with error, not save
        item.refresh_from_db()
        self.assertEqual(item.title, "Alice's Lost Earphones")

        # Alice logs in and can edit
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(reverse('edit_item', kwargs={'pk': item.pk}), {
            'title': "Alice's Wireless Earbuds (Updated)",
            'category': 'ELECTRONICS',
            'report_type': 'LOST',
            'campus_location': 'Library - 2nd Floor',
            'date_lost_or_found': date.today().isoformat(),
            'description': 'White wireless earbuds in black case',
        })
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.title, "Alice's Wireless Earbuds (Updated)")

    def test_owner_can_mark_recovered(self):
        item = Item.objects.create(
            title="Lost Wallet",
            category="BAGS",
            report_type="LOST",
            campus_location="Canteen",
            date_lost_or_found=date.today(),
            description="Brown leather wallet",
            created_by=self.owner
        )
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(reverse('update_item_status', kwargs={'pk': item.pk}), {
            'status': 'RECOVERED'
        })
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, 'RECOVERED')


class SearchAndFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='tester', password='pass')
        today = date.today()

        # Item 1: Lost Dell Charger in Library
        self.item1 = Item.objects.create(
            title="Dell 65W Laptop Charger",
            description="Black charger with round tip",
            category="ELECTRONICS",
            report_type="LOST",
            campus_location="Central Library",
            date_lost_or_found=today - timedelta(days=2),
            status="OPEN",
            created_by=user
        )

        # Item 2: Found Dell Charger in Library
        self.item2 = Item.objects.create(
            title="Found Dell Laptop Adapter",
            description="Dell 65 watt power supply found on 2nd floor desk",
            category="ELECTRONICS",
            report_type="FOUND",
            campus_location="Central Library",
            date_lost_or_found=today - timedelta(days=1),
            status="OPEN",
            created_by=user
        )

        # Item 3: Lost ID Card in Canteen
        self.item3 = Item.objects.create(
            title="Student ID Card Mechanical Dept",
            description="Identity badge with blue strap",
            category="ID_CARDS",
            report_type="LOST",
            campus_location="Student Canteen & Food Court",
            date_lost_or_found=today - timedelta(days=5),
            status="RECOVERED",
            created_by=user
        )

    def test_search_by_query_keyword(self):
        response = self.client.get(reverse('browse'), {'q': 'Adapter'})
        self.assertEqual(response.status_code, 200)
        items = list(response.context['page_obj'])
        self.assertIn(self.item2, items)
        self.assertNotIn(self.item3, items)

    def test_filter_by_report_type(self):
        response = self.client.get(reverse('browse'), {'type': 'FOUND'})
        items = list(response.context['page_obj'])
        self.assertIn(self.item2, items)
        self.assertNotIn(self.item1, items)

    def test_filter_by_category(self):
        response = self.client.get(reverse('browse'), {'category': 'ID_CARDS'})
        items = list(response.context['page_obj'])
        self.assertIn(self.item3, items)
        self.assertNotIn(self.item1, items)

    def test_filter_by_date_range(self):
        today = date.today()
        # Filter for items in the last 3 days
        response = self.client.get(reverse('browse'), {
            'date_from': (today - timedelta(days=3)).isoformat(),
            'date_to': today.isoformat()
        })
        items = list(response.context['page_obj'])
        self.assertIn(self.item1, items)
        self.assertIn(self.item2, items)
        self.assertNotIn(self.item3, items)  # Item 3 is 5 days ago

    def test_filter_by_status(self):
        response = self.client.get(reverse('browse'), {'status': 'RECOVERED'})
        items = list(response.context['page_obj'])
        self.assertIn(self.item3, items)
        self.assertNotIn(self.item1, items)


class PossibleMatchEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='match_user', password='password')
        today = date.today()

        # Target: Lost Sony WH-1000XM4 Headphones in Library
        self.lost_headphones = Item.objects.create(
            title="Lost Sony WH-1000XM4 Noise Canceling Headphones",
            description="Black over-ear headphones left in quiet zone table 5",
            category="ELECTRONICS",
            report_type="LOST",
            campus_location="Central Library",
            date_lost_or_found=today - timedelta(days=1),
            status="OPEN",
            created_by=self.user
        )

        # Candidate 1: Strong match - Found Sony headphones in library
        self.found_headphones = Item.objects.create(
            title="Found Black Sony Headphones",
            description="Sony over-ear wireless headphones picked up from library table",
            category="ELECTRONICS",
            report_type="FOUND",
            campus_location="Central Library",
            date_lost_or_found=today,
            status="OPEN",
            created_by=self.user
        )

        # Candidate 2: Different category & location (Water bottle in Canteen)
        self.found_bottle = Item.objects.create(
            title="Metal Water Bottle",
            description="Green thermos bottle",
            category="BOTTLES",
            report_type="FOUND",
            campus_location="Student Canteen & Food Court",
            date_lost_or_found=today,
            status="OPEN",
            created_by=self.user
        )

    def test_keyword_extraction(self):
        tokens = extract_keywords("Lost Sony WH-1000XM4 Noise Canceling Headphones in the library")
        self.assertIn("sony", tokens)
        self.assertIn("headphones", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("in", tokens)

    def test_high_match_score_for_matching_candidate(self):
        score_info = calculate_match_score(self.lost_headphones, self.found_headphones)
        # Category (+25) + Location (+20) + Date (+15) + Keywords (>15) => > 70
        self.assertGreaterEqual(score_info['score'], 70)
        self.assertEqual(score_info['confidence'], 'High Match')

    def test_low_match_for_unrelated_item(self):
        score_info = calculate_match_score(self.lost_headphones, self.found_bottle)
        self.assertLess(score_info['score'], 25)

    def test_find_possible_matches_filters_and_sorts(self):
        matches = find_possible_matches(self.lost_headphones, limit=5, min_threshold=25)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['candidate'], self.found_headphones)


class RecoveryRequestTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='finder_dave', password='Password123!')
        self.claimant = User.objects.create_user(username='claimant_emma', password='Password123!')
        self.other_person = User.objects.create_user(username='charlie', password='Password123!')

        self.item = Item.objects.create(
            title="Found Blue Laptop Bag with Asus Charger",
            description="Found under desk in CS Lab 3. Contains pens and a spiral notebook.",
            category="BAGS",
            report_type="FOUND",
            campus_location="Computer Science Lab",
            date_lost_or_found=date.today(),
            status="OPEN",
            created_by=self.owner
        )

    def test_submit_recovery_request_success(self):
        self.client.login(username='claimant_emma', password='Password123!')
        response = self.client.post(reverse('submit_claim', kwargs={'pk': self.item.pk}), {
            'message': 'This is my bag! Inside there is a blue notebook with "Emma Wilson - CS 301" written on the first page.'
        })
        self.assertEqual(response.status_code, 302)
        claim = RecoveryRequest.objects.filter(item=self.item, requester=self.claimant).first()
        self.assertIsNotNone(claim)
        self.assertEqual(claim.status, 'PENDING')

    def test_owner_cannot_claim_own_item(self):
        self.client.login(username='finder_dave', password='Password123!')
        response = self.client.post(reverse('submit_claim', kwargs={'pk': self.item.pk}), {
            'message': 'Trying to claim my own reported item'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RecoveryRequest.objects.filter(item=self.item, requester=self.owner).exists())

    def test_duplicate_active_claim_prevented(self):
        self.client.login(username='claimant_emma', password='Password123!')
        # Submit first claim
        self.client.post(reverse('submit_claim', kwargs={'pk': self.item.pk}), {
            'message': 'First claim attempt'
        })
        self.assertEqual(RecoveryRequest.objects.filter(item=self.item, requester=self.claimant).count(), 1)

        # Submit second claim while first is still pending
        response = self.client.post(reverse('submit_claim', kwargs={'pk': self.item.pk}), {
            'message': 'Second duplicate claim attempt'
        })
        self.assertEqual(RecoveryRequest.objects.filter(item=self.item, requester=self.claimant).count(), 1)

    def test_owner_approves_claim_and_updates_item_status(self):
        # Create claim
        claim = RecoveryRequest.objects.create(
            item=self.item,
            requester=self.claimant,
            message="Contains my student ID and notebooks"
        )

        self.client.login(username='finder_dave', password='Password123!')
        response = self.client.post(reverse('manage_claim', kwargs={'request_id': claim.pk}), {
            'action': 'approve',
            'owner_notes': 'Please meet at the CS lab tomorrow at 11 AM.'
        })
        self.assertEqual(response.status_code, 302)
        claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(claim.status, 'APPROVED')
        self.assertEqual(self.item.status, 'CLAIM_PENDING')
        self.assertEqual(claim.owner_notes, 'Please meet at the CS lab tomorrow at 11 AM.')

    def test_owner_completes_handover(self):
        claim = RecoveryRequest.objects.create(
            item=self.item,
            requester=self.claimant,
            message="Verified owner",
            status='APPROVED'
        )
        self.item.status = 'CLAIM_PENDING'
        self.item.save()

        self.client.login(username='finder_dave', password='Password123!')
        response = self.client.post(reverse('manage_claim', kwargs={'request_id': claim.pk}), {
            'action': 'complete'
        })
        self.assertEqual(response.status_code, 302)
        claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(claim.status, 'COMPLETED')
        self.assertEqual(self.item.status, 'RECOVERED')

    def test_unauthorized_user_cannot_manage_claims(self):
        claim = RecoveryRequest.objects.create(
            item=self.item,
            requester=self.claimant,
            message="Emma's claim"
        )
        # Charlie tries to approve Emma's claim on Dave's item
        self.client.login(username='charlie', password='Password123!')
        response = self.client.post(reverse('manage_claim', kwargs={'request_id': claim.pk}), {
            'action': 'approve'
        })
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'PENDING')  # Unchanged!


# ==============================================================================
# Assessment Requirements Test Suites
# ==============================================================================

from .models import FAQ, SupportTicket, ErrorCode
from .error_codes import ERROR_CATALOG, get_all_error_codes
from .ai_assistant import generate_ai_response
from .third_party_api import get_campus_weather_and_status


class AssessmentFAQTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Seed 10 FAQs in SQL
        for i in range(1, 11):
            FAQ.objects.create(
                question=f"Campus Question #{i}: How to handle item recovery?",
                answer=f"Answer for campus FAQ #{i} describing guidelines and proof verification.",
                category='REPORTING' if i % 2 == 0 else 'TECHNICAL',
                order=i
            )

    def test_minimum_10_faqs_stored_in_sql(self):
        count = FAQ.objects.filter(is_active=True).count()
        self.assertGreaterEqual(count, 10)

    def test_faqs_page_renders_with_faqs(self):
        response = self.client.get(reverse('faqs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campus Question #1")
        self.assertContains(response, "Campus Question #10")

    def test_faqs_category_filter(self):
        response = self.client.get(reverse('faqs'), {'category': 'TECHNICAL'})
        self.assertEqual(response.status_code, 200)
        faqs = list(response.context['faqs'])
        self.assertTrue(all(f.category == 'TECHNICAL' for f in faqs))


class AssessmentSupportTicketTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='student_ticket_user', password='Password123!')

    def test_create_support_ticket_stored_in_sql(self):
        self.client.login(username='student_ticket_user', password='Password123!')
        response = self.client.post(reverse('support_center'), {
            'contact_email': 'student@campus.edu',
            'subject': 'Unable to upload ID photo due to CLF-1001',
            'related_error_code': 'CLF-1001',
            'priority': 'HIGH',
            'message': 'My photo fails validation with code CLF-1001. Please help verify file limits.'
        })
        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.filter(related_error_code='CLF-1001').first()
        self.assertIsNotNone(ticket)
        self.assertTrue(ticket.ticket_number.startswith('TKT-'))
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.priority, 'HIGH')


class AssessmentErrorCodeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_minimum_eight_error_codes_defined(self):
        required_codes = ['400', '401', '403', '404', '429', '500', '503', 'CLF-1001']
        for code in required_codes:
            self.assertIn(code, ERROR_CATALOG)

    def test_error_catalog_page_renders(self):
        response = self.client.get(reverse('error_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CLF-1001")
        self.assertContains(response, "404")

    def test_custom_404_page_has_ask_assistant_option(self):
        response = self.client.get('/non-existent-page-testing-custom-404/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Ask the Assistant", status_code=404)

    def test_error_simulation_endpoints(self):
        # Test 404 simulation
        r_404 = self.client.get(reverse('simulate_error', kwargs={'code': '404'}))
        self.assertEqual(r_404.status_code, 404)

        # Test 403 simulation
        r_403 = self.client.get(reverse('simulate_error', kwargs={'code': '403'}))
        self.assertEqual(r_403.status_code, 403)

        # Test 429 simulation
        r_429 = self.client.get(reverse('simulate_error', kwargs={'code': '429'}))
        self.assertEqual(r_429.status_code, 429)

        # Test CLF-1001 simulation
        r_clf = self.client.get(reverse('simulate_error', kwargs={'code': 'CLF-1001'}))
        self.assertEqual(r_clf.status_code, 422)


class AssessmentAIAssistantAndMongoTests(TestCase):
    def setUp(self):
        self.client = Client()
        FAQ.objects.create(
            question="How do I report a lost calculator?",
            answer="Navigate to Report Lost Item, select Books and Calculators category, and submit.",
            category='REPORTING',
            order=1
        )

    def test_ai_explains_error_code(self):
        resp = generate_ai_response("What does error 404 mean?")
        self.assertEqual(resp['error_code'], '404')
        self.assertIn("Page or Item Not Found", resp['answer'])

    def test_ai_answers_from_sql_faq(self):
        resp = generate_ai_response("How do I report a lost calculator?")
        self.assertIn("Navigate to Report Lost Item", resp['answer'])

    def test_ai_creates_ticket_offer_for_unknown_question(self):
        resp = generate_ai_response("What is the quantum mechanics textbook room number in Mars?")
        self.assertTrue(resp['can_create_ticket'])

    def test_chat_api_endpoint(self):
        import json
        response = self.client.post(
            reverse('chat_api'),
            data=json.dumps({'message': 'Explain error CLF-1001', 'session_id': 'test_sess_123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_code'], 'CLF-1001')

    def test_chat_feedback_api_endpoint(self):
        import json
        response = self.client.post(
            reverse('chat_feedback_api'),
            data=json.dumps({'rating': 5, 'comment': 'Extremely helpful AI assistant', 'session_id': 'test_sess_123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)


class AssessmentHealthAndThirdPartyTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint_json(self):
        response = self.client.get(reverse('health_check') + '?format=json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('sql_database', data['services'])
        self.assertIn('mongodb_storage', data['services'])
        self.assertIn('third_party_api', data['services'])

    def test_third_party_api_fallback_behavior(self):
        data = get_campus_weather_and_status()
        self.assertIn('temperature', data)
        self.assertIn('campus_status', data)


import json


class AssessmentRubricExtendedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test_student_rubric', password='Password123!', email='rubric@campus.edu')
        
        # Seed 8 ErrorCodes into SQL
        import json
        for code, info in ERROR_CATALOG.items():
            ErrorCode.objects.update_or_create(
                code=code,
                defaults={
                    'title': info['title'],
                    'category': info['category'],
                    'summary': info['summary'],
                    'student_explanation': info['student_explanation'],
                    'campus_troubleshooting': json.dumps(info['campus_troubleshooting']),
                    'http_status': info['http_status'],
                    'is_active': True,
                }
            )

    def test_eight_error_codes_stored_in_sql(self):
        """Assessment Col F: 8+ error codes in SQL."""
        count = ErrorCode.objects.filter(is_active=True).count()
        self.assertGreaterEqual(count, 8)
        # Verify 404 and CLF-1001 exist in SQL
        self.assertTrue(ErrorCode.objects.filter(code='404').exists())
        self.assertTrue(ErrorCode.objects.filter(code='CLF-1001').exists())

    def test_api_errors_endpoint(self):
        """Verify /api/errors/ returns 8+ error codes."""
        resp = self.client.get(reverse('api_errors'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data['count'], 8)
        self.assertEqual(data['source'], 'SQL (items_errorcode)')

    def test_faq_api_endpoint(self):
        """Assessment Col E: FAQ page from API."""
        resp = self.client.get(reverse('api_faqs'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('faqs', data)
        self.assertIn('count', data)

    def test_ticket_crud_workflow(self):
        """Assessment Col I: Ticket created when unsure (CRUD)."""
        # 1. CREATE via REST API
        post_resp = self.client.post(
            reverse('api_ticket_crud_list'),
            data=json.dumps({
                'subject': 'CRUD Test Ticket',
                'message': 'Testing full CRUD workflow',
                'contact_email': 'rubric@campus.edu',
                'priority': 'HIGH'
            }),
            content_type='application/json'
        )
        self.assertEqual(post_resp.status_code, 201)
        created_data = post_resp.json()
        tkt_ref = created_data['ticket_number']
        self.assertTrue(tkt_ref.startswith('TKT-'))

        # 2. READ via REST API
        get_resp = self.client.get(reverse('api_ticket_crud', kwargs={'ticket_number': tkt_ref}))
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()['subject'], 'CRUD Test Ticket')

        # 3. UPDATE via REST API
        patch_resp = self.client.patch(
            reverse('api_ticket_crud', kwargs={'ticket_number': tkt_ref}),
            data=json.dumps({'message': 'Updated message details'}),
            content_type='application/json'
        )
        self.assertEqual(patch_resp.status_code, 200)
        updated_ticket = SupportTicket.objects.get(ticket_number=tkt_ref)
        self.assertEqual(updated_ticket.message, 'Updated message details')

        # 4. DELETE / CLOSE via REST API
        del_resp = self.client.delete(reverse('api_ticket_crud', kwargs={'ticket_number': tkt_ref}))
        self.assertEqual(del_resp.status_code, 200)
        closed_ticket = SupportTicket.objects.get(ticket_number=tkt_ref)
        self.assertEqual(closed_ticket.status, 'CLOSED')


