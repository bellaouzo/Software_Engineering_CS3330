from flask import current_app
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Returns a new Supabase client built from the app's SUPABASE_URL and SUPABASE_KEY.

    Raises SupabaseException if either value is missing from the environment.
    """
    return create_client(
        current_app.config["SUPABASE_URL"],
        current_app.config["SUPABASE_KEY"],
    )
