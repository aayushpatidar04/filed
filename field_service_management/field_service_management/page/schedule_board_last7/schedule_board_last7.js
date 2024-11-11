frappe.pages['schedule-board-last7'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Schedule Board: Last 7 Days',
		single_column: true
	});
}