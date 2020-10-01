$(document).ready(function(){
	
	/***************************** COMMENTS ************************************/
	// get the variables we need from page
	var initial_projected_countable_hours = $('#id_projected_countable_hours').val();
	var initial_total_hours_required = $('#id_total_hours_required').val();
	var form_id = $('#form_id').html();
	var form_type_name = $('#form_type_name').html();
	var action_url = '/apps/sisathl/sas/sp/comments/'
	var data_to_send = {
				'form_id': form_id,
				'form_type_name': form_type_name,
				};

	// function to fill a div with a rendered django template.
	function get_form(div_to_fill) {
		$.ajax({
			type: 'GET', 
			url: action_url,
			data: data_to_send,
			dataType: 'html',
			complete: function(data) {	
				// load the comments div with the comments view data
				div_to_fill.html(data.responseText);
			} 
		})
	}
		
	// load main comment form when page loads.
	get_form($('#comments'));

	// generic ajax function to process a form on an action
	// This can be called by any of the links, including the return form
	// The comment_id is the id of the comment to be saved, deleted, updated.
	// The action is an action code, corresponding to a constant in views/comments
	// Success is the function it should perform on a success.
	function process_form(link_clicked, success) {
		var comment_id = link_clicked.attr('id').substring(2);
		var action = link_clicked.attr('id').substring(0, 1);
		var comment = $('#text_' + comment_id).children('textarea').val()
		console.log(comment_id);
		console.log(comment);
		data_to_send['action'] = action;
		data_to_send['comment_id'] = comment_id;
		data_to_send['comment'] = comment;
        csrftoken =  $('input[name=csrfmiddlewaretoken]').val();
        data_to_send['csrfmiddlewaretoken'] = csrftoken;
		
		$.ajax({
			type: 'POST',
			url: action_url,
			data: data_to_send,
			dataType: 'html',
	        complete: function(data) {
	        	success(data);
			} 
		}) 
	}

	// on click on normal comment form, process the normal form
	$('#comments').on('click', 'a.comment_action', function(e){
		e.preventDefault();
		function success(data) {
			// load the comments div with the comments view data
			$('#comments').html(data.responseText);
		}
		process_form($(this), success);
	}); 

}); /* end document-ready */ 