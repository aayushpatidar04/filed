import jwt
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def login(email, password):
    # Authenticate user
    if not email or not password:
        return {
            "status": "error",
            "message": _("Email and password are required.")
        }

    try:
        # Attempt to log in using the email and password
        login_manager = frappe.local.login_manager
        login_manager.authenticate(email, password)

        # If authentication is successful, get user info
        user = frappe.get_doc("User", email)
        if user:
            if not user.api_key:
                return{
                    "status": "failed",
                    "message": "API access is not given to the user"
                }
            api_secret = frappe.utils.password.get_decrypted_password('User', user.name, 'api_secret')
            return {
                "status": "success",
                "message": _("Login successful"),
                "user": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "api_key": user.api_key,
                    "api_secret": api_secret
                }
            }
        else:
            return {
                "status": "failed",
                "message": "Invalid Credentials"
            }
    except frappe.AuthenticationError:
        return {
            "status": "error",
            "message": _("Invalid email or password.")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_maintenance():
    authorization_header = frappe.get_request_header("Authorization")
    if not authorization_header:
        return { "status": "error", "message": "Missing Authorization header"}
    api_key = frappe.get_request_header("Authorization").split(" ")[1].split(":")[0]
    # Find the user associated with the API key
    user = frappe.db.get_value("User", {"api_key": api_key}, "name")
    
    if not user:
        return {"status": "failed", "message": "Invalid API key"}
    
    maintenance_visits = frappe.get_all(
        "Maintenance Visit",
        fields="*"
    )
    
    # visits_with_details = []
    # for visit in maintenance_visits:
    #     visit_doc = frappe.get_doc("Maintenance Visit", visit.name)
        
    #     # Initialize a new dictionary for checktree_description
    #     checktree_description = {}
    #     for item in visit_doc.checktree_description:
    #         item_code = item.item_code
    #         if item_code not in checktree_description:
    #             checktree_description[item_code] = []
    #         checktree_description[item_code].append(item.as_dict())
        
    #     # Initialize a new dictionary for symptoms_table
    #     symptoms_table = {}
    #     for item in visit_doc.symptoms_table:
    #         item_code = item.item_code
    #         if item_code not in symptoms_table:
    #             symptoms_table[item_code] = []
    #         symptoms_table[item_code].append(item.as_dict())
        
    #     # Create a dictionary for the current visit, including the reformatted child tables
    #     visit_data = visit_doc.as_dict()
    #     visit_data['checktree_description'] = checktree_description
    #     visit_data['symptoms_table'] = symptoms_table
        
    #     # Append the reformatted data to the final output
    #     visits_with_details.append(visit_data)
    
    # return visits_with_details
    return maintenance_visits