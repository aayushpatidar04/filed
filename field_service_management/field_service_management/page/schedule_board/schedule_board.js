frappe.pages['schedule-board'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Schedule Board',
		single_column: true
	});

	page.set_title("Schedule Board");
	frappe.call({
		method: "field_service_management.field_service_management.page.schedule_board.schedule_board.get_context",
		callback: function(r) {
			if (r.message) {
				$(frappe.render_template("schedule_board", r.message, r.issues)).appendTo(page.body);
			} else {
				console.log("No message returned from the server.");
			}
		}
	});

	// document.getElementById("submit").addEventListener("click", function (event) {
	// 	const formData = {
	// 		code: document.getElementById("code").value,
	// 		technicians: Array.from(document.getElementById("technician").selectedOptions).map(option => option.value),
	// 		date: document.getElementById("date").value,
	// 		etime: document.getElementById("etime").value,
	// 		stime: document.getElementById("stime").value
	// 	};
	// 	console.log(formData);

	// 	// Make an API call to Frappe to save the data in your Doctype
	// 	frappe.call({
	// 		method: "field_service_management.field_service_management.page.schedule_board.schedule_board.save_form_data",
	// 		args: {
	// 			form_data: formData
	// 		},
	// 		callback: function (response) {
	// 			if (response.message) {
	// 				alert("Issue assigned successfully!");
	// 			} else {
	// 				alert("Form submission failed!");
	// 			}
	// 		},
	// 		error: function (error) {
	// 			console.error(error);
	// 			alert("An error occurred while submitting the form!");
	// 		}
	// 	});
	// });
	
	
	
}


	