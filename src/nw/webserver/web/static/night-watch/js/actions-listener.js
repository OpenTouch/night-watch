/*$('.btn-toggle').click(function() { // For generic actions on toggle
	console.log(".btn-toggle");
	$(this).find('.btn').toggleClass('active');
	$(this).find('.btn:not(.active)').removeClass('btn-danger btn-success').addClass('btn-default');

	if ($(this).find('.btn-on.active').size()>0) {
		$(this).find('.btn-on.active').toggleClass('btn-success');
		$(this).trigger('btn-on');
	}
	if ($(this).find('.btn-off.active').size()>0) {
		$(this).find('.btn-off.active').toggleClass('btn-danger');
		$(this).trigger('btn-off');
	}
});

$('#btn-monitoring').bind('btn-on', function(){
	console.log("Enable monitoring");
	$.ajax({
		type: 'PUT',
		url: "/api/v1/night-watch/resume",
		success: function (data) {
			$('#addContactPopup').modal('hide');
		},
		error: function(result) {
			// Display error popup
		} 
   }); 
});
$('#btn-monitoring').bind('btn-off', function(){
	console.log("Disable monitoring");
	$.ajax({
		type: 'PUT',
		url: "/api/v1/night-watch/pause",
		success: function (data) {
			$('#addContactPopup').modal('hide');
		},
		error: function(result) {
			// Display error popup
		} 
   }); 
});*/

$('#btn-monitoring-on').click(function() {
	console.log("Enable monitoring");
	$.ajax({
		type: 'PUT',
		url: "/api/v1/night-watch/resume",
		success: function (data) {
			$('#btn-monitoring-off').removeClass('btn-danger active').addClass('btn-default');
			$('#btn-monitoring-on').removeClass('btn-default').addClass('btn-success active');
		},
		error: function(result) {
			// Display error popup
		} 
   }); 
});

$("#confirm-diable-monitoring-button").click(function () {
	console.log("Disable monitoring");
	$('#disableMonitoringPopup').modal('hide');
	$.ajax({
		type: 'PUT',
		url: "/api/v1/night-watch/pause",
		success: function (data) {
			$('#btn-monitoring-on').removeClass('btn-success active').addClass('btn-default');
			$('#btn-monitoring-off').removeClass('btn-default').addClass('btn-danger active');
		},
		error: function(result) {
			// Display error popup
		} 
   }); 
});

$("#confirm-reload-config-button").click(function () {
	$('#reloadConfigPopup').modal('hide');
	/*
	// TODO: call an API for reloading Night-Watch's config files
	// Display a spinner / progress bar
	*/
	$.ajax({
		type: 'PUT',
		url: "/api/v1/night-watch/reload",
		success: function (data) {
			$('#addContactPopup').modal('hide');
		},
		error: function(result) {
			// Display error popup
		} 
   }); 
});