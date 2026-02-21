# app/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings # Import centralisé

def send_reference_check_email(to_email: str, candidate_name: str, yacht_name: str, token: str):
    verify_url = f"{settings.BASE_URL}/public/verify/{token}"

    message = MIMEMultipart("alternative")
    message["Subject"] = f"⚓ Vérification d'expérience : {candidate_name}"
    message["From"] = f"Harmony Network <{settings.SMTP_USER}>"
    message["To"] = to_email

    text = f"Bonjour, {candidate_name} souhaite valider son expérience sur {yacht_name}. Lien : {verify_url}"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #0F172A;">
        <h2 style="color: #0F172A;">Bonjour,</h2>
        <p><strong>{candidate_name}</strong> a ajouté une expérience sur le yacht <strong>{yacht_name}</strong> à son profil Harmony.</p>
        <p>Pourriez-vous confirmer cette expérience et la qualité de son service ?</p>
        <div style="margin: 30px 0;">
          <a href="{verify_url}" 
             style="background-color: #0F172A; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold;">
             VÉRIFIER L'EXPÉRIENCE
          </a>
        </div>
        <p style="font-size: 12px; color: #64748B;">L'équipe Harmony Maritime Network.</p>
      </body>
    </html>
    """
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"❌ Erreur SMTP: {e}")
        return False