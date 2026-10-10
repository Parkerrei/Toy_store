from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
import pprint

class Command(BaseCommand):
    help = 'Fetches and decodes the hidden session_data dictionary for any active session key.'

    def add_arguments(self, parser):
        # We make the session key a REQUIRED positional argument
        parser.add_argument(
            'session_key', 
            type=str, 
            help='The 40-character session_key or sessionid cookie string from Supabase'
        )

    def handle(self, *args, **options):
        session_key = options['session_key']

        try:
            # 1. Fetch the raw session row from your Supabase/PostgreSQL table
            session_row = Session.objects.get(pk=session_key)
            
            # 2. Decode the signed Base64 string into a readable Python dictionary
            decoded_data = session_row.get_decoded()

            self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- Session Key: {session_key} ---"))
            self.stdout.write(f"📅 Expires On: {session_row.expire_date}")
            self.stdout.write(self.style.MIGRATE_LABEL("📦 Decoded Data Dictionary:"))
            
            # 3. Pretty-print the dictionary so nested fields (like cart lists) look organized
            pp = pprint.PrettyPrinter(indent=4, stream=self.stdout)
            pp.pprint(decoded_data)
            self.stdout.write("\n")

        except Session.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: No session found matching key '{session_key}'. It may have expired or been deleted.")
            )
