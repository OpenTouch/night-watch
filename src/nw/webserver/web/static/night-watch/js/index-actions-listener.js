$( document ).ready(function() {
	// Register actions for buttons
	$('#btn-monitoring-on').click(function() {
		console.log("Enable monitoring");
		$.ajax({
			type: 'PUT',
			url: "/api/v1/night-watch/resume",
			success: function (data) {
				switchToggleBtn("#btn-monitoring", true);
				$('#reload-config-button').prop('disabled', false);
			},
			error: function(data) {
				// Display error popup
				BootstrapDialog.alert({
					title: 'Failed to resume Night-Watch',
					message: 'The following error occurred while trying to resume Night-Watch: <pre>' + (data.responseJSON.error_msg ? data.responseJSON.error_msg : data.responseText) + '</pre>',
					type: BootstrapDialog.TYPE_DANGER
				});
			}
	   }); 
	});
	
	$("#btn-monitoring-off").click(function () {
	   // Display a confirmation popup
		popup = BootstrapDialog.show({
			type: BootstrapDialog.TYPE_WARNING,
			title: 'Pause Night-Watch monitoring?',
			message: '<p>Night-Watch will <strong>stop monitoring</strong>.</p>\
	    				<p>Are you sure you want to proceed?</p>',
			buttons: [{
				label: 'Yes',
				cssClass: 'btn-warning',
				//hotkey: 13, // Enter
				autospin: true,
				action: function(dialogRef){
					dialogRef.enableButtons(false);
					dialogRef.setClosable(false);
					console.log("Disable monitoring");
					$.ajax({
						type: 'PUT',
						url: "/api/v1/night-watch/pause",
						success: function (data) {
							switchToggleBtn("#btn-monitoring", false);
							$('#reload-config-button').prop('disabled', true);
						},
						error: function(data) {
							// Display error popup
							BootstrapDialog.alert({
								title: 'Failed to pause Night-Watch',
								message: 'The following error occurred while trying to pause Night-Watch: <pre>' + (data.responseJSON.error_msg ? data.responseJSON.error_msg : data.responseText) + '</pre>',
								type: BootstrapDialog.TYPE_DANGER
							});
						},complete: function(data) {
							popup.close();
						}
				   }); 
				}
			}, {
				label: 'Cancel',
				action: function(dialogRef){
					dialogRef.close();
				}
			}]
		});
	});
	
	$("#reload-config-button").click(function () {
	   // Display a confirmation popup
		popup = BootstrapDialog.show({
			type: BootstrapDialog.TYPE_WARNING,
			title: 'Reload Night-Watch configuration files?',
			message: "<p>Night-Watch will reload all its configuration files and <strong>won't monitor anymore while it's reloading</strong> (for a few seconds).</p>\
	    				<p>Are you sure you want to proceed?</p>",
			buttons: [{
				label: 'Yes',
				cssClass: 'btn-warning',
				//hotkey: 13, // Enter
				autospin: true,
				action: function(dialogRef){
					$('#reload-config-button').prop('disabled', true).html('<span class="glyphicon glyphicon-refresh spinning"></span> Reloading Night-Watch...');
					dialogRef.enableButtons(false);
					dialogRef.setClosable(false);
					console.log("Disable monitoring");
					/*
					// TODO: call an API for reloading Night-Watch's config files
					// Display a spinner / progress bar
					*/
					$.ajax({
						type: 'PUT',
						url: "/api/v1/night-watch/reload",
						success: function (data) {
							console.log("Night-Watch successfully reloaded");
						},
						error: function(data) {
							// Display error popup
							BootstrapDialog.alert({
								title: 'Failed to reload Night-Watch',
								message: 'The following error occurred while reloading Night-Watch: <pre>' + (data.responseJSON.error_msg ? data.responseJSON.error_msg : data.responseText) + '</pre>',
								type: BootstrapDialog.TYPE_DANGER
							});
						},
						complete: function(data) {
							$('#reload-config-button').prop('disabled', false).html("Reload config files");
							popup.close();
						}
				   }); 
				}
			}, {
				label: 'Cancel',
				action: function(dialogRef){
					dialogRef.close();
				}
			}]
		});
	});
});