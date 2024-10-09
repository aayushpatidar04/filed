import frappe
from frappe import _
import json
from datetime import datetime
from datetime import timedelta


@frappe.whitelist()
def get_context():  
    context = {}
    issues = frappe.get_all('Issue', fields=['name', 'subject', 'status', 'creation', 'issue_type', '_assign', 'description'])
    for issue in issues:
        if issue._assign:
            try:
                assign_list = json.loads(issue._assign)  
                issue.assigned = json.loads(issue._assign)
                issue._assign = " | ".join(assign_list)  
            except json.JSONDecodeError:
                issue._assign = "No one assigned"
    context['issues'] = issues
    technicians = frappe.get_all('User',filters={'role_profile_name': 'Service Technician Role Profile'}, fields=['email', 'user_image', 'full_name'])
    date = datetime.now().date()
    time_slots = [
        {'label': '9:00 AM', 'time': timedelta(hours=9)},
        {'label': '10:00 AM', 'time': timedelta(hours=10)},
        {'label': '11:00 AM', 'time': timedelta(hours=11)},
        {'label': '12:00 PM', 'time': timedelta(hours=12)},
        {'label': '1:00 PM', 'time': timedelta(hours=13)},
        {'label': '2:00 PM', 'time': timedelta(hours=14)},
        {'label': '3:00 PM', 'time': timedelta(hours=15)},
        {'label': '4:00 PM', 'time': timedelta(hours=16)},
        {'label': '5:00 PM', 'time': timedelta(hours=17)},
        {'label': '6:00 PM', 'time': timedelta(hours=18)},
        {'label': '7:00 PM', 'time': timedelta(hours=19)},
        {'label': '8:00 PM', 'time': timedelta(hours=20)}
    ]
    for tech in technicians:
        html_content = ""
        tasks = frappe.get_all('Assigned Tasks', filters={'date': date, 'technician': tech.email}, fields=['issue_code', 'stime', 'etime', 'rescheduled'])
        for task in tasks:
            time_diff = task.etime - task.stime
            task.duration_in_hours = time_diff.total_seconds() / 3600
            task.flag = 0
        tech.tasks = tasks
        count = 0
        for slot in time_slots:
            task_in_slot = None
            for task in tasks:
                if task.stime <= slot['time'] and task.etime > slot['time']:
                    if task.flag == 0:  # Check if not already displayed
                        task_in_slot = task
                        task.flag = 1  # Mark as displayed
                        break
            if task_in_slot:
                html_content += f"""
                <div style="width: {task_in_slot['duration_in_hours'] * 100}px; background-color: green; border-right: 1px solid #000;" class="px-1 text-white text-center">
                    {task_in_slot['issue_code']}
                </div>
                """
                count += task_in_slot['duration_in_hours'] - 1
                print(count)
            else:
                print(count)
                if(count == 0):
                    html_content += '<div style="width: 100px; border-right: 1px solid #000;" class="px-1"></div>'
                else:
                    count -= 1
        tech.html_content = html_content
    context['technicians'] = technicians

    
    context['slots'] = time_slots
    context['message'] = "Welcome to your schedule board!"
    return context


def save_form_data(form_data):
    # Parse the form_data from the request
    print(form_data)
    try:
        technicians = form_data.get('technicians', [])
        code = form_data.get('code')
        date = form_data.get('date')
        etime = form_data.get('etime')
        stime = form_data.get('stime')

        for tech in technicians:
            new_doc = frappe.get_doc({
                "doctype": "Assigned Tasks",
                "issue_code": code,
                "technician": tech,
                "date": date,
                "etime": etime,
                "stime": stime
            })
            new_doc.insert()

        # Optionally, you can update the Issue doctype as well
        issue_doc = frappe.get_doc('Issue', code)
        if issue_doc:
            existing_techs = json.loads(issue_doc._assign) if issue_doc._assign else []
            for tech in technicians:
                if tech not in existing_techs:
                    existing_techs.append(tech)
            issue_doc._assign = json.dumps(existing_techs)
            issue_doc.save()

        return {"message": "success"}
    except Exception as e:
        return {"message": "error", "message": str(e)}