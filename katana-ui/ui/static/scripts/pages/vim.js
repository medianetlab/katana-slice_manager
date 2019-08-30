$(document).ready(function(){
	var source   = $("#vim-table").html();
	var template = Handlebars.compile(source);

	$.ajax({
        type: 'GET',
        url: '/api/vim/all',
        timeout: 15000,

        error: function(err)
        {
            console.log(err);
        },
        dataType: 'json',
        success: function(data) {
            // console.log(data);
            var html    = template(data);
            $('.vim-table-tpl').html(html);

        }
    });
});