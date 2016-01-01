function customAlert(title, message, type) {
	$.notify({
		// options
		icon: "glyphicon glyphicon-warning-sign",
		title: title,
		message: message
	},{
		// settings
		element: "body",
		position: null,
		type: type,
		allow_dismiss: true,
		newest_on_top: false,
		showProgressbar: false,
		placement: {
			from: "top",
			align: "right"
		},
		offset: 20,
		spacing: 10,
		z_index: 1031,
		delay: 5000,
		timer: 1000,
		mouse_over: null,
		animate: {
			enter: "animated bounceInDown",
			exit: "animated fadeOutUp"
		}
	});
};