$(document).ready(function(){

/*
	$("input.import_submit").each(function(){
		$(this).hide();
		var $form = $(this).parent().parent();
		$('<a title="Importar traducción desde un fichero .po" href="javascript:void(0);" class="import-link btn btn-mini"><i class="icon-download-alt"></i> Importar traducción</a>')
			.insertAfter($form)
			.click(function(){
				$form.submit();
			});
		
	});
*/

	$("form.import").hide();
	
	$("a.import-link").click(function(){
		
		$(this).siblings("form").toggle();
	});

});
