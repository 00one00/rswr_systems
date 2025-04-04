from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create the missing technician_portal_techniciannotification table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if table exists first
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_schema = 'public'
                   AND table_name = 'technician_portal_techniciannotification'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                self.stdout.write(self.style.SUCCESS('Table already exists, nothing to do!'))
                return
            
            # Create the missing table
            cursor.execute("""
                CREATE TABLE "technician_portal_techniciannotification" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "message" text NOT NULL,
                    "read" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "redemption_id" bigint NULL,
                    "technician_id" bigint NOT NULL
                );
            """)
            
            # Add foreign key constraints
            cursor.execute("""
                ALTER TABLE "technician_portal_techniciannotification" 
                ADD CONSTRAINT "technician_portal_tech_redemption_id_75c2e126_fk_rewards_r" 
                FOREIGN KEY ("redemption_id") 
                REFERENCES "rewards_referrals_rewardredemption" ("id") 
                ON DELETE SET NULL
                DEFERRABLE INITIALLY DEFERRED;
            """)
            
            cursor.execute("""
                ALTER TABLE "technician_portal_techniciannotification" 
                ADD CONSTRAINT "technician_portal_tech_technician_id_f4cc6b65_fk_technicia" 
                FOREIGN KEY ("technician_id") 
                REFERENCES "technician_portal_technician" ("id") 
                ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED;
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX "technician_portal_techniciannotification_redemption_id_75c2e126" 
                ON "technician_portal_techniciannotification" ("redemption_id");
            """)
            
            cursor.execute("""
                CREATE INDEX "technician_portal_techniciannotification_technician_id_f4cc6b65"
                ON "technician_portal_techniciannotification" ("technician_id");
            """)
            
        self.stdout.write(self.style.SUCCESS('Successfully created technician_portal_techniciannotification table!')) 