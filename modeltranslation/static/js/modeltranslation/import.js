$(document).ready(function(){

	$("form.import").hide();

	$("a.import-link").click(function(){
		
		$(this).siblings("form").toggle();
	});

});
