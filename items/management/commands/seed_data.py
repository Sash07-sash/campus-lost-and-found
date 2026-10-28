from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from items.models import Item, RecoveryRequest


class Command(BaseCommand):
    help = 'Seeds sample campus lost and found items, users, and recovery requests for demonstration.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding sample campus data...")

        # 1. Create Demo Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@campus.edu',
                'first_name': 'Campus',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        student_rahul, _ = User.objects.get_or_create(
            username='rahul_sharma',
            defaults={
                'email': 'rahul.s@campus.edu',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
            }
        )
        student_rahul.set_password('student123')
        student_rahul.save()

        student_priya, _ = User.objects.get_or_create(
            username='priya_patel',
            defaults={
                'email': 'priya.p@campus.edu',
                'first_name': 'Priya',
                'last_name': 'Patel',
            }
        )
        student_priya.set_password('student123')
        student_priya.save()

        student_arjun, _ = User.objects.get_or_create(
            username='arjun_kumar',
            defaults={
                'email': 'arjun.k@campus.edu',
                'first_name': 'Arjun',
                'last_name': 'Kumar',
            }
        )
        student_arjun.set_password('student123')
        student_arjun.save()

        today = timezone.now().date()

        # 2. Sample Items
        items_data = [
            {
                'title': 'Casio fx-991EX Scientific Calculator',
                'description': 'Left on desk 12 in Computer Science Lab Room 204. Black with silver slide cover. Has a tiny barcode sticker at the back.',
                'category': 'BOOKS',
                'report_type': 'LOST',
                'campus_location': 'Computer Science Lab',
                'date_lost_or_found': today - timedelta(days=2),
                'status': 'OPEN',
                'created_by': student_rahul,
            },
            {
                'title': 'Casio Scientific Calculator with Slide Case',
                'description': 'Found a Casio fx-991EX on table 12 in CS Lab 204 after lab session. Handed over to lab attendant desk.',
                'category': 'BOOKS',
                'report_type': 'FOUND',
                'campus_location': 'Computer Science Lab',
                'date_lost_or_found': today - timedelta(days=2),
                'status': 'OPEN',
                'created_by': student_priya,
            },
            {
                'title': 'College Student ID Card - CSE 3rd Year',
                'description': 'Lost my college student identity card with blue branded lanyard. Roll number starts with 21CS...',
                'category': 'ID_CARDS',
                'report_type': 'LOST',
                'campus_location': 'Central Library',
                'date_lost_or_found': today - timedelta(days=3),
                'status': 'OPEN',
                'created_by': student_arjun,
            },
            {
                'title': 'Student ID Card with Blue Lanyard Found',
                'description': 'Found an ID card near the Library 1st floor turnstile. Deposited at Library reception desk for verification.',
                'category': 'ID_CARDS',
                'report_type': 'FOUND',
                'campus_location': 'Central Library',
                'date_lost_or_found': today - timedelta(days=2),
                'status': 'OPEN',
                'created_by': student_rahul,
            },
            {
                'title': 'Black Dell 65W Laptop Charger',
                'description': 'Left my Dell charger plugged into the wall outlet in Science Block Canteen charging zone.',
                'category': 'ELECTRONICS',
                'report_type': 'LOST',
                'campus_location': 'Student Canteen & Food Court',
                'date_lost_or_found': today - timedelta(days=1),
                'status': 'OPEN',
                'created_by': student_priya,
            },
            {
                'title': 'Found Dell USB-C Laptop Power Adapter',
                'description': 'Found near the canteen corner charging booth. Safe with canteen supervisor.',
                'category': 'ELECTRONICS',
                'report_type': 'FOUND',
                'campus_location': 'Student Canteen & Food Court',
                'date_lost_or_found': today - timedelta(days=1),
                'status': 'OPEN',
                'created_by': student_arjun,
            },
            {
                'title': 'Set of 3 Keys with Batman Keychain',
                'description': 'Two brass room keys and a bike key attached to a black metal Batman logo keychain.',
                'category': 'KEYS',
                'report_type': 'LOST',
                'campus_location': 'Sports Complex & Ground',
                'date_lost_or_found': today - timedelta(days=4),
                'status': 'CLAIM_PENDING',
                'created_by': student_rahul,
            },
            {
                'title': 'Keys with Superhero Keychain Found at Basketball Court',
                'description': 'Found keys sitting on the court boundary bench after evening practice.',
                'category': 'KEYS',
                'report_type': 'FOUND',
                'campus_location': 'Sports Complex & Ground',
                'date_lost_or_found': today - timedelta(days=4),
                'status': 'OPEN',
                'created_by': student_priya,
            },
            {
                'title': 'Navy Blue Wildcraft Backpack',
                'description': 'Accidentally misplaced in Main Auditorium row G during the orientation symposium. Contains textbook and water bottle.',
                'category': 'BAGS',
                'report_type': 'LOST',
                'campus_location': 'Main Auditorium',
                'date_lost_or_found': today - timedelta(days=6),
                'status': 'RECOVERED',
                'created_by': student_arjun,
            },
            {
                'title': 'Milton Stainless Steel Water Bottle (Silver)',
                'description': 'Insulated flask left behind in Physics Seminar Hall 1.',
                'category': 'BOTTLES',
                'report_type': 'FOUND',
                'campus_location': 'Science & Research Block',
                'date_lost_or_found': today - timedelta(days=2),
                'status': 'OPEN',
                'created_by': student_rahul,
            },
        ]

        created_items = []
        for d in items_data:
            item, created = Item.objects.get_or_create(
                title=d['title'],
                defaults=d
            )
            created_items.append(item)

        # 3. Sample Recovery Request
        # Rahul submits a claim on Priya's found calculator
        found_calc = created_items[1]
        claim, _ = RecoveryRequest.objects.get_or_create(
            item=found_calc,
            requester=student_rahul,
            defaults={
                'message': 'Hello Priya, this is my Casio calculator. There is a faded white tape on the back of the slide cover with "RS" written in black marker.',
                'status': 'PENDING'
            }
        )

        # 4. Assessment Requirement: Minimum 10 FAQs and 8 Error Codes stored in SQL database
        from items.models import FAQ, SupportTicket, ErrorCode
        from items.error_codes import ERROR_CATALOG
        import json

        faqs_data = [
            {
                'question': 'How do I report an item I lost on campus?',
                'answer': 'Click "Report Lost Item" on the top navigation bar, sign in with your college credentials, and fill in the title, category, campus spot (e.g. Central Library 2nd floor), date, and description. You can optionally upload a photo. To protect your security, never include passwords, PINs, or confidential ID digits.',
                'category': 'REPORTING',
                'order': 1
            },
            {
                'question': 'How do I report an item I found on campus?',
                'answer': 'Click "Report Found Item" on the navigation bar. Describe the item, note the location where you spotted it, and consider depositing high-value belongings at the nearest official desk (such as the Central Library Desk or Security Office).',
                'category': 'REPORTING',
                'order': 2
            },
            {
                'question': 'What should I do if I lost my college student ID card?',
                'answer': 'First, filter by category "ID Cards" on the Browse Listings page. If you do not see it, file a "Report Lost" listing immediately and alert the campus registrar office. When describing your ID card, do not disclose your full roll number.',
                'category': 'REPORTING',
                'order': 3
            },
            {
                'question': 'How does the Possible-Matches suggestion engine work?',
                'answer': 'When you view a listing, our rule-based algorithm cross-examines title and description keywords (40%), category (25%), campus location (20%), and date proximity (15%) against active opposing listings. When a strong candidate is found, it appears in the "Possible Matches" section with an explanatory breakdown.',
                'category': 'SEARCH',
                'order': 4
            },
            {
                'question': 'How do I submit an ownership recovery claim for an item?',
                'answer': 'Open the item details page and click "Submit Recovery Claim". Provide specific identifying details that only the true owner would know (e.g. scratch marks, lock screen wallpaper, stickers, or internal contents). The listing creator will review your claim privately.',
                'category': 'CLAIMS',
                'order': 5
            },
            {
                'question': 'What happens once my recovery claim is approved?',
                'answer': 'When the listing creator approves your claim, the item status updates to "Claim Pending". You can then arrange an in-person handover in a verified public location on campus, such as the Central Library information counter.',
                'category': 'CLAIMS',
                'order': 6
            },
            {
                'question': 'What safety precautions should I follow during an item handover?',
                'answer': 'Always conduct handovers during daylight in busy, public campus areas. Request the claimant to show student ID or unlock electronic devices before handing them over. Never send money, courier fees, or reveal banking PINs.',
                'category': 'SAFETY',
                'order': 7
            },
            {
                'question': 'Why is my personal email and phone number not displayed publicly?',
                'answer': 'To prevent spam, harassment, and fraudulent identity theft, Campus Lost & Found never shows contact emails or phone numbers on public listing cards. All verification is handled through in-app recovery claims.',
                'category': 'SAFETY',
                'order': 8
            },
            {
                'question': 'Why did my image upload fail with error code CLF-1001?',
                'answer': 'Site-specific error CLF-1001 occurs when an uploaded photo exceeds the 5MB file size limit or uses an unsupported file format. Please upload photos in JPG, PNG, or WEBP format under 5MB.',
                'category': 'TECHNICAL',
                'order': 9
            },
            {
                'question': 'What does Error 404 (Page or Item Not Found) mean?',
                'answer': 'Error 404 means the requested page or item listing ID does not exist, or was removed by the owner after being successfully recovered. Try searching for the item on the Browse Listings page.',
                'category': 'TECHNICAL',
                'order': 10
            },
            {
                'question': 'What does Error 403 (Forbidden) mean?',
                'answer': 'Error 403 indicates that you do not have permission to modify this listing (only the original creator can edit or close a listing), or your browser CSRF token needs refreshing. Refresh your browser (Ctrl+F5) and ensure you are logged into the correct account.',
                'category': 'TECHNICAL',
                'order': 11
            },
            {
                'question': 'How is a technical Support Ticket different from a Recovery Claim?',
                'answer': 'A Recovery Claim is sent to another student to reclaim a lost physical belonging. A Support Ticket is sent to college web administrators for assistance with technical errors, account problems, or platform bugs.',
                'category': 'ACCOUNT',
                'order': 12
            },
        ]

        seeded_faqs = 0
        for f in faqs_data:
            faq_obj, created = FAQ.objects.get_or_create(
                question=f['question'],
                defaults=f
            )
            seeded_faqs += 1

        # Assessment Requirement: Minimum 8 Error Codes stored in SQL database
        seeded_errors = 0
        for code, err in ERROR_CATALOG.items():
            ErrorCode.objects.update_or_create(
                code=code,
                defaults={
                    'title': err['title'],
                    'category': err['category'],
                    'summary': err['summary'],
                    'student_explanation': err['student_explanation'],
                    'campus_troubleshooting': json.dumps(err['campus_troubleshooting']),
                    'http_status': err['http_status'],
                    'is_active': True,
                }
            )
            seeded_errors += 1

        # 5. Assessment Requirement: Support tickets stored in SQL
        ticket, _ = SupportTicket.objects.get_or_create(
            subject='Assistance with photo upload on laptop charger listing',
            defaults={
                'ticket_number': 'TKT-DEMO1001',
                'user': student_priya,
                'contact_email': 'priya.p@campus.edu',
                'message': 'Hello, I received error CLF-1001 when uploading a photo of the charger from my mobile camera. Could you help verify if high-resolution images are allowed?',
                'related_error_code': 'CLF-1001',
                'priority': 'MEDIUM',
                'status': 'OPEN',
                'admin_notes': 'Advised user on 5MB compression.'
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(created_items)} items, {seeded_faqs} FAQs in SQL, 1 support ticket, 4 users, and 1 recovery claim!\n"
            "Default Superuser:\n"
            "  Username: admin\n"
            "  Password: admin123\n"
            "Demo Student Users:\n"
            "  rahul_sharma / student123\n"
            "  priya_patel / student123\n"
            "  arjun_kumar / student123\n"
        ))

