import frappe
from frappe import _
import json
from datetime import datetime
from datetime import timedelta


@frappe.whitelist()
def get_context(context=None):
    context = context or {}
    user = frappe.session.user

        
    if user == "Administrator":
        issues = frappe.get_all(
            "Maintenance Visit",
            filters={"_assign": ""},
            fields=[
                "name",
                "subject",
                "status",
                "creation",
                "maintenance_type",
                "_assign",
                "description",
                "maintenance_description",
                "customer_address"
            ],
        )
        technicians = frappe.get_all(
            "User",
            filters={"role_profile_name": "Service Technician Role Profile"},
            fields=["email", "user_image", "full_name"],
        )
    role_profile = frappe.db.get_value("User", user, "role_profile_name")
    if role_profile == "Service Coordinator Profile":
        # Fetch the user's territory from User Permissions
        
        territory = frappe.db.get_value(
            "User Permission", {"user": user, "allow": "Territory"}, "for_value"
        )
        # Fetch issues based on the user's territory
        issues = frappe.get_all(
            "Maintenance Visit",
            filters={"territory": territory, "_assign": ""},
            fields=[
                "name",
                "subject",
                "status",
                "creation",
                "maintenance_type",
                "_assign",
                "description",
                "maintenance_description",
                "customer_address"
            ],
        )
        technicians = frappe.get_all(
            "User",
            filters={"role_profile_name": "Service Technician Role Profile"},
            fields=["email", "user_image", "full_name"],
        )
        # Filter technicians based on their territory in User Permission
        technician_list = []
        for tech in technicians:
            tech_territory = frappe.db.get_value(
                "User Permission", {"user": tech["email"], "allow": "Territory"}, "for_value"
            )
            if tech_territory == territory:
                technician_list.append(tech)
        technicians = technician_list
    for issue in issues:
        if issue._assign:
            try:
                assign_list = json.loads(issue._assign)
                issue.assigned = json.loads(issue._assign)
                issue._assign = " | ".join(assign_list)
            except json.JSONDecodeError:
                issue._assign = "No one assigned"

        #geolocation --------------------------------------------------
        geolocation = frappe.get_all('Address', filters = {'name' : issue.customer_address}, fields = ['geolocation'])
        geolocation = json.loads(geolocation[0].geolocation)
        
        issue.geolocation = json.dumps(geolocation['features']).replace('"', "'")
        # issue.geolocation = geolocation
        # checklist tree ----------------------------------------------
        checklist = frappe.get_all(
            "Maintenance Visit Checklist",
            filters = {"parent": issue.name},
            fields = ['item_code', 'item_name', 'heading', 'work_done', 'done_by']
        )
        checklist_tree = {}
        html_content = ""
        for problem in checklist:
            key = problem.item_code
            if key not in checklist_tree:
                checklist_tree[key] = []
            checklist_tree[key].append(problem)

        for item_code, products in checklist_tree.items():
            if products:
                html_content += f"<p><strong>{item_code}: {products[0].item_name}</strong></p>"
                for product in products:
                    checked_attribute = "checked" if product.work_done == "Yes" else ""
                    html_content += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type='checkbox' {checked_attribute} disabled> &nbsp;&nbsp;&nbsp;&nbsp;{product.heading}<br>"
                html_content += "</p>"
        issue.checklist_tree = html_content


        # Products -------------------------------------------------------------
        products = frappe.get_all(
            "Maintenance Visit Purpose",
            filters = {"parent": issue.name},
            fields = ['item_code', 'item_name', 'custom_image']
        )
        issue.products = products

        # Spare Items -------------------------------------------------------------
        spare_items = frappe.get_all(
            "Spare Part",
            filters = {"parent": issue.name},
            fields = ['item_code', 'description', 'periodicity', 'uom']
        )
        issue.spare_items = spare_items

        #symptoms and resolutions ------------------------------------------------------
        symptoms = frappe.get_all(
            "Maintenance Visit Symptoms",
            filters = {"parent": issue.name},
            fields = ['item_code', 'symptom_code', 'resolution', 'image']
        )
        symptoms_res = {}
        html_content = ""
        for symptom in symptoms:
            key = symptom.item_code
            if key not in symptoms_res:
                symptoms_res[key] = []
            symptoms_res[key].append(symptom)

        for item_code, resolutions in symptoms_res.items():
            if resolutions:
                html_content += f"<p><strong>{item_code}:</strong></p>"
                for resolution in resolutions:
                    html_content += f"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src='{resolution.image}' style='max-width: 100px;'> --> <strong>{resolution.symptom_code}</strong> --> {resolution.resolution}<br>"
                html_content += "</p>"
        issue.symptoms_res = html_content


    context["issues"] = issues
        

    # Get today's date
    current_date = datetime.now().date()

    # Generate the last 7 days including today
    dates = [(current_date - timedelta(days=i)) for i in range(7)]

    # Define your time slots for each day
    time_slots = [
        {"label": "09", "time": timedelta(hours=9)},
        {"label": "10", "time": timedelta(hours=10)},
        {"label": "11", "time": timedelta(hours=11)},
        {"label": "12", "time": timedelta(hours=12)},
        {"label": "01", "time": timedelta(hours=13)},
        {"label": "02", "time": timedelta(hours=14)},
        {"label": "03", "time": timedelta(hours=15)},
        {"label": "04", "time": timedelta(hours=16)},
        {"label": "05", "time": timedelta(hours=17)},
        {"label": "06", "time": timedelta(hours=18)},
        {"label": "07", "time": timedelta(hours=19)},
        {"label": "08", "time": timedelta(hours=20)},
    ]

    # Loop through each technician
    for tech in technicians:
        html_content = ""

        # Fetch tasks for the past 7 days for each technician
        all_tasks = frappe.get_all(
            "Assigned Tasks",
            filters={"technician": tech.email, "date": ["in", dates]},
            fields=["issue_code", "date", "stime", "etime", "rescheduled"],
            order_by="date, stime"
        )

        # Organize tasks by date
        tasks_by_date = {date: [] for date in dates}
        for task in all_tasks:
            time_diff = task.etime - task.stime
            task.duration_in_hours = time_diff.total_seconds() / 3600
            task.flag = 0
            tasks_by_date[task.date].append(task)

        # Loop through each day for the past week
        for date in dates:
            # html_content += f'<div class="day-header">{date.strftime("%A, %d %b %Y")}</div>'
            tasks = tasks_by_date[date]
            count = 0
            
            # Loop through each time slot for the day
            for slot in time_slots:
                not_available = []
                
                # Check availability for the current time slot
                ts = frappe.get_all(
                    "Assigned Tasks",
                    filters={"date": date},
                    fields=["issue_code", "stime", "etime", "rescheduled", "technician"],
                )
                for t in ts:
                    if t.stime <= slot["time"] and t.etime > slot["time"]:
                        not_available.append(t.technician)
                slot['not_available'] = not_available

                task_in_slot = None
                for task in tasks:
                    maintenance = frappe.get_doc('Maintenance Visit', task.issue_code)
                    if task.stime <= slot["time"] and task.etime > slot["time"]:
                        if task.flag == 0:  # Check if not already displayed
                            task_in_slot = task
                            task.flag = 1  # Mark as displayed
                            break
                
                # Generate HTML for the task if found
                if task_in_slot:
                    html_content += f"""
                    <div style="width: {task_in_slot['duration_in_hours'] * 25}px; background-color: red; border-right: 1px solid #000;" class="px-1 py-2 text-white text-center drag" data-type="type2" draggable="true" id="task-{task_in_slot['issue_code']}" data-duration="{task_in_slot['duration_in_hours']}">
                        <a href="javascript:void(0)"
                            class="text-white" data-toggle="modal"
                            data-target="#taskModaltask-{task_in_slot['issue_code']}">{task_in_slot['issue_code']}</a>
                    </div>
                    """
                    count += task_in_slot["duration_in_hours"] - 1
                else:
                    # Display an empty drop zone if no task is found
                    if count == 0:
                        html_content += f'<div style="width: 25px; border-right: 1px solid #000; background-color: cyan;" data-time="{slot["time"]}" data-tech="{tech.email}" data-na="{slot["not_available"]}" class="px-1 drop-zone">-</div>'
                    elif count % 1 == 0.5:
                        slot['time'] += timedelta(minutes=30)
                        html_content += f'<div style="width: 12.5px; border-right: 1px solid #000; background-color: cyan;" data-time="{slot["time"]}" data-tech="{tech.email}" data-na="{slot["not_available"]}" class="px-1 drop-zone">-</div>'
                        count -= 0.5
                    else:
                        count -= 1

            tech.html_content = html_content

    context["dates"] = dates
    context["technicians"] = technicians    
    context["slots"] = time_slots
    context["message"] = "Welcome to your schedule board!"
    return context


