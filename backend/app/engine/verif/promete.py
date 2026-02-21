import os
import re
from playwright.sync_api import sync_playwright  # On utilise la version SYNC

# S'assurer que le dossier logs existe
os.makedirs("logs", exist_ok=True)

def verify_certificate_on_promete(titre_principal: str, version: str, titulaire: str):
    suffix_clean = re.sub(r"\D", "", version).strip()
    if not suffix_clean: 
        suffix_clean = "1"

    # Utilisation du context manager SYNC
    with sync_playwright() as p:
        # Lancement synchrone (pas de await)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            url = "https://promete.din.developpement-durable.gouv.fr/promete/ConsulterTitreOuVisa?language=fr"
            page.goto(url, wait_until="networkidle", timeout=45000)

            page.wait_for_selector('#numeroTitre', timeout=10000)

            page.fill('#numeroTitre', titre_principal.strip())
            page.fill('#numeroVersion', suffix_clean)
            page.fill('#numeroAdm', titulaire.strip())

            page.click('button[type="submit"].btn-info')
            page.wait_for_load_state("networkidle")
            
            # Helper d'extraction synchrone
            def get_value_by_label(label_text):
                try:
                    locator = page.locator(f"label:has-text('{label_text}') + div div.form-control-static")
                    if locator.count() > 0:
                        return locator.first.inner_text().strip()
                    return None
                except:
                    return None

            full_text = page.inner_text("body")
            
            if "État du titre" in full_text or "Libellé du brevet" in full_text:
                official_data = {
                    "num_titre": get_value_by_label("N° du Titre"),
                    "num_titulaire": get_value_by_label("Titulaire"),
                    "date_naissance": get_value_by_label("Né le"),
                    "brevet_libelle": get_value_by_label("Brevet"),
                    "date_effet": get_value_by_label("Date d'effet"),
                    "date_expiration": get_value_by_label("Date d'expiration"),
                    "etat_officiel": get_value_by_label("État du titre"),
                    "autorite": get_value_by_label("Autorité de délivrance")
                }
                
                is_valide = "Valide" in (official_data["etat_officiel"] or "")
                return {
                    "status": "success",
                    "is_valid": is_valide,
                    "message": "Authentifié avec succès",
                    "official_details": official_data
                }
            
            if "aucun titre ne correspond" in full_text.lower():
                return {"status": "success", "is_valid": False, "message": "Aucun titre trouvé", "official_details": {}}

            page.screenshot(path=f"logs/unknown_page_{titre_principal}.png")
            return {"status": "error", "message": "Format de page inconnu"}

        except Exception as e:
            page.screenshot(path=f"logs/crash_{titre_principal}.png")
            return {"status": "error", "message": f"Erreur Playwright: {str(e)}"}
        finally:
            browser.close()