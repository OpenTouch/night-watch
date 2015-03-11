function switchToggleBtn(btn_toggle_id, enabled) {
	var btn_on = $(btn_toggle_id).find('.btn-on');
	var btn_off = $(btn_toggle_id).find('.btn-off');
	if (enabled) {
		btn_on.removeClass('btn-default').addClass('btn-success active').prop('disabled', true);
		btn_off.removeClass('btn-danger active').addClass('btn-default').prop('disabled', false);
	}
	else {
		btn_on.removeClass('btn-success active').addClass('btn-default').prop('disabled', false);
		btn_off.removeClass('btn-default').addClass('btn-danger active').prop('disabled', true);
	}
}