@frappe.whitelist()
def save_form_data(form_data):
    # Parse the form_data from the request
    try:
        form_data = json.loads(form_data)
        technicians = form_data["technicians"]
        code = form_data["code"]
        date = form_data["date"]
        etime = form_data["etime"]
        stime = form_data["stime"]
        hours, minutes = map(int, etime.split(":"))
        etime = timedelta(hours=hours, minutes=minutes)
        hours, minutes = map(int, stime.split(":"))
        stime = timedelta(hours=hours, minutes=minutes)
        for tech in technicians:
            assigned_tasks = frappe.get_all(
                "Assigned Tasks",
                filters={"technician": tech, "date": date},
                fields=["issue_code", "stime", "etime"],
            )
            for task in assigned_tasks:
                if (
                    (stime > task.stime and stime < task.etime)
                    or (etime > task.stime and etime < task.etime)
                    or (task.stime > stime and task.stime < etime)
                ):
                    return {
                        "error": "error",
                        "message": f"Time Slot Clash for technician: {tech}",
                    }

        for tech in technicians:

            new_doc = frappe.get_doc(
                {
                    "doctype": "Assigned Tasks",
                    "issue_code": code,
                    "technician": tech,
                    "date": date,
                    "etime": etime,
                    "stime": stime,
                }
            )
            new_doc.insert()

        # Optionally, you can update the Issue doctype as well
        issue_doc = frappe.get_doc("Maintenance Visit", code)
        if issue_doc:
            existing_techs = json.loads(issue_doc._assign) if issue_doc._assign else []
            for tech in technicians:
                if tech not in existing_techs:
                    existing_techs.append(tech)
            issue_doc._assign = json.dumps(existing_techs)
            frappe.db.sql(
                """
                UPDATE `tabMaintenance Visit` SET `_assign` = %s WHERE name = %s
            """,
                (json.dumps(existing_techs), code),
            )

            frappe.db.commit()
        return {"success": "success"}
    except Exception as e:
        return {"error": "error", "message": str(e)}


