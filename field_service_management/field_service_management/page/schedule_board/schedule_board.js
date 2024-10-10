frappe.pages['schedule-board'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Schedule Board',
		single_column: true
	});

	page.set_title("Schedule Board");
	frappe.call({
		method: "field_service_management.field_service_management.page.schedule_board.schedule_board.get_context",
		callback: function (r) {
			if (r.message) {
				$(frappe.render_template("schedule_board", r.message, r.issues)).appendTo(page.body);
			} else {
				console.log("No message returned from the server.");
			}
		}
	});
	$(document).ready(function () {
		
		$(document).on("click", ".submit", function () {
			const issueId = $(this).data("issue");
			const form = $("#custom-form-" + issueId);

			// Collect form data
			const formData = {
				code: form.find(".code").val(),
				technicians: form.find(".technician").val(),
				date: form.find(".date").val(),
				stime: form.find(".stime").val(),
				etime: form.find(".etime").val()
			};

			// Make an API call to Frappe to save the data in your Doctype
			frappe.call({
				method: "field_service_management.field_service_management.page.schedule_board.schedule_board.save_form_data",
				args: {
					form_data: formData
				},
				callback: function (response) {
					if (response.message.success) {
						alert("Issue assigned successfully!");
						window.location.reload();
					} else {
						alert(`Form submission failed!" ${response.message.message}`);
					}
				},
				error: function (error) {
					console.error(error);
					alert("An error occurred while submitting the form!");
				}
			});
		});


		$(document).on('shown.bs.modal', '.issue-modal', function () {
			const issueId = $(this).attr('id').replace('issueModal', '');
			console.log(issueId);
			const customerLat = 20.894800;  // Replace with customer's actual lat
			const customerLng = 105.925160;  // Replace with customer's actual lng
			frappe.call({
				method: "field_service_management.field_service_management.page.schedule_board.schedule_board.get_cords",
				callback: function (r) {
					if (r.message) {
						const technicians = r.message;
						const mapContainerId = 'map-' + issueId;
			
						// Check if the map container exists
						if ($('#' + mapContainerId).length) {
							const map = L.map(mapContainerId).setView([customerLat, customerLng], 13);
			
							// Add OpenStreetMap tiles
							L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
								maxZoom: 19
							}).addTo(map);
			
							// Add customer marker
							L.marker([customerLat, customerLng]).addTo(map)
								.bindPopup('<b>Customer Location</b>').openPopup();
			
							const greenIcon = L.icon({
								iconUrl: '/private/files/green-marker51773a.png', // Replace with a link to a green icon image
								iconSize: [25, 41], // Size of the icon
								iconAnchor: [12, 41], // Point of the icon which will correspond to marker's location
								popupAnchor: [1, -34], // Point from which the popup should open relative to the iconAnchor
							});

							// Add technician markers (assuming technicians is an available variable)
							technicians.forEach(function (tech) {
								L.marker([tech.latitude, tech.longitude], { icon: greenIcon }).addTo(map)
									.bindPopup('<b>Technician: ' + tech.technician + '</b>');
							});
						} else {
							console.error('Map container not found:', mapContainerId);
						}
					} else {
						console.log("No cords returned from the server.");
					}
				}
			});
		});

	});







}


