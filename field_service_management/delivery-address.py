
import frappe

# In your custom app's file, for example: field_service/doctype/your_doctype/your_doctype.py

# @frappe.whitelist()
# def get_customer_addresses(customer):
#     # Query the Address doctype and filter based on linked Customer
#     addresses = frappe.db.sql("""
#         SELECT parent 
#         FROM `tabDynamic Link`
#         WHERE parenttype = 'Address' 
#         AND link_doctype = 'Customer'
#         AND link_name = %s
#     """, (customer,), as_dict=True)

#     # Get the list of address names from the result
#     address_list = [address.get('parent') for address in addresses]

#     # Fetch full Address documents for each address
#     full_addresses = []
#     for address_name in address_list:
#         full_addresses.append(frappe.get_doc('Address', address_name))
#     return full_addresses  # Returns a list of full Address documents


@frappe.whitelist()
def get_delivery_notes(doctype, txt, searchfield, start, page_len, filters):
    customer = filters.get("customer")
    if customer:
        delivery_notes = frappe.db.get_all(
            "Delivery Note", 
            filters={"customer": customer}, 
            fields=["name", "shipping_address"],
            limit_start=start,
            limit_page_length=page_len
        )
        result = []

        # For each delivery note, fetch associated items from the child table
        for note in delivery_notes:
            items = frappe.db.get_all(
                "Delivery Note Item", 
                filters={"parent": note.name},  # Link between Delivery Note and Delivery Note Item
                fields=["item_code", "item_name"]
            )
            
            item_descriptions = ", ".join([f"{item['item_code']}: {item['item_name']}" for item in items])
            result.append((note.name, f"{note.shipping_address} | Items: {item_descriptions}"))
        return result
    


@frappe.whitelist()
def get_item_table(name):
    childs = frappe.db.get_all(
        "Item Maintenance Table",
        filters = {"parent": name},
        fields = ["heading", "content"]
    )
    return childs


@frappe.whitelist()
def get_symptoms_table(name):
    childs = frappe.db.get_all(
        "Symptom Resolution Table",
        filters = {"parent": name},
        fields = ["symptom_code", "resolution", "attach_image"]
    )
    return childs


@frappe.whitelist()
def get_spare_items(name):
    childs = frappe.db.get_all(
        "Spare Part",
        filters = {"parent": name},
        fields = ["item_code", "description", "rate", "rate_eur", "periodicity", "frequency_in_years", "uom"]
    )
    return childs

@frappe.whitelist()
def get_item(name):
    childs = frappe.get_doc('Item', name)
    print(childs)
    return childs



@frappe.whitelist()
def get_item_code_from_child_table(cdn):
    if frappe.has_permission('Maintenance Visit Purpose', 'read'):
        item_code = frappe.db.get_value('Maintenance Visit Purpose', cdn, 'item_code')
        return item_code
    else:
        frappe.throw(_("You do not have permission to access this resource."))


@frappe.whitelist()
def site_survey(name):
    childs = frappe.db.get_all(
        "Item Maintenance Table",
        filters = {"parent": name},
        fields = ["heading", "content"]
    )
    return childs


@frappe.whitelist()
def update_maintenance_visit(maintenance_visit, name):
    if not maintenance_visit:
        return
    try:
        frappe.db.sql("""
            UPDATE `tabMaintenance Visit`
            SET _assign = %s, maintenance_type = %s
            WHERE name = %s
        """, ('', 'Rescheduled', maintenance_visit))  # Empty _assign and set maintenance_type to Rescheduled
        
        # Commit the transaction to ensure changes are saved
        frappe.db.commit()

        print("Maintenance Visit updated successfully.")
    except Exception as e:
        print(f"Error updating Maintenance Visit: {e}")

    reschedule_doc = frappe.get_doc("Reschedule Requests", name)
    reschedule_doc.approval = 'Approved'
    reschedule_doc.approval_status = '1'
    reschedule_doc.save(ignore_permissions=True)

    return {"success": True}