@frappe.whitelist()
def get_cords():
    query = """
    SELECT technician, latitude, longitude, time 
    FROM `tabLive Location` 
    WHERE (technician, time) IN (
        SELECT technician, MAX(time) 
        FROM `tabLive Location` 
        GROUP BY technician
    )
    """
    technicians = frappe.db.sql(query, as_dict=True)
    
    return technicians



@frappe.whitelist()
def update_form_data(form_data):
    # # Parse the form_data from the request
    # pass
    try:
        form_data = json.loads(form_data)
        technicians = form_data["technicians"]
        code = form_data["code"]
        date = form_data["date"]
        etime = form_data["etime"]
        stime = form_data["stime"]
        if(len(etime) > 5):
            hours, minutes, seconds = map(int, etime.split(":"))
        else:
            hours, minutes = map(int, etime.split(":"))
        etime = timedelta(hours=hours, minutes=minutes)
        if(len(stime) > 5):
            hours, minutes, seconds = map(int, stime.split(":"))
        else:
            hours, minutes = map(int, stime.split(":"))

        stime = timedelta(hours=hours, minutes=minutes)


        tasks = frappe.get_all("Assigned Tasks", filters={"issue_code": code}, fields=["name"])

        if tasks:
            for task in tasks:
                frappe.delete_doc("Assigned Tasks", task.name, force=True)
            frappe.db.commit()



        for tech in technicians:
            assigned_tasks = frappe.get_all(
                "Assigned Tasks",
                filters={"technician": tech, "date": date},
                fields=["issue_code", "stime", "etime"],
            )
            for task in assigned_tasks:
                if (
                    (stime > task.stime and stime < task.etime)
                    or (etime > task.stime and etime < task.etime)
                    or (task.stime > stime and task.stime < etime)
                ):
                    return {
                        "error": "error",
                        "message": f"Time Slot Clash for technician: {tech}",
                    }

        for tech in technicians:

            new_doc = frappe.get_doc(
                {
                    "doctype": "Assigned Tasks",
                    "issue_code": code,
                    "technician": tech,
                    "date": date,
                    "etime": etime,
                    "stime": stime,
                }
            )
            new_doc.insert()

        # Optionally, you can update the Issue doctype as well
        issue_doc = frappe.get_doc("Maintenance Visit", code)
        if issue_doc:
            existing_techs = json.loads(issue_doc._assign) if issue_doc._assign else []
            for tech in technicians:
                if tech not in existing_techs:
                    existing_techs.append(tech)
            issue_doc._assign = json.dumps(existing_techs)
            frappe.db.sql(
                """
                UPDATE `tabMaintenance Visit` SET `_assign` = %s WHERE name = %s
            """,
                (json.dumps(existing_techs), code),
            )

            frappe.db.commit()
        return {"success": "success"}
    except Exception as e:
        return {"error": "error", "message": str(e)}