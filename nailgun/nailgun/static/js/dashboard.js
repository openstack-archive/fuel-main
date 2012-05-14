$.fn.renameable = function (object_type)
{
	this.click(function(){
		var label = $(this).text();
		$(this).text(prompt('Enter new name for ' + object_type + ' "' + label + '"', label))
	})
}

$(document).ready(function($){
	$('.node .label a').renameable('node');
	$('nav a.active').renameable('cluster') 

	$('#show-update-dialog').click(function() { $('#update-dialog').dialog({ modal: true, title : 'What\'s new in NailGun ver. 0.1.5', width: 600}) })
})
