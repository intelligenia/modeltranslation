$(document).ready(function(){
	
	$("<a id='copy_source' class='copy_source' href='javascript:void(0);'>Copiar texto original</a>")
		.prependTo($(".controls:first"))
		.click(function(e){
			var source_text = $.trim($("#source_text").html());
			// Si no hay editor TinyMCE editor
			if($("#id_translation_parent").length==0){
				$("#id_translation").html(source_text);
			}
			// Si lo hay usamos su API
			else{
				tinymce.activeEditor.setContent(source_text, {format: 'raw'});
			}
			return false;
		});
	
});
