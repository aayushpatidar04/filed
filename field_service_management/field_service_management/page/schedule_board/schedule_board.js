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

		setTimeout(function () {
			var drags = $('.drag');
			$('.drag').each(function () {
				$(this).on('dragstart', function (e) {
					e.originalEvent.dataTransfer.setData('text/plain', this.id); // Store the ID of the dragging card
					setTimeout(() => {
						$(this).css('opacity', '0.5'); // Visual feedback on drag start
					}, 0);
				});

				$(this).on('dragend', function () {
					$(this).css('opacity', '1'); // Reset opacity on drag end
				});
			});

			var dropZones = $('.drop-zone');

			$('.drop-zone').each(function () {
				$(this).on('dragover', function (e) {
					e.preventDefault(); // Prevent default to allow drop
					$(this).addClass('drop-hover'); // Add hover class
					$(this).css('background-color', 'green'); // Change background color to green
				});

				$(this).on('dragleave', function () {
					$(this).removeClass('drop-hover'); // Remove hover class
					$(this).css('background-color', 'cyan'); // Reset background color
				});

				$(this).on('drop', function (e) {
					e.preventDefault(); // Prevent default action
					const cardId = e.originalEvent.dataTransfer.getData('text/plain'); // Get the ID of the dragged card
					const slotTime = $(this).data('time');
					const tech = $(this).data('tech');
					const card = $('#' + cardId); // Select the card by ID
					$(this).removeClass('drop-hover'); // Remove hover class
					$(this).css('background-color', 'cyan'); // Reset background color

					// Open modal for the dropped card using its issue name
					openModal(cardId, slotTime, tech);
				});
			});

			function openModal(issueName, slot, tech) {
				const modalId = `formModal${issueName}`; // Construct the modal ID
				const modal = $(`#${modalId}`); // Select the modal using jQuery

				if (modal.length) { // Check if the modal exists
					const modalInstance = new bootstrap.Modal(modal[0]); // Pass the raw DOM element to bootstrap.Modal
					const currentDate = new Date();
					const year = currentDate.getFullYear();
					const month = String(currentDate.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
					const day = String(currentDate.getDate()).padStart(2, '0');
					modalInstance.show(); // Show the modal
					modal.find('.stime').val(slot.substring(0, 5));
					modal.find('.etime').data('stime', slot.substring(0, 5));
					modal.find('.technician').val(tech).change();
					const formattedDate = `${year}-${month}-${day}`;
					modal.find('.date').val(formattedDate).change();
				} else {
					console.error(`Modal with ID ${modalId} not found.`);
				}
			}
			$(document).on('click', '.close', function () {
				$(this).closest('.modal').modal('hide'); // Ensure the modal hides on close
			});

			var etime = $('.etime');
			etime.each(function () {
				$(this).on('change', function (e) {
					setTimeout(() => {
						const timeValue = $(this).val();
						const stime = $(this).data('stime');
						if (timeValue) {
							const [hours, minutes] = timeValue.split(':').map(Number);
							if (minutes % 30 !== 0) {
								alert('Please select a time that is a multiple of 30 minutes.');
								$(this).val(''); // Clear the input
								$(this).focus(); // Focus back on the input
							}else if(stime >= timeValue){
								alert('Please select a time that is greater than start time.');
								$(this).val(''); // Clear the input
								$(this).focus();
							}
						}
					}, 1000);  // Focus back on the input
				});
			});
		}, 1000);



	});


}


